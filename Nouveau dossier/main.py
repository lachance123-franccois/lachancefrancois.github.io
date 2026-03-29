"""
Script principal d’orchestration - Academic Tracker
Coordonne la collecte des données, les mises à jour de la base de données
et l’envoi des notifications par email
"""

import sys
import time
import json
from datetime import datetime
from pathlib import Path
import logging

from crous_scraper import CROUSScraper
from phd_scraper import PhDScraper
from internship_scraper import InternshipScraper
from database import DatabaseManager
from email_notifier import EmailNotifier

# Configuration du système de logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FrancoisTracker:
    """
    Orchestrateur principal du système de suivi académique
    """
    
    def __init__(self, config_path: str = "config.json"):
        """Initialisation avec le fichier de configuration"""
        self.config = self._load_config(config_path)
        self.db = DatabaseManager(self.config.get('database', 'academic_tracker.db'))
        
        # Initialisation des scrapers
        self.housing_scraper = CROUSScraper()
        self.phd_scraper = PhDScraper()
        self.internship_scraper = InternshipScraper()
        
        # Initialisation du système d’email si activé
        email_config = self.config.get('email', {})
        if email_config.get('enabled', False):
            self.email_notifier = EmailNotifier(
                smtp_server=email_config['smtp_server'],
                smtp_port=email_config['smtp_port'],
                email=email_config['email'],
                password=email_config['password']
            )
        else:
            self.email_notifier = None
        
        logger.info("🚀 Francois Tracker initialisé")
    
    def _load_config(self, config_path: str) -> dict:
        """Chargement de la configuration depuis un fichier JSON"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("⚠️ Fichier de configuration introuvable, utilisation des paramètres par défaut")
            return self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """Retourne la configuration par défaut"""
        return {
            'database': 'francois_tracker.db',
            'email': {
                'enabled': False,
                'recipient': 'lachanceawounang@icloud.com',
                'smtp_server': 'smtp.mail.icloud.com',
                'smtp_port': 587,
                'email': 'lachanceawounang@icloud.com',
                'password': 'qktu-rusa-hqjt-wzim'
            },
            'scraping': {
                'housing_max_price': 450,
                'enable_housing': True,
                'enable_phd': True,
                'enable_internship': True
            }
        }
    
    def run_full_scraping(self) -> dict:
        """
        Lance un cycle complet de collecte pour toutes les sources
        Retourne des statistiques sur l’exécution
        """
        logger.info("=" * 60)
        logger.info("🔄 Démarrage du cycle complet de collecte")
        logger.info("=" * 60)
        
        stats = {
            'start_time': datetime.now(),
            'housing': {'found': 0, 'new': 0, 'duration': 0, 'status': 'pending'},
            'phd': {'found': 0, 'new': 0, 'duration': 0, 'status': 'pending'},
            'internship': {'found': 0, 'new': 0, 'duration': 0, 'status': 'pending'},
            'errors': []
        }
        
        scraping_config = self.config.get('scraping', {})
        
        # Collecte des offres de logement
        if scraping_config.get('enable_housing', True):
            stats['housing'] = self._scrape_housing()
        
        # Collecte des offres de thèse
        if scraping_config.get('enable_phd', True):
            stats['phd'] = self._scrape_phd()
        
        # Collecte des offres de stage
        if scraping_config.get('enable_internship', True):
            stats['internship'] = self._scrape_internship()
        
        stats['end_time'] = datetime.now()
        stats['total_duration'] = (stats['end_time'] - stats['start_time']).total_seconds()
        
        # Affichage du résumé
        self._log_summary(stats)
        
        return stats
    
    def _scrape_housing(self) -> dict:
        """Collecte des offres de logement"""
        logger.info("\n🏠 Collecte des logements CROUS...")
        start_time = time.time()
        
        try:
            max_price = self.config.get('scraping', {}).get('housing_max_price', 600)
            offers = self.housing_scraper.search_toulouse_housing(max_price=max_price)
            
            # Conversion en dictionnaires
            offers_dict = [offer.to_dict() for offer in offers]
            
            # Insertion dans la base de données
            new_count = self.db.insert_housing_offers(offers_dict)
            
            duration = time.time() - start_time
            
            # Enregistrement de l’exécution dans la base
            self.db.log_scraping_run(
                'housing', len(offers), new_count, duration, 'success'
            )
            
            return {
                'found': len(offers),
                'new': new_count,
                'duration': duration,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"❌ Échec de la collecte des logements : {e}")
            duration = time.time() - start_time
            
            self.db.log_scraping_run(
                'housing', 0, 0, duration, 'error', str(e)
            )
            
            return {
                'found': 0,
                'new': 0,
                'duration': duration,
                'status': 'error',
                'error': str(e)
            }
    
    def _scrape_phd(self) -> dict:
        """Collecte des offres de thèse"""
        logger.info("\n🎓 Collecte des offres de doctorat...")
        start_time = time.time()
        
        try:
            offers = self.phd_scraper.scrape_all_sources()
            
            # Conversion en dictionnaires
            offers_dict = [offer.to_dict() for offer in offers]
            
            # Insertion dans la base de données
            new_count = self.db.insert_phd_offers(offers_dict)
            
            duration = time.time() - start_time
            
            # Enregistrement de l’exécution
            self.db.log_scraping_run(
                'phd', len(offers), new_count, duration, 'success'
            )
            
            return {
                'found': len(offers),
                'new': new_count,
                'duration': duration,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"❌ Échec de la collecte des thèses : {e}")
            duration = time.time() - start_time
            
            self.db.log_scraping_run(
                'phd', 0, 0, duration, 'error', str(e)
            )
            
            return {
                'found': 0,
                'new': 0,
                'duration': duration,
                'status': 'error',
                'error': str(e)
            }
    
    def _scrape_internship(self) -> dict:
        """Collecte des offres de stage"""
        logger.info("\n💼 Collecte des offres de stage...")
        start_time = time.time()
        
        try:
            offers = self.internship_scraper.scrape_all_sources()
            
            # Conversion en dictionnaires
            offers_dict = [offer.to_dict() for offer in offers]
            
            # Insertion dans la base de données
            new_count = self.db.insert_internship_offers(offers_dict)
            
            duration = time.time() - start_time
            
            # Enregistrement de l’exécution
            self.db.log_scraping_run(
                'internship', len(offers), new_count, duration, 'success'
            )
            
            return {
                'found': len(offers),
                'new': new_count,
                'duration': duration,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"❌ Échec de la collecte des stages : {e}")
            duration = time.time() - start_time
            
            self.db.log_scraping_run(
                'internship', 0, 0, duration, 'error', str(e)
            )
            
            return {
                'found': 0,
                'new': 0,
                'duration': duration,
                'status': 'error',
                'error': str(e)
            }
    
    def send_notifications(self) -> bool:
        """Envoi des notifications email pour les nouvelles offres"""
        if not self.email_notifier:
            logger.info("📧 Notifications email désactivées")
            return False
        
        logger.info("\n📧 Préparation des notifications email...")
        
        # Récupération des nouvelles offres
        housing_offers = self.db.get_new_housing_offers()
        phd_offers = self.db.get_new_phd_offers()
        internship_offers = self.db.get_new_internship_offers()
        
        total_new = len(housing_offers) + len(phd_offers) + len(internship_offers)
        
        if total_new == 0:
            logger.info("✅ Aucune nouvelle offre à notifier")
            return True
        
        # Envoi de l’email
        recipient = self.config.get('email', {}).get('recipient')
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
        
        return success
    
    def _log_summary(self, stats: dict):
        """Affiche le résumé de la collecte"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 RÉSUMÉ DE LA COLLECTE")
        logger.info("=" * 60)
        
        logger.info(f"🏠 Logements : {stats['housing']['new']}/{stats['housing']['found']} nouveaux "
                   f"({stats['housing']['duration']:.1f}s) - {stats['housing']['status']}")
        
        logger.info(f"🎓 Thèses : {stats['phd']['new']}/{stats['phd']['found']} nouvelles "
                   f"({stats['phd']['duration']:.1f}s) - {stats['phd']['status']}")
        
        logger.info(f"💼 Stages : {stats['internship']['new']}/{stats['internship']['found']} nouveaux "
                   f"({stats['internship']['duration']:.1f}s) - {stats['internship']['status']}")
        
        total_new = (stats['housing']['new'] + stats['phd']['new'] + 
                     stats['internship']['new'])
        
        logger.info(f"\n✨ Total des nouvelles offres : {total_new}")
        logger.info(f"⏱️  Durée totale : {stats['total_duration']:.1f}s")
        logger.info("=" * 60 + "\n")
    
    def get_statistics(self) -> dict:
        """Retourne les statistiques globales du système"""
        return self.db.get_statistics()
    
    def cleanup_old_data(self, days: int = 90):
        """Suppression des offres anciennes"""
        logger.info(f"🧹 Suppression des offres de plus de {days} jours...")
        deleted = self.db.cleanup_old_offers(days)
        logger.info(f"✅ {deleted} offres supprimées")
    
    def close(self):
        """Fermeture de la connexion à la base de données"""
        self.db.close()


def main():
    """Point d’entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Academic Tracker - Suivi automatisé des opportunités')
    parser.add_argument('--config', default='config.json', help='Chemin vers le fichier de configuration')
    parser.add_argument('--no-email', action='store_true', help='Désactiver l’envoi des emails')
    parser.add_argument('--cleanup', type=int, help='Supprimer les offres plus anciennes que N jours')
    parser.add_argument('--stats', action='store_true', help='Afficher uniquement les statistiques')
    
    args = parser.parse_args()
    
    tracker = FrancoisTracker(args.config)
    
    try:
        if args.stats:
            # Affichage des statistiques uniquement
            stats = tracker.get_statistics()
            print("\n📊 Statistiques du système :")
            print(f"   Total logements : {stats['total_housing']}")
            print(f"   Total thèses : {stats['total_phd']}")
            print(f"   Total stages : {stats['total_internship']}")
            print(f"   Notifications en attente : {stats['pending_housing'] + stats['pending_phd'] + stats['pending_internship']}")
        
        elif args.cleanup:
            # Nettoyage des données anciennes
            tracker.cleanup_old_data(args.cleanup)
        
        else:
            # Exécution complète de la collecte
            tracker.run_full_scraping()
            
            # Envoi des notifications sauf si désactivé
            if not args.no_email:
                tracker.send_notifications()
        
        tracker.close()
        sys.exit(0)
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ Interruption par l’utilisateur")
        tracker.close()
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"\n❌ Erreur fatale : {e}")
        tracker.close()
        sys.exit(1)


if __name__ == "__main__":
    main()
