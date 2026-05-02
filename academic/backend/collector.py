#!/usr/bin/env python3
"""
Collecteur unifié - RSS + APIs + Emails
Produit un fichier JSON unique pour le frontend
"""

import json
import time
import requests
import feedparser
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
import hashlib
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class UnifiedCollector:
    """Collecte les offres depuis RSS, APIs, et emails"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.rss_feeds = self._load_rss_feeds()
        self.all_offers = {
            "last_update": datetime.now().isoformat(),
            "phd": [],
            "internship": [],
            "housing": []
        }
        self.seen_hashes = set()
    
    def _load_config(self, path: str) -> dict:
        """Charge la configuration"""
        default = {
            "cache_duration_hours": 6,
            "output_file": "data/all_offers.json",
            "max_offers_per_source": 20
        }
        try:
            with open(path, 'r') as f:
                return {**default, **json.load(f)}
        except:
            return default
    
    def _load_rss_feeds(self) -> dict:
        """Charge la liste des flux RSS"""
        try:
            with open("rss_feeds.json", 'r') as f:
                return json.load(f)
        except:
            logger.warning("rss_feeds.json non trouvé, création d'un fichier vide")
            return {"phd": [], "internship": [], "housing": []}
    
    def _hash_offer(self, title: str, url: str) -> str:
        """Génère un hash unique pour éviter les doublons"""
        return hashlib.md5(f"{title}{url}".encode()).hexdigest()
    
    def fetch_rss_feed(self, feed_url: str, source_name: str, category: str) -> List[Dict]:
        """Récupère un flux RSS et le convertit en offres"""
        offers = []
        try:
            logger.info(f"📡 Fetching RSS: {source_name}")
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:self.config.get("max_offers_per_source", 20)]:
                # Extraction des données
                title = entry.get('title', 'Sans titre')
                link = entry.get('link', '')
                description = entry.get('description', entry.get('summary', ''))
                published = entry.get('published', datetime.now().isoformat())
                
                # Nettoyage HTML dans la description
                import re
                description = re.sub('<[^<]+?>', '', description)[:500]
                
                offer = {
                    "id": self._hash_offer(title, link),
                    "title": title,
                    "source": source_name,
                    "url": link,
                    "description": description,
                    "published": published,
                    "category": category,
                    "type": "phd" if "theses" in source_name.lower() or "phd" in source_name.lower() 
                            else "internship" if "stage" in source_name.lower() 
                            else "housing"
                }
                
                # Extraction de mots-clés
                offer["keywords"] = self._extract_keywords(title + " " + description)
                
                offers.append(offer)
            
            logger.info(f"✅ {source_name}: {len(offers)} offres")
            
        except Exception as e:
            logger.error(f"❌ Erreur RSS {source_name}: {e}")
        
        return offers
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extrait les mots-clés pertinents"""
        keywords_list = [
            'image', 'video', 'computer vision', 'vision par ordinateur',
            'signal', 'traitement du signal', 'deep learning', 'machine learning',
            '5G', '6G', 'telecom', 'réseaux', 'IA', 'AI', 'intelligence artificielle',
            'python', 'pytorch', 'tensorflow', 'opencv', 'matlab'
        ]
        text_lower = text.lower()
        found = [kw for kw in keywords_list if kw.lower() in text_lower]
        return list(set(found))[:8]
    
    def fetch_indeed_api(self) -> List[Dict]:
        """Utilise l'API Indeed Publisher (gratuite)"""
        offers = []
        # Note: Nécessite une clé API Indeed
        # https://publisher.indeed.com/
        
        api_key = self.config.get("indeed_api_key", "")
        if not api_key:
            logger.info("ℹ️ Indeed API non configurée (clé manquante)")
            return []
        
        try:
            params = {
                "publisher": api_key,
                "q": "stage+informatique+signal+image",
                "l": "Toulouse",
                "sort": "date",
                "limit": 20
            }
            response = requests.get("http://api.indeed.com/ads/apisearch", params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                for job in data.get("results", []):
                    offer = {
                        "id": self._hash_offer(job.get("jobtitle", ""), job.get("url", "")),
                        "title": job.get("jobtitle", ""),
                        "source": "Indeed",
                        "url": job.get("url", ""),
                        "description": job.get("snippet", "")[:500],
                        "company": job.get("company", ""),
                        "location": job.get("formattedLocation", ""),
                        "published": job.get("date", datetime.now().isoformat()),
                        "category": "internship",
                        "keywords": self._extract_keywords(job.get("jobtitle", ""))
                    }
                    offers.append(offer)
            logger.info(f"✅ Indeed API: {len(offers)} offres")
        except Exception as e:
            logger.error(f"❌ Indeed API error: {e}")
        
        return offers
    
    def fetch_github_jobs(self) -> List[Dict]:
        """Récupère les offres GitHub Jobs"""
        offers = []
        try:
            url = "https://jobs.github.com/positions.json"
            params = {"description": "machine learning OR computer vision OR signal", "location": "france"}
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                jobs = response.json()
                for job in jobs[:20]:
                    offer = {
                        "id": self._hash_offer(job.get("title", ""), job.get("url", "")),
                        "title": job.get("title", ""),
                        "source": "GitHub Jobs",
                        "url": job.get("url", ""),
                        "description": job.get("description", "")[:500],
                        "company": job.get("company", ""),
                        "location": job.get("location", ""),
                        "published": job.get("created_at", datetime.now().isoformat()),
                        "category": "internship" if "intern" in job.get("title", "").lower() else "job",
                        "keywords": self._extract_keywords(job.get("title", ""))
                    }
                    offers.append(offer)
            logger.info(f"✅ GitHub Jobs: {len(offers)} offres")
        except Exception as e:
            logger.error(f"❌ GitHub Jobs error: {e}")
        return offers
    
    def run(self):
        """Exécute la collecte complète"""
        logger.info("🚀 Démarrage de la collecte unifiée")
        
        # 1. Récupération des flux RSS (PhD + Stages)
        for category in ["phd", "internship", "housing"]:
            for feed in self.rss_feeds.get(category, []):
                offers = self.fetch_rss_feed(feed["url"], feed["name"], category)
                for offer in offers:
                    if offer["id"] not in self.seen_hashes:
                        self.seen_hashes.add(offer["id"])
                        self.all_offers[category].append(offer)
        
        # 2. Indeed API
        indeed_offers = self.fetch_indeed_api()
        for offer in indeed_offers:
            if offer["id"] not in self.seen_hashes:
                self.seen_hashes.add(offer["id"])
                self.all_offers["internship"].append(offer)
        
        # 3. GitHub Jobs
        github_offers = self.fetch_github_jobs()
        for offer in github_offers:
            if offer["id"] not in self.seen_hashes and offer["category"] == "internship":
                self.seen_hashes.add(offer["id"])
                self.all_offers["internship"].append(offer)
        
        # 4. Sauvegarde du fichier JSON
        self.all_offers["last_update"] = datetime.now().isoformat()
        self.all_offers["total"] = {
            "phd": len(self.all_offers["phd"]),
            "internship": len(self.all_offers["internship"]),
            "housing": len(self.all_offers["housing"])
        }
        
        output_path = self.config.get("output_file", "data/all_offers.json")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.all_offers, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Collecte terminée !")
        logger.info(f"   📄 Fichier: {output_path}")
        logger.info(f"   🎓 Thèses: {self.all_offers['total']['phd']}")
        logger.info(f"   💼 Stages: {self.all_offers['total']['internship']}")


def main():
    collector = UnifiedCollector()
    collector.run()


if __name__ == "__main__":
    main()