"""
Email Notification System with Premium HTML Templates
Sends beautiful daily digest emails with new offers
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
from typing import List, Dict
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailNotifier:
    """
    Premium email notification system with custom templates
    """
    
    def __init__(self, smtp_server: str, smtp_port: int, 
                 email: str, password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.password = password
    
    def send_daily_digest(self, recipient: str, 
                     housing_offers: List[Dict],
                     phd_offers: List[Dict],
                        internship_offers: List[Dict]) -> bool:
        """
        Send daily digest with all new offers
        """
        total_offers = len(housing_offers) + len(phd_offers) + len(internship_offers)
        
        if total_offers == 0:
            logger.info("No new offers to send")
            return True
        
        logger.info(f"📧 Preparing email with {total_offers} new offers")
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🎯 {total_offers} Nouvelles Opportunités - {datetime.now().strftime('%d/%m/%Y')}"
        msg['From'] = self.email
        msg['To'] = recipient
        
        # ✅ Corrected: pass recipient as argument
        html_content = self._generate_html_digest(
            recipient, housing_offers, phd_offers, internship_offers
        )
        
        # Attach HTML
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Send email
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            logger.info(f"✅ Email sent successfully to {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            return False

    
    def _generate_html_digest(self, recipient: str,
                             housing_offers: List[Dict],
                             phd_offers: List[Dict],
                             internship_offers: List[Dict]) -> str:
        """
        Generate premium HTML email template with futuristic design
        """
        
        # Count totals
        total_housing = len(housing_offers)
        total_phd = len(phd_offers)
        total_internship = len(internship_offers)
        total = total_housing + total_phd + total_internship
        
        # Generate offer sections
        housing_html = self._generate_housing_section(housing_offers)
        phd_html = self._generate_phd_section(phd_offers)
        internship_html = self._generate_internship_section(internship_offers)
        
        html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Francois Tracker - Daily Digest</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Space+Grotesk:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
            color: #e0e0e0;
            line-height: 1.6;
            padding: 20px;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: #16162a;
            border: 1px solid #2d2d44;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(0, 255, 157, 0.1);
        }}
        
        .header {{
            background: linear-gradient(135deg, #00ff9d 0%, #00b8ff 100%);
            padding: 40px 30px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: rotate 20s linear infinite;
        }}
        
        @keyframes rotate {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}
        
        .header h1 {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 32px;
            font-weight: 700;
            color: #0a0a0a;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 2px;
            position: relative;
            z-index: 1;
        }}
        
        .header .date {{
            font-size: 14px;
            color: #0a0a0a;
            font-weight: 600;
            opacity: 0.8;
            position: relative;
            z-index: 1;
        }}
        
        .stats {{
            display: flex;
            justify-content: space-around;
            padding: 30px;
            background: #1a1a2e;
            border-bottom: 1px solid #2d2d44;
        }}
        
        .stat-card {{
            text-align: center;
            flex: 1;
            padding: 15px;
            border-right: 1px solid #2d2d44;
        }}
        
        .stat-card:last-child {{
            border-right: none;
        }}
        
        .stat-number {{
            font-size: 36px;
            font-weight: 700;
            color: #00ff9d;
            font-family: 'JetBrains Mono', monospace;
            text-shadow: 0 0 20px rgba(0, 255, 157, 0.5);
        }}
        
        .stat-label {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #888;
            margin-top: 5px;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section-header {{
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #00ff9d;
        }}
        
        .section-icon {{
            font-size: 24px;
            margin-right: 12px;
        }}
        
        .section-title {{
            font-size: 20px;
            font-weight: 700;
            color: #00ff9d;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .offer-card {{
            background: #1e1e38;
            border: 1px solid #2d2d44;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .offer-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(180deg, #00ff9d 0%, #00b8ff 100%);
        }}
        
        .offer-card:hover {{
            transform: translateX(5px);
            border-color: #00ff9d;
            box-shadow: 0 10px 30px rgba(0, 255, 157, 0.2);
        }}
        
        .offer-title {{
            font-size: 18px;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 10px;
            padding-left: 15px;
        }}
        
        .offer-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-bottom: 12px;
            padding-left: 15px;
            font-size: 14px;
        }}
        
        .meta-item {{
            display: flex;
            align-items: center;
            color: #b0b0b0;
        }}
        
        .meta-icon {{
            margin-right: 6px;
        }}
        
        .offer-description {{
            color: #888;
            font-size: 14px;
            line-height: 1.6;
            margin-bottom: 15px;
            padding-left: 15px;
        }}
        
        .offer-keywords {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 15px;
            padding-left: 15px;
        }}
        
        .keyword {{
            background: rgba(0, 255, 157, 0.1);
            color: #00ff9d;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            border: 1px solid rgba(0, 255, 157, 0.3);
        }}
        
        .offer-link {{
            display: inline-block;
            background: linear-gradient(135deg, #00ff9d 0%, #00b8ff 100%);
            color: #0a0a0a;
            padding: 10px 20px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 600;
            font-size: 14px;
            margin-left: 15px;
            transition: all 0.3s ease;
        }}
        
        .offer-link:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 255, 157, 0.4);
        }}
        
        .footer {{
            background: #0f0f1e;
            padding: 30px;
            text-align: center;
            border-top: 1px solid #2d2d44;
        }}
        
        .footer-text {{
            color: #666;
            font-size: 13px;
            line-height: 1.8;
        }}
        
        .footer-link {{
            color: #00ff9d;
            text-decoration: none;
        }}
        
        .empty-section {{
            text-align: center;
            padding: 30px;
            color: #666;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Francois Tracker</h1>
            <div class="date">{datetime.now().strftime('%A %d %B %Y')}</div>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{total_housing}</div>
                <div class="stat-label">Logements</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_phd}</div>
                <div class="stat-label">Thèses</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_internship}</div>
                <div class="stat-label">Stages</div>
            </div>
        </div>
        
        <div class="content">
            {housing_html}
            {phd_html}
            {internship_html}
        </div>
        
        <div class="footer">
            <div class="footer-text">
                <strong>Academic Tracker</strong> - Votre veille académique automatisée<br>
                Système de tracking intelligent pour Toulouse<br>
                <a href="https://francois-tracker.fr/preferences?email={recipient}" class="footer-link">Gérer mes préférences</a> • 
                <a href="https://francois-tracker.fr/unsubscribe?email={recipient}" class="footer-link">Se désabonner</a>
            </div>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def _generate_housing_section(self, offers: List[Dict]) -> str:
        """Generate housing offers section"""
        if not offers:
            return """
            <div class="section">
                <div class="section-header">
                    <span class="section-icon">🏠</span>
                    <h2 class="section-title">Logements CROUS</h2>
                </div>
                <div class="empty-section">Aucun nouveau logement aujourd'hui</div>
            </div>
            """
        
        offers_html = ""
        for offer in offers:
            offers_html += f"""
            <div class="offer-card">
                <h3 class="offer-title">{offer['title']}</h3>
                <div class="offer-meta">
                    <span class="meta-item">
                        <span class="meta-icon">📍</span>
                        {offer.get('location', 'Toulouse')}
                    </span>
                    <span class="meta-item">
                        <span class="meta-icon">💰</span>
                        {offer.get('price', 'N/A')}€/mois
                    </span>
                    <span class="meta-item">
                        <span class="meta-icon">📐</span>
                        {offer.get('surface', 'N/A')}
                    </span>
                </div>
                <p class="offer-description">
                    {offer.get('description', 'Aucune description disponible')[:200]}...
                </p>
                <a href="{offer['url']}" class="offer-link">Voir l'offre →</a>
            </div>
            """
        
        return f"""
        <div class="section">
            <div class="section-header">
                <span class="section-icon">🏠</span>
                <h2 class="section-title">Logements CROUS</h2>
            </div>
            {offers_html}
        </div>
        """
    
    def _generate_phd_section(self, offers: List[Dict]) -> str:
        """Generate PhD offers section"""
        if not offers:
            return """
            <div class="section">
                <div class="section-header">
                    <span class="section-icon">🎓</span>
                    <h2 class="section-title">Thèses de Doctorat</h2>
                </div>
                <div class="empty-section">Aucune nouvelle thèse aujourd'hui</div>
            </div>
            """
        
        offers_html = ""
        for offer in offers:
            keywords = offer.get('keywords', [])
            if isinstance(keywords, str):
                import json
                try:
                    keywords = json.loads(keywords)
                except:
                    keywords = []
            
            keywords_html = "".join([
                f'<span class="keyword">{kw}</span>' 
                for kw in keywords[:6]
            ])
            
            offers_html += f"""
            <div class="offer-card">
                <h3 class="offer-title">{offer['title']}</h3>
                <div class="offer-meta">
                    <span class="meta-item">
                        <span class="meta-icon">🏛️</span>
                        {offer.get('institution', 'N/A')}
                    </span>
                    <span class="meta-item">
                        <span class="meta-icon">🔬</span>
                        {offer.get('laboratory', 'N/A')}
                    </span>
                    <span class="meta-item">
                        <span class="meta-icon">⏱️</span>
                        {offer.get('duration', '3 ans')}
                    </span>
                </div>
                <p class="offer-description">
                    {offer.get('description', 'Aucune description disponible')[:250]}...
                </p>
                <div class="offer-keywords">
                    {keywords_html}
                </div>
                <a href="{offer['url']}" class="offer-link">Voir l'offre →</a>
            </div>
            """
        
        return f"""
        <div class="section">
            <div class="section-header">
                <span class="section-icon">🎓</span>
                <h2 class="section-title">Thèses de Doctorat</h2>
            </div>
            {offers_html}
        </div>
        """
    
    def _generate_internship_section(self, offers: List[Dict]) -> str:
        """Generate internship offers section"""
        if not offers:
            return """
            <div class="section">
                <div class="section-header">
                    <span class="section-icon">💼</span>
                    <h2 class="section-title">Stages</h2>
                </div>
                <div class="empty-section">Aucun nouveau stage aujourd'hui</div>
            </div>
            """
        
        offers_html = ""
        for offer in offers:
            keywords = offer.get('keywords', [])
            if isinstance(keywords, str):
                import json
                try:
                    keywords = json.loads(keywords)
                except:
                    keywords = []
            
            keywords_html = "".join([
                f'<span class="keyword">{kw}</span>' 
                for kw in keywords[:6]
            ])
            
            offers_html += f"""
            <div class="offer-card">
                <h3 class="offer-title">{offer['title']}</h3>
                <div class="offer-meta">
                    <span class="meta-item">
                        <span class="meta-icon">🏢</span>
                        {offer.get('company', 'N/A')}
                    </span>
                    <span class="meta-item">
                        <span class="meta-icon">📍</span>
                        {offer.get('location', 'Toulouse')}
                    </span>
                    <span class="meta-item">
                        <span class="meta-icon">⏱️</span>
                        {offer.get('duration', 'N/A')}
                    </span>
                    <span class="meta-item">
                        <span class="meta-icon">🎓</span>
                        {offer.get('level', 'M2')}
                    </span>
                </div>
                <p class="offer-description">
                    {offer.get('description', 'Aucune description disponible')[:250]}...
                </p>
                <div class="offer-keywords">
                    {keywords_html}
                </div>
                <a href="{offer['url']}" class="offer-link">Voir l'offre →</a>
            </div>
            """
        
        return f"""
        <div class="section">
            <div class="section-header">
                <span class="section-icon">💼</span>
                <h2 class="section-title">Stages</h2>
            </div>
            {offers_html}
        </div>
        """


# Example usage
if __name__ == "__main__":
    # Configuration (use environment variables in production)
    notifier = EmailNotifier(
        smtp_server="smtp.icloud.com",
        smtp_port=587,
        email="lachanceawounang@icloud.com",
        password="qktu-rusa-hqjt-wzim"

    )
    
    # Test data
    test_housing = [{
        'title': 'Studio 10m² - Rangueil',
        'location': 'Toulouse Rangueil',
        'price': 350,
        'surface': '10m²',
        'description': 'Studio meublé proche université',
        'url': 'https://www.lokaviz.fr'
    }]
    
    # Send test email
    # notifier.send_daily_digest("lachanceawounang@icloud.com", test_housing, [], [])
