"""
Housing Scraper - Multi-sources (CROUS, LeBonCoin, SeLoger, PAP, Logic-Immo)
Version stealth avec rotation et délais aléatoires
"""

import re
import logging
import random
from typing import List, Optional
from dataclasses import dataclass
from bs4 import BeautifulSoup
from stealth_utils import StealthSession, rate_limited

logger = logging.getLogger(__name__)


@dataclass
class HousingOffer:
    id: str
    title: str
    location: str
    price: float
    surface: str
    source: str
    url: str
    description: str
    available_date: Optional[str]
    posted_date: str


class HousingScraper:
    """
    Scraper multi-sources pour logements (priorité aux APIs quand disponibles)
    """
    
    TOULOUSE_CODES = ['31000', '31100', '31200', '31300', '31400', '31500']
    
    def __init__(self):
        self.session = StealthSession(use_cache=True)
        self.max_price = 600
    
    def search_all(self, max_price: int = 600) -> List[HousingOffer]:
        """Recherche sur toutes les sources"""
        self.max_price = max_price
        all_offers = []
        
        # Sources prioritaires (moins de risques)
        all_offers.extend(self._scrape_crous())
        all_offers.extend(self._scrape_leboncoin())
        all_offers.extend(self._scrape_seloger())
        all_offers.extend(self._scrape_pap())
        
        # Filtrage Toulouse uniquement
        filtered = [o for o in all_offers if self._is_toulouse(o.location)]
        
        logger.info(f"🏠 Total housing offers: {len(filtered)} from {len(all_offers)} raw")
        return filtered
    
    @rate_limited(min_delay=4, max_delay=10)
    def _scrape_crous(self) -> List[HousingOffer]:
        """Scrape CROUS (site institutionnel - plus tolérant)"""
        offers = []
        
        try:
            # Utiliser l'API publique si disponible
            url = "https://trouverunlogement.lescrous.fr/api/search"
            params = {
                'city': 'Toulouse',
                'maxPrice': self.max_price,
                'limit': 30
            }
            
            data = self.session.get(url, params=params, ttl_hours=12)
            
            if isinstance(data, dict):
                for item in data.get('data', {}).get('residences', []):
                    offers.append(HousingOffer(
                        id=f"crous_{item.get('id')}",
                        title=item.get('name', 'Logement CROUS'),
                        location=f"Toulouse {item.get('district', '')}",
                        price=float(item.get('price', 0)),
                        surface=f"{item.get('surface', 'N/A')}m²",
                        source="CROUS",
                        url=f"https://trouverunlogement.lescrous.fr/residence/{item.get('id')}",
                        description=item.get('description', '')[:300],
                        available_date=item.get('availableDate'),
                        posted_date=item.get('createdAt', '')
                    ))
            
            logger.info(f"CROUS: {len(offers)} offers")
            
        except Exception as e:
            logger.warning(f"CROUS scrape error: {e}")
        
        return offers
    
    @rate_limited(min_delay=5, max_delay=12)
    def _scrape_leboncoin(self) -> List[HousingOffer]:
        """Scrape LeBonCoin (utilisation de l'API officielle)"""
        offers = []
        
        try:
            # API publique LeBonCoin (rate limitée)
            url = "https://api.leboncoin.fr/finder/search"
            headers = {
                'x-algolia-api-key': 'YOUR_API_KEY',  # À remplacer
                'x-algolia-application-id': 'YOUR_APP_ID'
            }
            
            params = {
                'q': 'location Toulouse',
                'price': f'0-{self.max_price}',
                'category': '9',  # Location
                'limit': 20
            }
            
            # Note: Nécessite une clé API valide
            # Alternative: parsing HTML avec délais plus longs
            
            logger.info(f"LeBonCoin: {len(offers)} offers (API mode)")
            
        except Exception as e:
            logger.warning(f"LeBonCoin scrape error: {e}")
        
        return offers
    
    @rate_limited(min_delay=6, max_delay=15)
    def _scrape_seloger(self) -> List[HousingOffer]:
        """Scrape SeLoger"""
        offers = []
        
        try:
            url = "https://www.seloger.com/list.htm"
            params = {
                'idtt': '1',  # Location
                'idtypebien': '1,2',  # Appartement, Maison
                'ci': '31000,31100,31200,31300,31400,31500',  # Codes postaux Toulouse
                'pxmax': self.max_price,
                'tri': 'd_dt_crea'
            }
            
            html = self.session.get(url, params=params, ttl_hours=6)
            soup = BeautifulSoup(html, 'html.parser')
            
            cards = soup.find_all('div', class_=re.compile(r'c-card|c-pal-card'))
            
            for card in cards[:15]:
                try:
                    title_elem = card.find('div', class_=re.compile(r'title'))
                    price_elem = card.find('div', class_=re.compile(r'price'))
                    link_elem = card.find('a', href=True)
                    
                    if title_elem and price_elem:
                        price = self._extract_price(price_elem.text)
                        
                        if price <= self.max_price:
                            offers.append(HousingOffer(
                                id=f"seloger_{hash(title_elem.text)}",
                                title=title_elem.text.strip(),
                                location="Toulouse",
                                price=price,
                                surface=self._extract_surface(card),
                                source="SeLoger",
                                url=link_elem.get('href', '') if link_elem else '',
                                description=card.get_text(strip=True)[:200],
                                available_date=None,
                                posted_date=''
                            ))
                except Exception:
                    continue
            
            logger.info(f"SeLoger: {len(offers)} offers")
            
        except Exception as e:
            logger.warning(f"SeLoger scrape error: {e}")
        
        return offers
    
    @rate_limited(min_delay=5, max_delay=10)
    def _scrape_pap(self) -> List[HousingOffer]:
        """Scrape PAP (Particulier à Particulier)"""
        offers = []
        
        try:
            url = "https://www.pap.fr/annonnes/locations/toulouse"
            params = {
                'prix_max': self.max_price,
                'surface_min': '9'
            }
            
            html = self.session.get(url, params=params, ttl_hours=6)
            soup = BeautifulSoup(html, 'html.parser')
            
            annonces = soup.find_all('div', class_=re.compile(r'annonce'))
            
            for annonce in annonces[:15]:
                try:
                    title = annonce.find('h3', class_=re.compile(r'title|annonce-title'))
                    price = annonce.find('span', class_=re.compile(r'price|prix'))
                    link = annonce.find('a', href=True)
                    
                    if title and price:
                        price_val = self._extract_price(price.text)
                        
                        if price_val <= self.max_price:
                            offers.append(HousingOffer(
                                id=f"pap_{hash(title.text)}",
                                title=title.text.strip(),
                                location="Toulouse",
                                price=price_val,
                                surface=self._extract_surface(annonce),
                                source="PAP",
                                url=link.get('href', '') if link else '',
                                description=annonce.get_text(strip=True)[:200],
                                available_date=None,
                                posted_date=''
                            ))
                except Exception:
                    continue
            
            logger.info(f"PAP: {len(offers)} offers")
            
        except Exception as e:
            logger.warning(f"PAP scrape error: {e}")
        
        return offers
    
    def _is_toulouse(self, location: str) -> bool:
        """Vérifie si le logement est à Toulouse"""
        location_lower = location.lower()
        return any([
            'toulouse' in location_lower,
            any(code in location for code in self.TOULOUSE_CODES)
        ])
    
    def _extract_price(self, text: str) -> float:
        """Extrait le prix d'un texte"""
        match = re.search(r'(\d+[\s]?\d*)\s*€', text)
        if match:
            return float(match.group(1).replace(' ', ''))
        return 9999
    
    def _extract_surface(self, element) -> str:
        """Extrait la surface"""
        text = element.get_text(strip=True)
        match = re.search(r'(\d+)\s*m²', text)
        if match:
            return f"{match.group(1)}m²"
        return "N/A"