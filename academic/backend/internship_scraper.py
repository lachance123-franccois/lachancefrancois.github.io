"""
Internship Scraper - Version corrigée avec URLs fonctionnelles
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Optional
import hashlib
import logging
import time
import random
from dataclasses import dataclass, asdict
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class InternshipOffer:
    id: str
    title: str
    company: str
    location: str
    domain: str
    keywords: List[str]
    duration: str
    level: str
    start_date: Optional[str]
    deadline: Optional[str]
    url: str
    description: str
    compensation: Optional[str]
    posted_date: str
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def hash_id(self) -> str:
        return hashlib.md5(f"{self.title}{self.company}".encode()).hexdigest()


class InternshipScraper:
    
    KEYWORDS = [
        'image', 'video', 'computer vision', 'vision par ordinateur',
        'signal', 'traitement du signal', 'deep learning', 'machine learning',
        '5G', '6G', 'telecom', 'IA', 'AI', 'python', 'pytorch', 'tensorflow'
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
        })
    
    def scrape_all_sources(self) -> List[InternshipOffer]:
        """Scrape all configured sources"""
        all_offers = []
        
        all_offers.extend(self._scrape_abg())
        time.sleep(random.uniform(3, 8))
        
        all_offers.extend(self._scrape_welcometothejungle())
        time.sleep(random.uniform(3, 8))
        
        all_offers.extend(self._scrape_hellowork())
        
        filtered = self._filter_relevant_offers(all_offers)
        unique = self._deduplicate_offers(filtered)
        
        logger.info(f"💼 Total internship offers: {len(unique)}")
        return unique
    
    def _scrape_abg(self) -> List[InternshipOffer]:
        """Scrape ABG internships"""
        logger.info("🔍 Scraping ABG internships...")
        offers = []
        
        try:
            url = "https://www.abg.asso.fr/fr/stages"
            params = {'domaine': 'informatique'}
            
            response = self.session.get(url, params=params, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            cards = soup.find_all(['div', 'article'], class_=re.compile(r'offre|offer|card'))
            
            for card in cards[:15]:
                title_elem = card.find(['h2', 'h3', 'a'])
                if title_elem:
                    title = title_elem.text.strip()
                    link = title_elem.get('href', '')
                    if link and not link.startswith('http'):
                        link = f"https://www.abg.asso.fr{link}"
                    
                    offer = InternshipOffer(
                        id=hashlib.md5(title.encode()).hexdigest()[:8],
                        title=title[:200],
                        company="À préciser",
                        location="France",
                        domain="Informatique",
                        keywords=self._extract_keywords(title),
                        duration="6 mois",
                        level="M2/Ingénieur",
                        start_date=None,
                        deadline=None,
                        url=link,
                        description=card.get_text(strip=True)[:500],
                        compensation="Gratification légale",
                        posted_date=datetime.now().isoformat()
                    )
                    offers.append(offer)
            
            logger.info(f"✅ ABG: {len(offers)} offers")
            
        except Exception as e:
            logger.warning(f"ABG error: {e}")
        
        return offers
    
    def _scrape_welcometothejungle(self) -> List[InternshipOffer]:
        """Scrape Welcome To The Jungle"""
        logger.info("🔍 Scraping Welcome To The Jungle...")
        offers = []
        
        try:
            url = "https://www.welcometothejungle.com/fr/jobs"
            params = {
                'query': 'stage',
                'location': 'Toulouse'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            jobs = soup.find_all('a', class_=re.compile(r'job|offer'))
            
            for job in jobs[:15]:
                title = job.text.strip()
                if title and 'stage' in title.lower():
                    offer = InternshipOffer(
                        id=hashlib.md5(title.encode()).hexdigest()[:8],
                        title=title[:200],
                        company="À préciser",
                        location="Toulouse",
                        domain="Informatique",
                        keywords=self._extract_keywords(title),
                        duration="6 mois",
                        level="M2",
                        start_date=None,
                        deadline=None,
                        url=job.get('href', ''),
                        description=title,
                        compensation="À préciser",
                        posted_date=datetime.now().isoformat()
                    )
                    offers.append(offer)
            
            logger.info(f"✅ Welcome To The Jungle: {len(offers)} offers")
            
        except Exception as e:
            logger.warning(f"Welcome To The Jungle error: {e}")
        
        return offers
    
    def _scrape_hellowork(self) -> List[InternshipOffer]:
        """Scrape HelloWork"""
        logger.info("🔍 Scraping HelloWork...")
        offers = []
        
        try:
            url = "https://www.hellowork.com/fr-fr/emploi/recherche.html"
            params = {'k': 'stage informatique', 'l': 'toulouse'}
            
            response = self.session.get(url, params=params, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            jobs = soup.find_all(['div', 'article'], class_=re.compile(r'job|offer'))
            
            for job in jobs[:10]:
                text = job.get_text(strip=True)
                if 'stage' in text.lower():
                    offer = InternshipOffer(
                        id=hashlib.md5(text.encode()).hexdigest()[:8],
                        title=text[:200],
                        company="À préciser",
                        location="Toulouse",
                        domain="Informatique",
                        keywords=self._extract_keywords(text),
                        duration="6 mois",
                        level="M2",
                        start_date=None,
                        deadline=None,
                        url="https://www.hellowork.com",
                        description=text[:500],
                        compensation="À préciser",
                        posted_date=datetime.now().isoformat()
                    )
                    offers.append(offer)
            
            logger.info(f"✅ HelloWork: {len(offers)} offers")
            
        except Exception as e:
            logger.warning(f"HelloWork error: {e}")
        
        return offers
    
    def _extract_keywords(self, text: str) -> List[str]:
        text_lower = text.lower()
        found = [kw for kw in self.KEYWORDS if kw.lower() in text_lower]
        return list(set(found))[:8]
    
    def _filter_relevant_offers(self, offers: List[InternshipOffer]) -> List[InternshipOffer]:
        filtered = []
        for offer in offers:
            text = (offer.title + " " + offer.description).lower()
            if any(kw.lower() in text for kw in self.KEYWORDS):
                filtered.append(offer)
        return filtered
    
    def _deduplicate_offers(self, offers: List[InternshipOffer]) -> List[InternshipOffer]:
        seen = set()
        unique = []
        for offer in offers:
            if offer.hash_id() not in seen:
                seen.add(offer.hash_id())
                unique.append(offer)
        return unique