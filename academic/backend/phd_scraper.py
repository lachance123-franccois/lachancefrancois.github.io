"""
PhD Thesis Scraper - Computer Vision, Signal Processing & Telecommunications
Scrapes PhD positions from multiple academic sources
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
import json
import hashlib
import logging
from dataclasses import dataclass, asdict
import re

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
        """Generate unique hash for the offer"""
        content = f"{self.title}{self.institution}{self.start_date}"
        return hashlib.md5(content.encode()).hexdigest()


class PhDScraper:
    """
    Multi-source PhD position scraper with domain-specific filtering
    """
    
    # Keywords for filtering relevant positions
    RELEVANT_KEYWORDS = [
        'image', 'video', 'computer vision', 'vision par ordinateur',
        'traitement d\'image', 'signal', 'traitement du signal',
        'telecommunication', 'télécommunication', 'radio', '5G', '6G',
        'deep learning', 'machine learning', 'neural network',
        'compression', 'codage', 'multimedia', 'streaming',
        'detection', 'segmentation', 'classification', 
        'reconnaissance', 'reconstruction', 'synthesis',
        'radar', 'lidar', 'satellite', 'remote sensing',
        'optical', 'photonics', 'wireless', 'antenna',
        'modulation', 'coding theory', 'information theory'
    ]
    
    # Toulouse research labs
    TOULOUSE_LABS =[
        'IRIT', 'LAAS-CNRS', 'TéSA', 'ISAE-SUPAERO', 
        'CNES', 'ONERA', 'INPT', 'Université Toulouse',
        'Paul Sabatier', 'INSA Toulouse'
        "Institut Fresnel (Marseille) - Optique, Traitement du Signal & Image",  # UMR 7249 :contentReference[oaicite:2]{index=2}
        "LTSI - Laboratoire Traitement du Signal et de l'Image (Rennes) - INSERM/Univ Rennes 1",  # :contentReference[oaicite:3]{index=3}
        "GIPSA-Lab (Grenoble) - Grenoble Images Parole Signal Automatique",  # :contentReference[oaicite:4]{index=4}
        "Laboratoire des Signaux et Systèmes (L2S) - CNRS/CentraleSupélec/Université Paris-Saclay",  # :contentReference[oaicite:5]{index=5}
        "Institut des Systèmes Intelligents et de Robotique (ISIR) - Sorbonne Univ",  # :contentReference[oaicite:6]{index=6}
        "Laboratoire d'Informatique de Grenoble (LIG)",  # :contentReference[oaicite:7]{index=7}
        "IPOL - Image Processing On Line journal collaborations",  # :contentReference[oaicite:8]{index=8}
        "LIP6 - Laboratoire d'Informatique de Paris 6 (Sorbonne Univ)",  # :contentReference[oaicite:9]{index=9}
        "LRI - Laboratoire de Recherche en Informatique (Paris-Sud / Univ Paris-Saclay)",  # :contentReference[oaicite:10]{index=10}
        "LAAS-CNRS (Toulouse) - Automatique, Robotique et IA",  # :contentReference[oaicite:11]{index=11}
        "MIAI@Grenoble Alpes - IA/Data science",  # :contentReference[oaicite:12]{index=12}
        "LIMSI-CNRS (Orsay) - Traitement du signal, parole & IA",  # :contentReference[oaicite:13]{index=13}
        "Laboratoire Hubert Curien - Saint-Etienne",  # :contentReference[oaicite:14]{index=14}
        "LIST3N - Univ. Technologie Troyes",  # :contentReference[oaicite:15]{index=15}
        "CREATIS - Lyon (Imagerie médicale)",  # :contentReference[oaicite:16]{index=16}
        "LabTAu - Lyon (Traitement d’images & IA)",  # :contentReference[oaicite:17]{index=17}
        "CARMEN - Lyon (Réseaux & informatique)",  # :contentReference[oaicite:18]{index=18}
        "CRNL - Lyon Neurosciences & IA",  # :contentReference[oaicite:19]{index=19}
        "INL - Institut Lumière Matière (Lyon)",  # :contentReference[oaicite:20]{index=20}
        "Laboratoire d’Informatique, de Robotique et de Microélectronique (LIRMM) - Montpellier",  # :contentReference[oaicite:21]{index=21}
        "Université Côte d'Azur - INRIA Sophia Antipolis (IA/Signal)",  # common research center
        "Université Paris-Saclay - Signal & Image research teams",
        "ENS Paris - Équipe de Traitement d’Image et Machine Learning",
        "INRIA Paris - Equipe Parietal (ML & imagerie)", 
        "INRIA Grenoble - équipe de vision/ML",
        "INRIA Lille - équipe Data/Signal",
        "INRIA Bordeaux - équipe IA/vision",
        "INRIA Toulouse - équipe traitement du signal et data",
        "Sorbonne Université - Laboratoire Mathématiques & Applications (I2M)",
        "I2M - Institut de Mathématiques de Marseille",  # :contentReference[oaicite:22]{index=22}
        "IMS Bordeaux - Groupe Signal & Image",  # :contentReference[oaicite:23]{index=23}
        "Univ de Strasbourg - Laboratoire de Vision et Cognition",
        "Univ de Strasbourg - Laboratoire de Traitement du Signal",
        "Institut d'Electronique et des Systèmes - Rennes",
        "Univ de Lille - L2EP (Signal & électrique)",  # :contentReference[oaicite:24]{index=24}
        "Laboratoire SYSTEM@TIC Paris-Est",
        "Centre Borelli - CNRS/ENS Paris-Saclay",
        "Laboratoire MAP5 (Mathématiques & applications, Univ Paris Cité)",
        "Mines Paris - PSL Research team IA/Signal",
        "Télécom Paris - LTCI (Traitement du Signal & image)",  # :contentReference[oaicite:25]{index=25}
        "CEA List (Intelligence digitale & vision)",
        "CEA NeuroSpin (Imagerie & machine learning)",
        "CEA Paris-Saclay - Signal/IA teams",
        "CEA Grenoble - Imagerie & vision teams",
        "Institut Curie - Bio-imagerie & ML",
        "Université de Bordeaux - Data Science & Vision teams",
        "Université de Rennes 1 - IMS",
        "Université de Rennes 1 - ENSCR research teams",
        "Université de Montpellier - Informatique & vision",
        "Université de Nantes - IRCCyN (IA/Robotique)",
        "Université de Technologie de Compiègne - Heudiasyc",
        "Université de Technologie de Troyes - LIST3N",
        "Université de Lorraine - CRAN",
        "Université de Montpellier - LIRMM IA teams",
        "Université Grenoble Alpes - LIG ML/vision",
        "Université Grenoble Alpes - GIPSA Lab",
        "Université Grenoble Alpes - LJK (Mathématiques appliquées)",
        "Université Grenoble Alpes - LISTIC",
        "Université de Toulouse - IRAP (Imagerie spatiale)",
        "Université de Toulouse - LAAS",
        "Université de Toulouse - CESBIO (Satellites & images)",
        "Université de Toulouse - LIS (Traitement et IA)",
        "Université Paris Cité - LIP6 IA/vision",
        "Université Paris Cité - LIMSI",
        "Université Paris Cité - LIP ADE (signaux)",
        "Université Sorbonne Paris Nord - L2TI",
        "Université Côte d'Azur - I3S (Informatique & signal)",
        "Université Nice - XLIM (Vision & signal)",
        "Université de Caen - GREYC",
        "Université de Rouen - LITIS",
        "Université de Bretagne Sud - Lab-STICC",
        "Université de Bretagne Occidentale - Lab-STICC",
        "Université de Brest - Lab-STICC",
        "Université de Poitiers - XLIM",
        "Université de Tours - IRISA",
        "Université de Bretagne - IMT Atlantique Nantes",
        "Université de Lorraine - LORIA",
        "Université de Lyon - LIRIS",
        "Université de Lyon - CEREMADE",
        "Université de Nancy - CRAN teams",
        "Université de Dijon - MITS",
        "Université de Montpellier - Sys’Com",
        "Université de Paris Sud - LRI IA teams",
        "Université d’Orléans - LIFO",
        "Université de Reims - URCA vision/ML",
        "Université Clermont Auvergne - SIGMA",
        "Université de Strasbourg - ICube",
        "Université de Haute Alsace - AS2M",
        "Université de Bretagne Sud - SATIE"
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/html',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8'
        })
    
    def scrape_all_sources(self) -> List[PhDOffer]:
        """Scrape all configured sources"""
        all_offers = []
        
        # Source 1: ABG (Association Bernard Gregory)
        all_offers.extend(self._scrape_abg())
        
        # Source 2: theses.fr
        all_offers.extend(self._scrape_theses_fr())
        
        # Source 3: ADUM
        all_offers.extend(self._scrape_adum())
        
        # Source 4: Direct lab websites
        all_offers.extend(self._scrape_toulouse_labs())
        
        # Filter and deduplicate
        filtered_offers = self._filter_relevant_offers(all_offers)
        unique_offers = self._deduplicate_offers(filtered_offers)
        
        logger.info(f"📚 Total PhD offers found: {len(unique_offers)}")
        return unique_offers
    
    def _scrape_abg(self) -> List[PhDOffer]:
        """Scrape ABG website"""
        logger.info("🔍 Scraping ABG...")
        offers = []
        
        try:
            url = "https://www.abg.asso.fr/fr/candidats/offres"
            params = {
                'f[0]': 'offre_type:1',  # Type: Thèse
                'f[1]': 'offre_secteur:35',  # Secteur: Informatique/Telecom
            }
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find offer cards
            offer_cards = soup.find_all(['article', 'div'], class_=re.compile(r'offre|offer|card'))
            
            for card in offer_cards[:20]:  # Limit to recent offers
                offer = self._parse_abg_offer(card)
                if offer:
                    offers.append(offer)
            
            logger.info(f"✅ ABG: {len(offers)} offers")
            
        except Exception as e:
            logger.error(f"❌ ABG scraping error: {e}")
        
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
            
            # Extract other info
            text_content = card.get_text(strip=True)
            
            return PhDOffer(
                id=hashlib.md5(title.encode()).hexdigest()[:8],
                title=title,
                institution=self._extract_institution(text_content),
                laboratory=self._extract_lab(text_content),
                location=self._extract_location(text_content),
                domain="Image/Signal/Telecom",
                keywords=self._extract_keywords(title + " " + text_content),
                start_date=None,
                duration="3 ans",
                deadline=self._extract_deadline(text_content),
                url=url,
                description=text_content[:500],
                supervisor=None,
                funding="À préciser",
                posted_date=datetime.now().isoformat()
            )
        except Exception as e:
            logger.warning(f"Error parsing ABG offer: {e}")
            return None
    
    def _scrape_theses_fr(self) -> List[PhDOffer]:
        """Scrape theses.fr"""
        logger.info("🔍 Scraping theses.fr...")
        offers = []
        
        try:
            url = "https://www.theses.fr/fr/annonces"
            params = {
                'q': 'image OR signal OR télécommunication',
                'fq': 'pays:FR',
                'sort': 'date desc'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse results
            result_items = soup.find_all(['div', 'article'], class_=re.compile(r'result|these|annonce'))
            
            for item in result_items[:15]:
                offer = self._parse_theses_fr_offer(item)
                if offer:
                    offers.append(offer)
            
            logger.info(f"✅ theses.fr: {len(offers)} offers")
            
        except Exception as e:
            logger.error(f"❌ theses.fr scraping error: {e}")
        
        return offers
    
    def _parse_theses_fr_offer(self, item) -> Optional[PhDOffer]:
        """Parse theses.fr offer"""
        try:
            title = item.find(['h2', 'h3'])
            if not title:
                return None
            
            link = item.find('a', href=True)
            url = link['href'] if link else ""
            if url and not url.startswith('http'):
                url = f"https://www.theses.fr{url}"
            
            return PhDOffer(
                id=hashlib.md5(title.text.encode()).hexdigest()[:8],
                title=title.text.strip(),
                institution="À préciser",
                laboratory="",
                location="France",
                domain="Image/Signal/Telecom",
                keywords=self._extract_keywords(title.text),
                start_date=None,
                duration="3 ans",
                deadline=None,
                url=url,
                description=item.get_text(strip=True)[:400],
                supervisor=None,
                funding="Variable",
                posted_date=datetime.now().isoformat()
            )
        except Exception as e:
            logger.warning(f"Error parsing theses.fr offer: {e}")
            return None
    
    def _scrape_adum(self) -> List[PhDOffer]:
        """Scrape ADUM (system for doctoral schools)"""
        logger.info("🔍 Scraping ADUM...")
        offers = []
        
        try:
            # ADUM Toulouse
            url = "https://www.adum.fr/as/ed/voirpropositions.pl"
            params = {'site': 'TSE'}  # Toulouse
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse table or list of offers
            rows = soup.find_all(['tr', 'li'])
            
            for row in rows[:10]:
                offer = self._parse_adum_offer(row)
                if offer:
                    offers.append(offer)
            
            logger.info(f"✅ ADUM: {len(offers)} offers")
            
        except Exception as e:
            logger.error(f"❌ ADUM scraping error: {e}")
        
        return offers
    
    def _parse_adum_offer(self, element) -> Optional[PhDOffer]:
        """Parse ADUM offer"""
        try:
            text = element.get_text()
            
            # Basic extraction
            title_match = re.search(r'Titre[:\s]+([^\n]+)', text, re.IGNORECASE)
            title = title_match.group(1) if title_match else text[:100]
            
            return PhDOffer(
                id=hashlib.md5(text.encode()).hexdigest()[:8],
                title=title.strip(),
                institution="Université de Toulouse",
                laboratory=self._extract_lab(text),
                location="Toulouse",
                domain="Image/Signal/Telecom",
                keywords=self._extract_keywords(text),
                start_date=None,
                duration="3 ans",
                deadline=None,
                url="https://www.adum.fr",
                description=text[:400],
                supervisor=None,
                funding="Contrat doctoral",
                posted_date=datetime.now().isoformat()
            )
        except Exception as e:
            return None
    
    def _scrape_toulouse_labs(self) -> List[PhDOffer]:
        """Scrape Toulouse research labs directly"""
        logger.info("🔍 Scraping Toulouse labs...")
        offers = []
        
        lab_urls = {
    # Toulouse / Sud-Ouest
    'IRIT': 'https://www.irit.fr/departement/ispr/offres/',
    'LAAS-CNRS': 'https://www.laas.fr/public/fr/recrutement',
    'TéSA': 'https://www.tesa.prd.fr/fr/recrutement/offres',
    'CESBIO': 'https://www.cesbio.cnrs.fr/fr/emplois/',
    'IRAP': 'https://www.irap.omp.eu/emplois/',
    'ONERA Toulouse': 'https://www.onera.fr/fr/carrieres/stages',

    # Paris / Île-de-France
    'L2S': 'https://l2s.centralesupelec.fr/fr/recrutement',
    'LIP6': 'https://www.lip6.fr/emplois',
    'LIMSI': 'https://www.limsi.fr/fr/recrutement',
    'LRI': 'https://www.lri.fr/recrutement/',
    'L2TI': 'https://www.l2ti.univ-paris13.fr/recrutement/',
    'Télécom Paris LTCI': 'https://www.telecom-paris.fr/fr/recrutement',
    'CEA LIST': 'https://list.cea.fr/fr/recrutement/',
    'CEA NeuroSpin': 'https://joliot.cea.fr/drf/joliot/Pages/Entites/NeuroSpin/recrutement.aspx',
    'Institut Curie (Imagerie)': 'https://institut-curie.org/offres-emploi',
    'ENS Paris PSL': 'https://www.ens.psl.eu/recrutement',

    # Grenoble / Alpes
    'GIPSA-lab': 'https://www.gipsa-lab.grenoble-inp.fr/recrutement/',
    'LIG': 'https://www.liglab.fr/fr/recrutement',
    'INRIA Grenoble': 'https://www.inria.fr/fr/recrutement',
    'MIAI Grenoble': 'https://miai.univ-grenoble-alpes.fr/recrutement/',
    'LISTIC': 'https://www.listic.univ-smb.fr/recrutement/',

    # Lyon
    'CREATIS': 'https://www.creatis.insa-lyon.fr/site7/fr/recrutement',
    'LIRIS': 'https://liris.cnrs.fr/recrutement/',
    'CRNL': 'https://www.crnl.fr/fr/recrutement',
    'CARMEN': 'https://carmen.univ-lyon1.fr/site/recrutement/',
    'INL': 'https://inl.cnrs.fr/recrutement/',

    # Rennes / Ouest
    'IRISA': 'https://www.irisa.fr/recrutement',
    'LTSI': 'https://ltsi.univ-rennes.fr/recrutement',
    'IETR': 'https://www.ietr.fr/recrutement',
    'Lab-STICC': 'https://www.labsticc.fr/fr/recrutement',
    'IMT Atlantique': 'https://www.imt-atlantique.fr/fr/recrutement',

    # Montpellier / Sud-Est
    'LIRMM': 'https://www.lirmm.fr/recrutement/',
    'I3S': 'https://www.i3s.unice.fr/recrutement/',
    'INRIA Sophia Antipolis': 'https://www.inria.fr/fr/recrutement',
    'XLIM': 'https://www.xlim.fr/recrutement/',
    
    # Est / Nord
    'ICube Strasbourg': 'https://icube.unistra.fr/recrutement/',
    'LORIA': 'https://www.loria.fr/recrutement/',
    'CRAN': 'https://www.cran.univ-lorraine.fr/recrutement/',
    'GREYC': 'https://www.greyc.fr/recrutement/',
    'LITIS': 'https://www.litislab.fr/recrutement/',

    # Bordeaux
    'IMS Bordeaux': 'https://www.ims-bordeaux.fr/recrutement/',
    'INRIA Bordeaux': 'https://www.inria.fr/fr/recrutement',
}

        
        for lab_name, url in lab_urls.items():
            try:
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Generic parsing - adapt based on site structure
                links = soup.find_all('a', text=re.compile(r'thèse|phd|doctorat', re.IGNORECASE))
                
                for link in links[:5]:
                    offer = PhDOffer(
                        id=hashlib.md5(link.text.encode()).hexdigest()[:8],
                        title=link.text.strip(),
                        institution=lab_name,
                        laboratory=lab_name,
                        location="Toulouse",
                        domain="Image/Signal/Telecom",
                        keywords=self._extract_keywords(link.text),
                        start_date=None,
                        duration="3 ans",
                        deadline=None,
                        url=link.get('href', ''),
                        description=link.text,
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
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text"""
        text_lower = text.lower()
        found_keywords = [
            kw for kw in self.RELEVANT_KEYWORDS 
            if kw.lower() in text_lower
        ]
        return list(set(found_keywords))[:10]  # Max 10 keywords
    
    def _extract_institution(self, text: str) -> str:
        """Extract institution name"""
        for lab in self.TOULOUSE_LABS:
            if lab.lower() in text.lower():
                return lab
        return "À préciser"
    
    def _extract_lab(self, text: str) -> str:
        """Extract laboratory name"""
        for lab in self.TOULOUSE_LABS:
            if lab.lower() in text.lower():
                return lab
        return ""
    
    def _extract_location(self, text: str) -> str:
        """Extract location"""
        if 'toulouse' in text.lower():
            return "Toulouse"
        return "France"
    
    def _extract_deadline(self, text: str) -> Optional[str]:
        """Extract application deadline"""
        deadline_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
        match = re.search(deadline_pattern, text)
        return match.group(0) if match else None
    
    def _filter_relevant_offers(self, offers: List[PhDOffer]) -> List[PhDOffer]:
        """Filter offers by relevance to domain"""
        filtered = []
        
        for offer in offers:
            # Check if any relevant keyword is present
            text_to_check = (offer.title + " " + offer.description).lower()
            
            is_relevant = any(
                kw.lower() in text_to_check 
                for kw in self.RELEVANT_KEYWORDS
            )
            
            if is_relevant or offer.laboratory in self.TOULOUSE_LABS:
                filtered.append(offer)
        
        return filtered
    
    def _deduplicate_offers(self, offers: List[PhDOffer]) -> List[PhDOffer]:
        """Remove duplicate offers based on similarity"""
        seen_hashes = set()
        unique_offers = []
        
        for offer in offers:
            offer_hash = offer.hash_id()
            if offer_hash not in seen_hashes:
                seen_hashes.add(offer_hash)
                unique_offers.append(offer)
        
        return unique_offers
    
    def get_new_offers(self, previous_offers: List[str]) -> List[PhDOffer]:
        """Get only new offers not in previous list"""
        all_offers = self.scrape_all_sources()
        new_offers = [
            offer for offer in all_offers 
            if offer.hash_id() not in previous_offers
        ]
        
        logger.info(f"🆕 {len(new_offers)} new PhD offers")
        return new_offers


# Example usage
if __name__ == "__main__":
    scraper = PhDScraper()
    offers = scraper.scrape_all_sources()
    
    for offer in offers[:3]:
        print(f"\n🎓 {offer.title}")
        print(f"   🏛️  {offer.institution} - {offer.laboratory}")
        print(f"   📍 {offer.location}")
        print(f"   🏷️  {', '.join(offer.keywords[:5])}")
        print(f"   🔗 {offer.url}")
