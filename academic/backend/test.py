#!/usr/bin/env python3
"""
Quick Test Script - Academic Tracker
Tests all components without sending emails
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from crous_scraper import CROUSScraper
from phd_scraper import PhDScraper
from internship_scraper import InternshipScraper
from database import DatabaseManager

def test_scrapers():
    """Test all scrapers"""
    print("\n" + "=" * 60)
    print("🧪 TESTING ACADEMIC TRACKER")
    print("=" * 60)
    
    # Test CROUS scraper
    print("\n🏠 Testing CROUS Scraper...")
    try:
        crous = CROUSScraper()
        housing = crous.search_toulouse_housing(max_price=500)
        print(f"   ✅ Found {len(housing)} housing offers")
        if housing:
            print(f"   📍 Example: {housing[0].title} - {housing[0].price}€")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test PhD scraper
    print("\n🎓 Testing PhD Scraper...")
    try:
        phd = PhDScraper()
        offers = phd.scrape_all_sources()
        print(f"   ✅ Found {len(offers)} PhD offers")
        if offers:
            print(f"   📍 Example: {offers[0].title}")
            print(f"      🏛️  {offers[0].institution}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test Internship scraper
    print("\n💼 Testing Internship Scraper...")
    try:
        internship = InternshipScraper()
        offers = internship.scrape_all_sources()
        print(f"   ✅ Found {len(offers)} internship offers")
        if offers:
            print(f"   📍 Example: {offers[0].title}")
            print(f"      🏢 {offers[0].company}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test Database
    print("\n💾 Testing Database...")
    try:
        db = DatabaseManager("test_tracker.db")
        stats = db.get_statistics()
        print(f"   ✅ Database initialized")
        print(f"   📊 Stats: {stats['total_housing']} housing, "
              f"{stats['total_phd']} PhD, {stats['total_internship']} internships")
        db.close()
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Testing complete!")
    print("=" * 60)
    print("\n💡 Next steps:")
    print("   1. Configure your email settings in config/config.json")
    print("   2. Add GitHub Secrets for automation")
    print("   3. Run: python backend/main.py")
    print()

if __name__ == "__main__":
    test_scrapers()
