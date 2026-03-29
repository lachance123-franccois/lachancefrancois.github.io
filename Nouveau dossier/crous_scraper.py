"""
CROUS Housing Scraper - Toulouse Focus
Scrapes housing offers from CROUS with intelligent caching and filtering
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import hashlib
import logging
from dataclasses import dataclass, asdict
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class HousingOffer:
    """Data model for housing offers"""
    id: str
    title: str
    location: str
    price: float
    type: str
    surface: Optional[str]
    available_date: Optional[str]
    url: str
    description: str
    distance_to_uni: Optional[str]
    posted_date: str
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def hash_id(self) -> str:
        """Generate unique hash for the offer"""
        content = f"{self.title}{self.location}{self.price}{self.available_date}"
        return hashlib.md5(content.encode()).hexdigest()


class CROUSScraper:
    """
    Advanced CROUS housing scraper with rate limiting and error handling
    """
    
    BASE_URL = "https://trouverunlogement.lescrous.fr"
    SEARCH_URL = f"{BASE_URL}/tools/32/search"
    
    TOULOUSE_AREAS = [
        "Toulouse Centre",
        "Rangueil", 
        "Lardenne",
        "Ponsan",
        "Empalot"
        "souazelong"
    ]
    
    def __init__(self, cache_hours: int = 1):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/html',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8'
        })
        self.cache_duration = timedelta(hours=cache_hours)
        
    def search_toulouse_housing(self, max_price: float = 600) -> List[HousingOffer]:
        """
        Search for housing in Toulouse area
        
        Args:
            max_price: Maximum monthly rent in euros
            
        Returns:
            List of HousingOffer objects
        """
        logger.info(f"🏠 Searching CROUS housing in Toulouse (max {max_price}€)")
        
        offers = []
        
        try:
            # Build search parameters for Toulouse
            params = {
                'address': 'Toulouse',
                'maxPrice': max_price,
                'precision': 8  # 10km radius
            }
            
            response = self.session.get(self.SEARCH_URL, params=params, timeout=15)
            response.raise_for_status()
            
            # Try to parse JSON response
            try:
                data = response.json()
                offers = self._parse_json_response(data)
            except json.JSONDecodeError:
                # Fallback to HTML parsing
                offers = self._parse_html_response(response.text)
            
            logger.info(f"✅ Found {len(offers)} housing offers")
            
        except requests.RequestException as e:
            logger.error(f"❌ Error fetching CROUS data: {e}")
        
        return self._filter_toulouse_offers(offers)
    
    def _parse_json_response(self, data: dict) -> List[HousingOffer]:
        """Parse JSON API response"""
        offers = []
        
        residences = data.get('data', {}).get('residences', [])
        
        for residence in residences:
            try:
                offer = HousingOffer(
                    id=str(residence.get('id', '')),
                    title=residence.get('name', 'Sans titre'),
                    location=f"{residence.get('address', '')}, {residence.get('city', '')}",
                    price=float(residence.get('price', 0)),
                    type=residence.get('type', 'Studio'),
                    surface=f"{residence.get('surface', 'N/A')}m²",
                    available_date=residence.get('availableDate'),
                    url=f"{self.BASE_URL}/residence/{residence.get('id')}",
                    description=residence.get('description', ''),
                    distance_to_uni=self._calculate_distance(residence),
                    posted_date=datetime.now().isoformat()
                )
                offers.append(offer)
            except Exception as e:
                logger.warning(f"Error parsing offer: {e}")
                continue
        
        return offers
    
    def _parse_html_response(self, html: str) -> List[HousingOffer]:
        """Fallback HTML parsing"""
        soup = BeautifulSoup(html, 'html.parser')
        offers = []
        
        # Find housing cards/listings
        listings = soup.find_all(['div', 'article'], class_=re.compile(r'residence|logement|housing'))
        
        for listing in listings:
            try:
                offer = self._extract_offer_from_html(listing)
                if offer:
                    offers.append(offer)
            except Exception as e:
                logger.warning(f"Error parsing HTML listing: {e}")
                continue
        
        return offers
    
    def _extract_offer_from_html(self, element) -> Optional[HousingOffer]:
        """Extract offer details from HTML element"""
        # This is a template - adjust selectors based on actual HTML structure
        title = element.find(['h2', 'h3'])
        price_elem = element.find(text=re.compile(r'\d+\s*€'))
        
        if not title:
            return None
        
        # Extract price
        price = 0.0
        if price_elem:
            price_match = re.search(r'(\d+)', price_elem)
            if price_match:
                price = float(price_match.group(1))
        
        return HousingOffer(
            id=hashlib.md5(title.text.encode()).hexdigest()[:8],
            title=title.text.strip(),
            location="Toulouse",
            price=price,
            type="Studio",
            surface=None,
            available_date=None,
            url=self.BASE_URL,
            description=element.get_text(strip=True)[:200],
            distance_to_uni=None,
            posted_date=datetime.now().isoformat()
        )
    
    def _filter_toulouse_offers(self, offers: List[HousingOffer]) -> List[HousingOffer]:
        """Filter offers to Toulouse area only"""
        filtered = []
        
        for offer in offers:
            location_lower = offer.location.lower()
            if any(area.lower() in location_lower for area in self.TOULOUSE_AREAS):
                filtered.append(offer)
            elif 'toulouse' in location_lower:
                filtered.append(offer)
        
        return filtered
    
    def _calculate_distance(self, residence: dict) -> Optional[str]:
        """Calculate approximate distance to main university campus"""
        # This would require geocoding - placeholder for now
        return None
    
    def get_new_offers(self, previous_offers: List[str]) -> List[HousingOffer]:
        """
        Get only new offers not in previous list
        
        Args:
            previous_offers: List of offer IDs already seen
            
        Returns:
            List of new offers
        """
        all_offers = self.search_toulouse_housing()
        new_offers = [
            offer for offer in all_offers 
            if offer.hash_id() not in previous_offers
        ]
        
        logger.info(f"🆕 {len(new_offers)} new housing offers")
        return new_offers


# Exemple d'utilisation
if __name__ == "__main__":
    scraper = CROUSScraper()
    offers = scraper.search_toulouse_housing(max_price=500)
    
    for offer in offers[:3]:
        print(f"\n📍 {offer.title}")
        print(f"   💰 {offer.price}€/mois")
        print(f"   📍 {offer.location}")
        print(f"   🔗 {offer.url}")
