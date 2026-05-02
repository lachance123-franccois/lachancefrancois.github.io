#!/usr/bin/env python3
"""
Academic Tracker - Mode Stealth
Exécution avec délais aléatoires, cache, et respect des robots.txt
"""

import sys
import time
import random
import json
import logging
from pathlib import Path
from datetime import datetime

from stealth_utils import StealthSession
from crous_scraper import HousingScraper
from phd_scraper import PhDScraper
from internship_scraper import InternshipScraper
from database import DatabaseManager
from email_notifier import EmailNotifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StealthAcademicTracker:
    """Version furtive - scraping éthique et respectueux"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.db = DatabaseManager(self.config.get('database', 'academic_tracker.db'))
        
        # Session furtive
        self.session = StealthSession(
            use_cache=self.config.get('cache', {}).get('enabled', True)
        )
        
        # Scrapers
        self.housing_scraper = HousingScraper()
        self.phd_scraper = PhDScraper()
        self.internship_scraper = InternshipScraper()
        
        # Email (optionnel)
        email_config = self.config.get('email', {})
        if email_config.get('enabled'):
            self.email_notifier = EmailNotifier(**email_config)
        else:
            self.email_notifier = None
        
        logger.info("🕵️ Stealth Academic Tracker initialized")
    
    def run_safe_scraping(self) -> dict:
        """Exécution sécurisée avec pauses longues entre les sources"""
        stats = {
            'start_time': datetime.now(),
            'housing': {'found': 0, 'new': 0},
            'phd': {'found': 0, 'new': 0},
            'internship': {'found': 0, 'new': 0}
        }
        
        # Pause initiale aléatoire (évite le démarrage à heure fixe)
        initial_delay = random.randint(30, 180)
        logger.info(f"Initial warmup delay: {initial_delay}s")
        time.sleep(initial_delay)
        
        # Housing (priorité basse)
        if self.config.get('scraping', {}).get('enable_housing'):
            logger.info("🏠 Safe housing scraping...")
            max_price = self.config.get('scraping', {}).get('housing_max_price', 600)
            offers = self.housing_scraper.search_all(max_price=max_price)
            stats['housing']['found'] = len(offers)
            
            # Pause entre les catégories
            time.sleep(random.uniform(15, 30))
        
        # PhD (priorité moyenne)
        if self.config.get('scraping', {}).get('enable_phd'):
            logger.info("🎓 Safe PhD scraping...")
            offers = self.phd_scraper.scrape_all_sources()
            stats['phd']['found'] = len(offers)
            time.sleep(random.uniform(15, 30))
        
        # Internship (priorité haute - plus de sources)
        if self.config.get('scraping', {}).get('enable_internship'):
            logger.info("💼 Safe internship scraping...")
            offers = self.internship_scraper.scrape_all_sources()
            stats['internship']['found'] = len(offers)
        
        stats['end_time'] = datetime.now()
        stats['duration'] = (stats['end_time'] - stats['start_time']).total_seconds()
        
        self._log_summary(stats)
        return stats
    
    def _log_summary(self, stats: dict):
        """Affiche le résumé"""
        logger.info("\n" + "=" * 50)
        logger.info("📊 SCRAPING SUMMARY")
        logger.info("=" * 50)
        logger.info(f"🏠 Housing: {stats['housing']['found']} offers")
        logger.info(f"🎓 PhD: {stats['phd']['found']} offers")
        logger.info(f"💼 Internship: {stats['internship']['found']} offers")
        logger.info(f"⏱️ Duration: {stats['duration']:.1f}s")
        logger.info("=" * 50)
    
    def close(self):
        """Fermeture propre"""
        self.db.close()


def main():
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config.json')
    parser.add_argument('--no-email', action='store_true')
    
    args = parser.parse_args()
    
    tracker = StealthAcademicTracker(args.config)
    
    try:
        tracker.run_safe_scraping()
        
        if not args.no_email and tracker.email_notifier:
            # Envoyer email (optionnel)
            pass
        
        tracker.close()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        tracker.close()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        tracker.close()
        sys.exit(1)


if __name__ == "__main__":
    main()