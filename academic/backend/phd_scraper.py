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
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PhDOffer:
    """Data model for PhD thesis offers"""
    id: str
    title: str
    institution: str
    laboratory: str
    location: str
    domain: str
    keywords: List[str]
    start_date: Optional[str]
    duration: str
    deadline: Optional[str]
    url: str
    description: str
    supervisor: Optional[str]
    funding: Optional[str]
    posted_date: str
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def hash_id(self) -> str:
        content = f"{self.title}{self.institution}{self.start_date}"
        return hashlib.md5(content.encode()).hexdigest()


class PhDScraper:
    """Multi-source PhD position scraper - URLs corrigées"""
    
    RELEVANT_KEYWORDS = [
        'image', 'video', 'computer vision', 'vision par ordinateur',
        'traitement d\'image', 'signal', 'traitement du signal',
        'telecommunication', 'télécommunication', 'radio', '5G', '6G',
        'deep learning', 'machine learning', 'neural network',
        'compression', 'codage', 'multimedia', 'streaming',
        'detection', 'segmentation', 'classification', 'radar', 'lidar'
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
    
    def scrape_all_sources(self) -> List[PhDOffer]:
        """Scrape all configured sources"""
        all_offers = []
        
        # Pause entre les sources
        all_offers.extend(self._scrape_abg())
        time.sleep(random.uniform(3, 8))
        
        all_offers.extend(self._scrape_theses_fr())
        time.sleep(random.uniform(3, 8))
        
        all_offers.extend(self._scrape_toulouse_labs())
        time.sleep(random.uniform(3, 8))
        
        all_offers.extend(self._scrape_euraxess())
        
        filtered_offers = self._filter_relevant_offers(all_offers)
        unique_offers = self._deduplicate_offers(filtered_offers)
        
        logger.info(f"📚 Total PhD offers found: {len(unique_offers)}")
        return unique_offers
    
    def _scrape_abg(self) -> List[PhDOffer]:
        """Scrape ABG website - URL corrigée"""
        logger.info("🔍 Scraping ABG...")
        offers = []
        
        try:
            # URL corrigée
            url = "https://www.abg.asso.fr/fr/offres"
            params = {
                'type': 'these',
                'domaine': 'informatique',
                'page': '1'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Recherche des offres
            cards = soup.find_all(['div', 'article'], class_=re.compile(r'offre|offer|card|item'))
            
            for card in cards[:15]:
                offer = self._parse_abg_offer(card)
                if offer:
                    offers.append(offer)
            
            logger.info(f"✅ ABG: {len(offers)} offers")
            
        except Exception as e:
            logger.warning(f"ABG scraping: {e}")
        
        return offers
    
    def _parse_abg_offer(self, card) -> Optional[PhDOffer]:
        """Parse ABG offer card"""
        try:
            title_elem = card.find(['h2', 'h3', 'a'])
            if not title_elem:
                return None
            
            title = title_elem.text.strip()
            url = title_elem.get('href', '')
            if url and not url.startswith('http'):
                url = f"https://www.abg.asso.fr{url}"
            
            text_content = card.get_text(strip=True)
            
            return PhDOffer(
                id=hashlib.md5(title.encode()).hexdigest()[:8],
                title=title,
                institution=self._extract_institution(text_content),
                laboratory=self._extract_lab(text_content),
                location="France",
                domain="Image/Signal/Telecom",
                keywords=self._extract_keywords(title + " " + text_content),
                start_date=None,
                duration="3 ans",
                deadline=self._extract_deadline(text_content),
                url=url,
                description=text_content[:500],
                supervisor=None,
                funding="Contrat doctoral",
                posted_date=datetime.now().isoformat()
            )
        except Exception as e:
            logger.warning(f"Error parsing ABG offer: {e}")
            return None
    
    def _scrape_theses_fr(self) -> List[PhDOffer]:
        """Scrape theses.fr - API publique"""
        logger.info("🔍 Scraping theses.fr via API...")
        offers = []
        
        try:
            # Utilisation de l'API officielle
            url = "https://theses.fr/api/annonces/search.json"
            params = {
                'q': 'image OR signal OR informatique OR télécommunication',
                'limit': 20,
                'sort': 'date'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get('items', []):
                    offer = PhDOffer(
                        id=hashlib.md5(item.get('title', '')).hexdigest()[:8],
                        title=item.get('title', 'Sans titre'),
                        institution=item.get('institution', 'À préciser'),
                        laboratory=item.get('laboratory', ''),
                        location=item.get('location', 'France'),
                        domain="Image/Signal/Telecom",
                        keywords=self._extract_keywords(item.get('title', '') + " " + item.get('description', '')),
                        start_date=item.get('start_date'),
                        duration="3 ans",
                        deadline=item.get('deadline'),
                        url=item.get('url', ''),
                        description=item.get('description', '')[:500],
                        supervisor=item.get('supervisor'),
                        funding=item.get('funding', 'Contrat doctoral'),
                        posted_date=datetime.now().isoformat()
                    )
                    offers.append(offer)
            
            logger.info(f"✅ theses.fr: {len(offers)} offers")
            
        except Exception as e:
            logger.warning(f"theses.fr error: {e}")
        
        return offers
    
    def _scrape_toulouse_labs(self) -> List[PhDOffer]:
        """Scrape Toulouse research labs - URLs corrigées"""
        logger.info("🔍 Scraping Toulouse labs...")
        offers = []
        
        # URLs vérifiées et corrigées
        lab_urls = {
            'IRIT': 'https://www.irit.fr/recrutement/',
            'LAAS-CNRS': 'https://www.laas.fr/public/fr/offres-emploi',
            'CNES': 'https://cnes.fr/fr/offres-emploi',
            'ONERA': 'https://www.onera.fr/fr/offres-emploi',
        }
        
        for lab_name, url in lab_urls.items():
            try:
                time.sleep(random.uniform(2, 5))
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Chercher les liens contenant "these" ou "phd"
                    links = soup.find_all('a', href=re.compile(r'thèse|these|phd|doctorat|poste', re.IGNORECASE))
                    
                    for link in links[:5]:
                        title = link.text.strip()
                        if title and len(title) > 10:
                            offer = PhDOffer(
                                id=hashlib.md5(title.encode()).hexdigest()[:8],
                                title=title[:200],
                                institution=lab_name,
                                laboratory=lab_name,
                                location="Toulouse",
                                domain="Image/Signal/Telecom",
                                keywords=self._extract_keywords(title),
                                start_date=None,
                                duration="3 ans",
                                deadline=None,
                                url=link.get('href', ''),
                                description=title[:500],
                                supervisor=None,
                                funding="À préciser",
                                posted_date=datetime.now().isoformat()
                            )
                            offers.append(offer)
                
            except Exception as e:
                logger.warning(f"Error scraping {lab_name}: {e}")
                continue
        
        logger.info(f"✅ Toulouse labs: {len(offers)} offers")
        return offers
    
    def _scrape_euraxess(self) -> List[PhDOffer]:
        """Scrape EURAXESS (officiel pour thèses en Europe)"""
        logger.info("🔍 Scraping EURAXESS...")
        offers = []
        
        try:
            url = "https://euraxess.ec.europa.eu/jobs/search"
            params = {
                'keywords': 'computer vision OR signal OR image',
                'country': 'France',
                'page': '1'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                jobs = soup.find_all('div', class_=re.compile(r'job|offer'))
                
                for job in jobs[:15]:
                    title_elem = job.find(['h2', 'h3', 'a'])
                    if title_elem:
                        title = title_elem.text.strip()
                        link = title_elem.get('href', '')
                        if link and not link.startswith('http'):
                            link = f"https://euraxess.ec.europa.eu{link}"
                        
                        offer = PhDOffer(
                            id=hashlib.md5(title.encode()).hexdigest()[:8],
                            title=title[:200],
                            institution="EURAXESS",
                            laboratory="",
                            location="France",
                            domain="Image/Signal/Telecom",
                            keywords=self._extract_keywords(title),
                            start_date=None,
                            duration="3 ans",
                            deadline=None,
                            url=link,
                            description=job.get_text(strip=True)[:500],
                            supervisor=None,
                            funding="Variable",
                            posted_date=datetime.now().isoformat()
                        )
                        offers.append(offer)
            
            logger.info(f"✅ EURAXESS: {len(offers)} offers")
            
        except Exception as e:
            logger.warning(f"EURAXESS error: {e}")
        
        return offers
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords"""
        text_lower = text.lower()
        found = [kw for kw in self.RELEVANT_KEYWORDS if kw.lower() in text_lower]
        return list(set(found))[:8]
    
    def _extract_institution(self, text: str) -> str:
        """Extract institution name"""
        institutions = ['Université', 'CNRS', 'INRIA', 'INSERM', 'CEA', 'INSA', 'IRIT', 'LAAS', 'CNES', 'ONERA']
        for inst in institutions:
            if inst.lower() in text.lower():
                return inst
        return "À préciser"
    
    def _extract_lab(self, text: str) -> str:
        """Extract laboratory name"""
        labs = ['IRIT', 'LAAS', 'LIP6', 'LIRIS', 'GIPSA', 'LIG', 'INRIA', 'CEA']
        for lab in labs:
            if lab.lower() in text.lower():
                return lab
        return ""
    
    def _extract_deadline(self, text: str) -> Optional[str]:
        """Extract deadline"""
        patterns = [r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', r'\d{1,2}\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}']
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(0)
        return None
    
    def _filter_relevant_offers(self, offers: List[PhDOffer]) -> List[PhDOffer]:
        """Filter offers by relevance"""
        filtered = []
        for offer in offers:
            text = (offer.title + " " + offer.description).lower()
            if any(kw.lower() in text for kw in self.RELEVANT_KEYWORDS):
                filtered.append(offer)
        return filtered
    
    def _deduplicate_offers(self, offers: List[PhDOffer]) -> List[PhDOffer]:
        """Remove duplicates"""
        seen = set()
        unique = []
        for offer in offers:
            if offer.hash_id() not in seen:
                seen.add(offer.hash_id())
                unique.append(offer)
        return unique