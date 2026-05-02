"""
Internship Scraper - Computer Vision, Signal Processing & Telecommunications
Scrapes Master/Engineering internship offers from academic and industry sources
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Optional
import hashlib
import logging
from dataclasses import dataclass, asdict
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class InternshipOffer:
    """Data model for internship offers"""
    id: str
    title: str
    company: str
    location: str
    domain: str
    keywords: List[str]
    duration: str
    level: str  # M1, M2, Ingénieur
    start_date: Optional[str]
    deadline: Optional[str]
    url: str
    description: str
    compensation: Optional[str]
    posted_date: str
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def hash_id(self) -> str:
        """Generate unique hash for the offer"""
        content = f"{self.title}{self.company}{self.start_date}"
        return hashlib.md5(content.encode()).hexdigest()


class InternshipScraper:
    """
    Multi-source internship scraper for image/signal/telecom domain
    """
    
    # Relevant keywords
    KEYWORDS = [
        'image', 'video', 'computer vision', 'vision',
        'traitement d\'image', 'signal', 'traitement du signal',
        'telecommunication', 'télécommunication', 'radio',
        'deep learning', 'machine learning', 'IA', 'AI',
        'compression', 'codage', 'multimedia',
        'detection', 'segmentation', 'classification',
        'radar', 'lidar', 'satellite', 'drone',
        '5G', '6G', 'wireless', 'antenna', 'IoT'
    ]
    
    # Target companies and labs in Toulouse
    TOULOUSE_ENTITIES =[
    "Airbus", "Airbus Defence and Space", "Airbus Operations", "Airbus Helicopters",
    "ATR", "Stelia Aerospace", "Latécoère Groupe", "Liebherr-Aerospace Toulouse",
    "Safran Nacelles", "Thales Alenia Space", "Thales Group", "Collins Aerospace",
    "Honeywell Aerospace Toulouse", "Daher Aerospace", "Mecachrome Groupe",
    "Sogeclair Aerospace", "Satys", "Nexeya", "Hemeria", "Delair",
    "Donecle", "Akka Technologies Toulouse", "Actia Group", "Expleo Group",
    "CGI Toulouse", "Capgemini Toulouse", "Atos Toulouse", "SII Toulouse",
    "Assystem France", "Serma Ingénierie", "Spherea", "Easymile",
    "Schneider Electric IT France", "Vitesco Technologies France",
    "Migen", "Reel SAS", "Actemium Maintenance Toulouse",
    "Montech SARL", "Serres Outils Service", "SAS Hemao", "Kallisto",
    "Aéro Maintenance", "Embedded Systems Toulouse", "Noveltis",
    "Magellium Artal Group", "Artal Technologies", "INTEL Toulouse R&D",
    "R&D Optique & Photonique Toulouse", "DOTA ONERA Toulouse",
    "CNES Centre National d’Etudes Spatiales", "Onera", "IRT Saint Exupéry",
    "LAAS-CNRS Toulouse", "IRIT Toulouse", "Toulouse Brain & Cognition Lab",
    "Blue Water Intelligence", "U-Space", "Infinite Orbits Space",
    "Look Up Space", "Alpha Impulsion", "IoT Valley Startups",
    "Voelabs", "Ascendance FT", "MerciYanis", "Naïo Technologies",
    "BTBP Robotics", "BotDesign", "Medexprim", "Elter",
    "Inbenta Toulouse", "Embedded Map Toulouse", "6Wind Telecom",
    "S.M.T. Société de Montage Téléphonique", "Elokence", "Edix",
    "RAmces Services", "Actemium Industrie", "Automation Experts Toulouse",
    "Robotic Solutions Toulouse", "Toulouse Vision Systems", "Signal Processing Labs Toulouse",
    "Image Analysis Technologies", "Photonics & Imaging Solutions",
    "Optical Instrumentation Toulouse", "Laser Systems Toulouse",
    "Industrial Vision Robotics", "Automated Control Systems",
    "Embedded AI Solutions Toulouse", "Data Driven Vision Lab",
    "Smart Sensors & Robotics", "Connected Devices Toulouse",
    "Telecom Network Solutions Toulouse", "Network & Telecom R&D Labs",
    "Cyber-Physical Systems Toulouse", "Smart Mobility Toulouse",
    "Industrial IoT Toulouse", "Energy Systems Toulouse",
    "Electrical Automation Partners", "Advanced Controls Toulouse",
    "Machine Vision Group Toulouse", "Autonomous Systems R&D",
    "Biomedical Imaging Toulouse", "Medical Signal Processing Systems",
    "Advanced Robotics Toulouse", "Machine Learning Vision Toulouse"
]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/html',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8'
        })
    
    def scrape_all_sources(self) -> List[InternshipOffer]:
        """Scrape all configured sources"""
        all_offers = []
        
        # Source 1: ABG
        all_offers.extend(self._scrape_abg())
        
        # Source 2: HelloWork / RegionsJob
        all_offers.extend(self._scrape_hellowork())
        
        # Source 3: Indeed
        all_offers.extend(self._scrape_indeed())
        
        # Source 4: Direct university job boards
        all_offers.extend(self._scrape_university_boards())
        
        # Filter and deduplicate
        filtered_offers = self._filter_relevant_offers(all_offers)
        unique_offers = self._deduplicate_offers(filtered_offers)
        
        logger.info(f"💼 Total internship offers found: {len(unique_offers)}")
        return unique_offers
    
    def _scrape_abg(self) -> List[InternshipOffer]:
        """Scrape ABG internships"""
        logger.info("🔍 Scraping ABG internships...")
        offers = []
        
        try:
            url = "https://www.abg.asso.fr/fr/candidats/offres"
            params = {
                'f[0]': 'offre_type:2',  # Type: Stage
                'f[1]': 'offre_secteur:35',  # Secteur: Informatique/Telecom
            }
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            cards = soup.find_all(['article', 'div'], class_=re.compile(r'offre|card'))
            
            for card in cards[:20]:
                offer = self._parse_abg_internship(card)
                if offer:
                    offers.append(offer)
            
            logger.info(f"✅ ABG: {len(offers)} internships")
            
        except Exception as e:
            logger.error(f"❌ ABG scraping error: {e}")
        
        return offers
    
    def _parse_abg_internship(self, card) -> Optional[InternshipOffer]:
        """Parse ABG internship card"""
        try:
            title_elem = card.find(['h2', 'h3', 'a'])
            if not title_elem:
                return None
            
            title = title_elem.text.strip()
            url = title_elem.get('href', '')
            if url and not url.startswith('http'):
                url = f"https://www.abg.asso.fr{url}"
            
            text_content = card.get_text(strip=True)
            
            return InternshipOffer(
                id=hashlib.md5(title.encode()).hexdigest()[:8],
                title=title,
                company=self._extract_company(text_content),
                location=self._extract_location(text_content),
                domain="Image/Signal/Telecom",
                keywords=self._extract_keywords(title + " " + text_content),
                duration=self._extract_duration(text_content),
                level=self._extract_level(text_content),
                start_date=self._extract_start_date(text_content),
                deadline=None,
                url=url,
                description=text_content[:500],
                compensation=self._extract_compensation(text_content),
                posted_date=datetime.now().isoformat()
            )
        except Exception as e:
            logger.warning(f"Error parsing ABG internship: {e}")
            return None
    
    def _scrape_hellowork(self) -> List[InternshipOffer]:
        """Scrape HelloWork/RegionsJob"""
        logger.info("🔍 Scraping HelloWork...")
        offers = []
        
        try:
            url = "https://www.hellowork.com/fr-fr/emplois/recherche.html"
            params = {
                'k': 'stage image signal',
                'l': 'toulouse'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            job_cards = soup.find_all(['article', 'div'], class_=re.compile(r'job|offer|card'))
            
            for card in job_cards[:15]:
                offer = self._parse_hellowork_offer(card)
                if offer and 'stage' in offer.title.lower():
                    offers.append(offer)
            
            logger.info(f"✅ HelloWork: {len(offers)} internships")
            
        except Exception as e:
            logger.error(f"❌ HelloWork scraping error: {e}")
        
        return offers
    
    def _parse_hellowork_offer(self, card) -> Optional[InternshipOffer]:
        """Parse HelloWork job card"""
        try:
            title = card.find(['h2', 'h3'])
            if not title:
                return None
            
            company = card.find(class_=re.compile(r'company|entreprise'))
            location = card.find(class_=re.compile(r'location|lieu'))
            
            link = card.find('a', href=True)
            url = link['href'] if link else ""
            
            return InternshipOffer(
                id=hashlib.md5(title.text.encode()).hexdigest()[:8],
                title=title.text.strip(),
                company=company.text.strip() if company else "À préciser",
                location=location.text.strip() if location else "Toulouse",
                domain="Image/Signal/Telecom",
                keywords=self._extract_keywords(title.text),
                duration="5-6 mois",
                level="M2",
                start_date=None,
                deadline=None,
                url=url,
                description=card.get_text(strip=True)[:400],
                compensation="Gratification légale",
                posted_date=datetime.now().isoformat()
            )
        except Exception as e:
            return None
    
    def _scrape_indeed(self) -> List[InternshipOffer]:
        """Scrape Indeed"""
        logger.info("🔍 Scraping Indeed...")
        offers = []
        
        try:
            url = "https://fr.indeed.com/jobs"
            params = {
                'q': 'stage image traitement signal',
                'l': 'Toulouse',
                'sort': 'date'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Indeed has specific structure
            job_cards = soup.find_all('div', class_=re.compile(r'job_seen_beacon|jobsearch'))
            
            for card in job_cards[:15]:
                offer = self._parse_indeed_offer(card)
                if offer:
                    offers.append(offer)
            
            logger.info(f"✅ Indeed: {len(offers)} internships")
            
        except Exception as e:
            logger.error(f"❌ Indeed scraping error: {e}")
        
        return offers
    
    def _parse_indeed_offer(self, card) -> Optional[InternshipOffer]:
        """Parse Indeed job card"""
        try:
            title = card.find(['h2', 'span'], class_=re.compile(r'jobTitle'))
            company = card.find(['span', 'div'], class_=re.compile(r'companyName'))
            
            if not title:
                return None
            
            return InternshipOffer(
                id=hashlib.md5(title.text.encode()).hexdigest()[:8],
                title=title.text.strip(),
                company=company.text.strip() if company else "À préciser",
                location="Toulouse",
                domain="Image/Signal/Telecom",
                keywords=self._extract_keywords(title.text),
                duration="6 mois",
                level="M2/Ingénieur",
                start_date=None,
                deadline=None,
                url="https://fr.indeed.com",
                description=card.get_text(strip=True)[:400],
                compensation="Selon convention",
                posted_date=datetime.now().isoformat()
            )
        except Exception as e:
            return None
    
    def _scrape_university_boards(self) -> List[InternshipOffer]:
        """Scrape university job boards"""
        logger.info("🔍 Scraping university boards...")
        offers = []
        
        # Toulouse universities often post on their websites
        boards = [
            'https://www.univ-tlse3.fr/stages-emplois',
            'https://www.insa-toulouse.fr/fr/entreprises/offres.html'
        ]
        
        for board_url in boards:
            try:
                response = self.session.get(board_url, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Generic parsing
                links = soup.find_all('a', text=re.compile(r'stage', re.IGNORECASE))
                
                for link in links[:5]:
                    offer = InternshipOffer(
                        id=hashlib.md5(link.text.encode()).hexdigest()[:8],
                        title=link.text.strip(),
                        company="Université de Toulouse",
                        location="Toulouse",
                        domain="Image/Signal/Telecom",
                        keywords=self._extract_keywords(link.text),
                        duration="4-6 mois",
                        level="M1/M2",
                        start_date=None,
                        deadline=None,
                        url=link.get('href', ''),
                        description=link.text,
                        compensation="Gratification légale",
                        posted_date=datetime.now().isoformat()
                    )
                    offers.append(offer)
                
            except Exception as e:
                logger.warning(f"Error scraping university board: {e}")
                continue
        
        logger.info(f"✅ University boards: {len(offers)} internships")
        return offers
    
    # Helper methods
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords"""
        text_lower = text.lower()
        found = [kw for kw in self.KEYWORDS if kw.lower() in text_lower]
        return list(set(found))[:8]
    
    def _extract_company(self, text: str) -> str:
        """Extract company name"""
        for entity in self.TOULOUSE_ENTITIES:
            if entity.lower() in text.lower():
                return entity
        return "À préciser"
    
    def _extract_location(self, text: str) -> str:
        """Extract location"""
        if 'toulouse' in text.lower():
            return "Toulouse"
        return "France"
    
    def _extract_duration(self, text: str) -> str:
        """Extract internship duration"""
        duration_pattern = r'(\d+)\s*(mois|months)'
        match = re.search(duration_pattern, text.lower())
        if match:
            return f"{match.group(1)} mois"
        return "5-6 mois"
    
    def _extract_level(self, text: str) -> str:
        """Extract academic level"""
        text_lower = text.lower()
        if 'm2' in text_lower or 'master 2' in text_lower:
            return "M2"
        elif 'm1' in text_lower or 'master 1' in text_lower:
            return "M1"
        elif 'ingénieur' in text_lower or 'engineer' in text_lower:
            return "Ingénieur"
        return "M2/Ingénieur"
    
    def _extract_start_date(self, text: str) -> Optional[str]:
        """Extract start date"""
        date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
        match = re.search(date_pattern, text)
        return match.group(0) if match else None
    
    def _extract_compensation(self, text: str) -> Optional[str]:
        """Extract compensation info"""
        if 'gratification' in text.lower():
            return "Gratification légale"
        comp_pattern = r'(\d+)\s*€'
        match = re.search(comp_pattern, text)
        if match:
            return f"{match.group(1)}€/mois"
        return "À préciser"
    
    def _filter_relevant_offers(self, offers: List[InternshipOffer]) -> List[InternshipOffer]:
        """Filter offers by relevance"""
        filtered = []
        
        for offer in offers:
            text_to_check = (offer.title + " " + offer.description).lower()
            
            is_relevant = any(
                kw.lower() in text_to_check 
                for kw in self.KEYWORDS
            )
            
            if is_relevant or offer.company in self.TOULOUSE_ENTITIES:
                filtered.append(offer)
        
        return filtered
    
    def _deduplicate_offers(self, offers: List[InternshipOffer]) -> List[InternshipOffer]:
        """Remove duplicates"""
        seen_hashes = set()
        unique_offers = []
        
        for offer in offers:
            offer_hash = offer.hash_id()
            if offer_hash not in seen_hashes:
                seen_hashes.add(offer_hash)
                unique_offers.append(offer)
        
        return unique_offers
    
    def get_new_offers(self, previous_offers: List[str]) -> List[InternshipOffer]:
        """Get only new offers"""
        all_offers = self.scrape_all_sources()
        new_offers = [
            offer for offer in all_offers 
            if offer.hash_id() not in previous_offers
        ]
        
        logger.info(f"🆕 {len(new_offers)} new internship offers")
        return new_offers


if __name__ == "__main__":
    scraper = InternshipScraper()
    offers = scraper.scrape_all_sources()
    
    for offer in offers[:3]:
        print(f"\n💼 {offer.title}")
        print(f"   🏢 {offer.company}")
        print(f"   📍 {offer.location}")
        print(f"   ⏱️  {offer.duration} - {offer.level}")
        print(f"   🏷️  {', '.join(offer.keywords[:4])}")
