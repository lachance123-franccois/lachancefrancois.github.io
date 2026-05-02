#!/usr/bin/env python3
"""
Academic Tracker - Mode Stealth
Exécution avec délais aléatoires, cache, respect des robots.txt,
insertion en base de données, export JSON des thèses et notifications email.
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
        
        # Session furtive (utilisée pour les requêtes HTTP additionnelles si besoin)
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
    
    def _load_config(self, config_path: str) -> dict:
        """Charge la configuration depuis un fichier JSON."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Fichier de configuration introuvable, utilisation des valeurs par défaut")
            return self._default_config()
    
    def _default_config(self) -> dict:
        return {
            'database': 'academic_tracker.db',
            'email': {'enabled': False},
            'scraping': {
                'enable_housing': True,
                'enable_phd': True,
                'enable_internship': True,
                'housing_max_price': 600
            },
            'cache': {'enabled': True}
        }
    
    def run_safe_scraping(self) -> dict:
        """
        Exécution sécurisée :
        - Pause aléatoire initiale
        - Scraping et insertion en base pour chaque catégorie
        - Retourne les statistiques (trouvées, nouvelles)
        """
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
        
        scraping_config = self.config.get('scraping', {})
        
        # ----- Housing -----
        if scraping_config.get('enable_housing', True):
            logger.info("🏠 Scraping des logements...")
            max_price = scraping_config.get('housing_max_price', 600)
            offers = self.housing_scraper.search_all(max_price=max_price)
            stats['housing']['found'] = len(offers)
            # Conversion en dictionnaire
            offers_dict = [offer.to_dict() if hasattr(offer, 'to_dict') else offer for offer in offers]
            new_count = self.db.insert_housing_offers(offers_dict)
            stats['housing']['new'] = new_count
            logger.info(f"🏠 {stats['housing']['found']} trouvées, {new_count} nouvelles")
            time.sleep(random.uniform(15, 30))
        
        # ----- PhD -----
        if scraping_config.get('enable_phd', True):
            logger.info("🎓 Scraping des offres de thèse...")
            offers = self.phd_scraper.scrape_all_sources()
            stats['phd']['found'] = len(offers)
            offers_dict = [offer.to_dict() for offer in offers]
            new_count = self.db.insert_phd_offers(offers_dict)
            stats['phd']['new'] = new_count
            logger.info(f"🎓 {stats['phd']['found']} trouvées, {new_count} nouvelles")
            time.sleep(random.uniform(15, 30))
        
        # ----- Internship -----
        if scraping_config.get('enable_internship', True):
            logger.info("💼 Scraping des offres de stage...")
            offers = self.internship_scraper.scrape_all_sources()
            stats['internship']['found'] = len(offers)
            offers_dict = [offer.to_dict() for offer in offers]
            new_count = self.db.insert_internship_offers(offers_dict)
            stats['internship']['new'] = new_count
            logger.info(f"💼 {stats['internship']['found']} trouvées, {new_count} nouvelles")
        
        stats['end_time'] = datetime.now()
        stats['duration'] = (stats['end_time'] - stats['start_time']).total_seconds()
        
        self._log_summary(stats)
        return stats
    
    def export_phd_offers_to_json(self, output_file: str = "academic/phd_offers.json"):
        """
        Exporte les offres de thèse non encore notifiées (les plus récentes)
        vers un fichier JSON placé dans le dossier public `academic/`.
        """
        phd_offers = self.db.get_new_phd_offers()   # offres non notifiées
        offers_list = []
        for row in phd_offers:
            d = dict(row)
            # Conversion des champs JSON (keywords)
            if 'keywords' in d and isinstance(d['keywords'], str):
                try:
                    d['keywords'] = json.loads(d['keywords'])
                except:
                    d['keywords'] = []
            # Supprimer les champs binaires ou trop longs si nécessaire
            offers_list.append(d)
        
        # Créer le dossier parent si inexistant
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(offers_list, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📄 Exporté {len(offers_list)} offres de thèse vers {output_file}")
        
        # Retourne le nombre d'offres exportées pour vérification
        return len(offers_list)
    
    def send_notifications(self) -> bool:
        """Envoie les notifications email pour toutes les nouvelles offres."""
        if not self.email_notifier:
            logger.info("📧 Notifications email désactivées")
            return False
        
        housing_offers = self.db.get_new_housing_offers()
        phd_offers = self.db.get_new_phd_offers()
        internship_offers = self.db.get_new_internship_offers()
        
        total_new = len(housing_offers) + len(phd_offers) + len(internship_offers)
        if total_new == 0:
            logger.info("Aucune nouvelle offre à notifier")
            return True
        
        recipient = self.config.get('email', {}).get('recipient')
        if not recipient:
            logger.error("Destinataire email non configuré")
            return False
        
        success = self.email_notifier.send_daily_digest(
            recipient, housing_offers, phd_offers, internship_offers
        )
        
        if success:
            # Marquer les offres comme notifiées
            if housing_offers:
                self.db.mark_as_notified('housing', [o['id'] for o in housing_offers])
            if phd_offers:
                self.db.mark_as_notified('phd', [o['id'] for o in phd_offers])
            if internship_offers:
                self.db.mark_as_notified('internship', [o['id'] for o in internship_offers])
            logger.info(f"✅ Email envoyé avec {total_new} nouvelles offres")
        else:
            logger.error("❌ Échec de l'envoi de l'email")
        
        return success
    
    def _log_summary(self, stats: dict):
        logger.info("\n" + "=" * 50)
        logger.info("📊 RÉSUMÉ DU SCRAPING")
        logger.info("=" * 50)
        logger.info(f"🏠 Logements : {stats['housing']['new']}/{stats['housing']['found']} nouvelles")
        logger.info(f"🎓 Thèses     : {stats['phd']['new']}/{stats['phd']['found']} nouvelles")
        logger.info(f"💼 Stages     : {stats['internship']['new']}/{stats['internship']['found']} nouvelles")
        logger.info(f"⏱️  Durée totale : {stats['duration']:.1f}s")
        logger.info("=" * 50)
    
    def close(self):
        self.db.close()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Academic Tracker - Scraping automatisé')
    parser.add_argument('--config', default='config.json', help='Fichier de configuration')
    parser.add_argument('--no-email', action='store_true', help='Désactiver l’envoi des emails')
    parser.add_argument('--export-only', action='store_true', help='Exporter uniquement les thèses (sans scraping)')
    parser.add_argument('--cleanup', type=int, help='Supprimer les offres plus vieilles que N jours')
    parser.add_argument('--stats', action='store_true', help='Afficher les statistiques et quitter')
    
    args = parser.parse_args()
    
    tracker = StealthAcademicTracker(args.config)
    
    try:
        if args.stats:
            stats = tracker.db.get_statistics()
            print("\n📊 Statistiques système :")
            print(f"   Logements : {stats['total_housing']} (en attente : {stats['pending_housing']})")
            print(f"   Thèses     : {stats['total_phd']} (en attente : {stats['pending_phd']})")
            print(f"   Stages     : {stats['total_internship']} (en attente : {stats['pending_internship']})")
            tracker.close()
            return
        
        if args.cleanup:
            tracker.db.cleanup_old_offers(args.cleanup)
            logger.info(f"Nettoyage effectué (offres > {args.cleanup} jours)")
            tracker.close()
            return
        
        if args.export_only:
            # On exporte les thèses depuis la base existante sans rescraper
            count = tracker.export_phd_offers_to_json()
            print(f"✅ Export terminé : {count} offres de thèse exportées")
            tracker.close()
            return
        
        # Exécution normale : scraping + insertion
        stats = tracker.run_safe_scraping()
        
        # Export JSON des thèses (même s'il n'y a pas de nouvelles, on regénère)
        exported = tracker.export_phd_offers_to_json()
        print(f"📄 {exported} offres de thèse exportées vers academic/phd_offers.json")
        
        # Notifications email si demandé
        if not args.no_email:
            tracker.send_notifications()
        
        tracker.close()
        sys.exit(0)
        
    except KeyboardInterrupt:
        logger.info("Interruption par l'utilisateur")
        tracker.close()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erreur fatale : {e}", exc_info=True)
        tracker.close()
        sys.exit(1)


if __name__ == "__main__":
    main()