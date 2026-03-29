"""
Database Manager - SQLite with tracking and deduplication
Manages storage of housing, PhD, and internship offers
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    SQLite database manager for academic tracker
    """
    
    def __init__(self, db_path: str = "academic_tracker.db"):
        self.db_path = db_path
        self.conn = None
        self.initialize_database()
    
    def initialize_database(self):
        """Create database and tables if they don't exist"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        
        # Housing offers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS housing_offers (
                id TEXT PRIMARY KEY,
                hash_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                location TEXT,
                price REAL,
                type TEXT,
                surface TEXT,
                available_date TEXT,
                url TEXT,
                description TEXT,
                distance_to_uni TEXT,
                posted_date TEXT,
                scraped_at TEXT,
                is_new INTEGER DEFAULT 1,
                notified INTEGER DEFAULT 0
            )
        """)
        
        # PhD offers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS phd_offers (
                id TEXT PRIMARY KEY,
                hash_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                institution TEXT,
                laboratory TEXT,
                location TEXT,
                domain TEXT,
                keywords TEXT,
                start_date TEXT,
                duration TEXT,
                deadline TEXT,
                url TEXT,
                description TEXT,
                supervisor TEXT,
                funding TEXT,
                posted_date TEXT,
                scraped_at TEXT,
                is_new INTEGER DEFAULT 1,
                notified INTEGER DEFAULT 0
            )
        """)
        
        # Internship offers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS internship_offers (
                id TEXT PRIMARY KEY,
                hash_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                company TEXT,
                location TEXT,
                domain TEXT,
                keywords TEXT,
                duration TEXT,
                level TEXT,
                start_date TEXT,
                deadline TEXT,
                url TEXT,
                description TEXT,
                compensation TEXT,
                posted_date TEXT,
                scraped_at TEXT,
                is_new INTEGER DEFAULT 1,
                notified INTEGER DEFAULT 0
            )
        """)
        
        # Scraping log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scraping_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scrape_date TEXT NOT NULL,
                offer_type TEXT NOT NULL,
                total_found INTEGER,
                new_offers INTEGER,
                duration_seconds REAL,
                status TEXT,
                error_message TEXT
            )
        """)
        
        # User preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT
            )
        """)
        
        self.conn.commit()
        logger.info("✅ Database initialized")
    
    def insert_housing_offers(self, offers: List[Dict]) -> int:
        """Insert housing offers, return count of new offers"""
        cursor = self.conn.cursor()
        new_count = 0
        
        for offer in offers:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO housing_offers 
                    (id, hash_id, title, location, price, type, surface, 
                     available_date, url, description, distance_to_uni, 
                     posted_date, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    offer['id'],
                    offer.get('hash_id', offer['id']),
                    offer['title'],
                    offer.get('location'),
                    offer.get('price'),
                    offer.get('type'),
                    offer.get('surface'),
                    offer.get('available_date'),
                    offer['url'],
                    offer.get('description'),
                    offer.get('distance_to_uni'),
                    offer.get('posted_date'),
                    datetime.now().isoformat()
                ))
                
                if cursor.rowcount > 0:
                    new_count += 1
                    
            except sqlite3.IntegrityError:
                continue
        
        self.conn.commit()
        logger.info(f"💾 Inserted {new_count} new housing offers")
        return new_count
    
    def insert_phd_offers(self, offers: List[Dict]) -> int:
        """Insert PhD offers, return count of new offers"""
        cursor = self.conn.cursor()
        new_count = 0
        
        for offer in offers:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO phd_offers 
                    (id, hash_id, title, institution, laboratory, location, 
                     domain, keywords, start_date, duration, deadline, url, 
                     description, supervisor, funding, posted_date, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    offer['id'],
                    offer.get('hash_id', offer['id']),
                    offer['title'],
                    offer.get('institution'),
                    offer.get('laboratory'),
                    offer.get('location'),
                    offer.get('domain'),
                    json.dumps(offer.get('keywords', [])),
                    offer.get('start_date'),
                    offer.get('duration'),
                    offer.get('deadline'),
                    offer['url'],
                    offer.get('description'),
                    offer.get('supervisor'),
                    offer.get('funding'),
                    offer.get('posted_date'),
                    datetime.now().isoformat()
                ))
                
                if cursor.rowcount > 0:
                    new_count += 1
                    
            except sqlite3.IntegrityError:
                continue
        
        self.conn.commit()
        logger.info(f"💾 Inserted {new_count} new PhD offers")
        return new_count
    
    def insert_internship_offers(self, offers: List[Dict]) -> int:
        """Insert internship offers, return count of new offers"""
        cursor = self.conn.cursor()
        new_count = 0
        
        for offer in offers:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO internship_offers 
                    (id, hash_id, title, company, location, domain, keywords, 
                     duration, level, start_date, deadline, url, description, 
                     compensation, posted_date, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    offer['id'],
                    offer.get('hash_id', offer['id']),
                    offer['title'],
                    offer.get('company'),
                    offer.get('location'),
                    offer.get('domain'),
                    json.dumps(offer.get('keywords', [])),
                    offer.get('duration'),
                    offer.get('level'),
                    offer.get('start_date'),
                    offer.get('deadline'),
                    offer['url'],
                    offer.get('description'),
                    offer.get('compensation'),
                    offer.get('posted_date'),
                    datetime.now().isoformat()
                ))
                
                if cursor.rowcount > 0:
                    new_count += 1
                    
            except sqlite3.IntegrityError:
                continue
        
        self.conn.commit()
        logger.info(f"💾 Inserted {new_count} new internship offers")
        return new_count
    
    def get_new_housing_offers(self) -> List[Dict]:
        """Get housing offers not yet notified"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM housing_offers 
            WHERE notified = 0 
            ORDER BY scraped_at DESC
        """)
        
        offers = [dict(row) for row in cursor.fetchall()]
        logger.info(f"📬 Found {len(offers)} new housing offers to notify")
        return offers
    
    def get_new_phd_offers(self) -> List[Dict]:
        """Get PhD offers not yet notified"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM phd_offers 
            WHERE notified = 0 
            ORDER BY scraped_at DESC
        """)
        
        offers = [dict(row) for row in cursor.fetchall()]
        
        # Parse keywords JSON
        for offer in offers:
            if offer.get('keywords'):
                offer['keywords'] = json.loads(offer['keywords'])
        
        logger.info(f"📬 Found {len(offers)} new PhD offers to notify")
        return offers
    
    def get_new_internship_offers(self) -> List[Dict]:
        """Get internship offers not yet notified"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM internship_offers 
            WHERE notified = 0 
            ORDER BY scraped_at DESC
        """)
        
        offers = [dict(row) for row in cursor.fetchall()]
        
        # Parse keywords JSON
        for offer in offers:
            if offer.get('keywords'):
                offer['keywords'] = json.loads(offer['keywords'])
        
        logger.info(f"📬 Found {len(offers)} new internship offers to notify")
        return offers
    
    def mark_as_notified(self, offer_type: str, offer_ids: List[str]):
        """Mark offers as notified"""
        cursor = self.conn.cursor()
        
        table_map = {
            'housing': 'housing_offers',
            'phd': 'phd_offers',
            'internship': 'internship_offers'
        }
        
        table = table_map.get(offer_type)
        if not table:
            return
        
        placeholders = ','.join('?' * len(offer_ids))
        cursor.execute(f"""
            UPDATE {table} 
            SET notified = 1 
            WHERE id IN ({placeholders})
        """, offer_ids)
        
        self.conn.commit()
        logger.info(f"✉️ Marked {len(offer_ids)} {offer_type} offers as notified")
    
    def log_scraping_run(self, offer_type: str, total_found: int, 
                         new_offers: int, duration: float, 
                         status: str = "success", error: str = None):
        """Log scraping run statistics"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO scraping_log 
            (scrape_date, offer_type, total_found, new_offers, 
             duration_seconds, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            offer_type,
            total_found,
            new_offers,
            duration,
            status,
            error
        ))
        self.conn.commit()
    
    def get_statistics(self) -> Dict:
        """Get overall statistics"""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Total offers
        cursor.execute("SELECT COUNT(*) as count FROM housing_offers")
        stats['total_housing'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM phd_offers")
        stats['total_phd'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM internship_offers")
        stats['total_internship'] = cursor.fetchone()['count']
        
        # New offers pending notification
        cursor.execute("SELECT COUNT(*) as count FROM housing_offers WHERE notified = 0")
        stats['pending_housing'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM phd_offers WHERE notified = 0")
        stats['pending_phd'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM internship_offers WHERE notified = 0")
        stats['pending_internship'] = cursor.fetchone()['count']
        
        # Last scrape time
        cursor.execute("""
            SELECT scrape_date, offer_type, new_offers 
            FROM scraping_log 
            ORDER BY id DESC 
            LIMIT 3
        """)
        stats['recent_scrapes'] = [dict(row) for row in cursor.fetchall()]
        
        return stats
    
    def cleanup_old_offers(self, days: int = 90):
        """Remove offers older than specified days"""
        cursor = self.conn.cursor()
        cutoff_date = datetime.now().timestamp() - (days * 24 * 3600)
        
        for table in ['housing_offers', 'phd_offers', 'internship_offers']:
            cursor.execute(f"""
                DELETE FROM {table} 
                WHERE strftime('%s', scraped_at) < ?
            """, (cutoff_date,))
        
        deleted = cursor.rowcount
        self.conn.commit()
        logger.info(f"🧹 Cleaned up {deleted} old offers")
        return deleted
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


# Example usage
if __name__ == "__main__":
    db = DatabaseManager()
    
    # Get statistics
    stats = db.get_statistics()
    print("\n📊 Database Statistics:")
    print(f"   Housing offers: {stats['total_housing']} (Pending: {stats['pending_housing']})")
    print(f"   PhD offers: {stats['total_phd']} (Pending: {stats['pending_phd']})")
    print(f"   Internship offers: {stats['total_internship']} (Pending: {stats['pending_internship']})")
    
    db.close()
