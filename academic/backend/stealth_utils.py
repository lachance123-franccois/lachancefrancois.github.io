"""
Stealth Utilities - Rotation d'user-agents, délais aléatoires, cache intelligent
"""

import random
import time
import hashlib
import json
import os
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)

# Liste étendue d'user-agents réalistes
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
]

# Accept-Language réalistes
ACCEPT_LANGUAGES = [
    'fr-FR,fr;q=0.9,en;q=0.8',
    'fr,en;q=0.9,de;q=0.8',
    'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
]


class StealthSession:
    """Session HTTP avec rotation d'identifiants"""
    
    def __init__(self, use_cache: bool = True, cache_dir: str = ".cache"):
        self.session = None
        self.use_cache = use_cache
        self.cache_dir = cache_dir
        self._last_request_time = 0
        self._init_session()
        
        if use_cache:
            os.makedirs(cache_dir, exist_ok=True)
    
    def _init_session(self):
        """Initialise une nouvelle session avec user-agent aléatoire"""
        import requests
        self.session = requests.Session()
        self._rotate_headers()
    
    def _rotate_headers(self):
        """Change les headers aléatoirement"""
        user_agent = random.choice(USER_AGENTS)
        accept_lang = random.choice(ACCEPT_LANGUAGES)
        
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept-Language': accept_lang,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })
    
    def _random_delay(self, min_sec: float = 2, max_sec: float = 8):
        """Attente aléatoire entre requêtes"""
        elapsed = time.time() - self._last_request_time
        delay = random.uniform(min_sec, max_sec)
        
        if elapsed < delay:
            time.sleep(delay - elapsed)
        
        self._last_request_time = time.time()
    
    def _get_cache_key(self, url: str, params: dict = None) -> str:
        """Génère une clé de cache unique"""
        content = url + json.dumps(params or {}, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cached_response(self, key: str, ttl_hours: int = 24) -> Optional[str]:
        """Récupère une réponse en cache si valide"""
        if not self.use_cache:
            return None
        
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            cached_time = datetime.fromisoformat(data['timestamp'])
            if datetime.now() - cached_time < timedelta(hours=ttl_hours):
                logger.debug(f"Cache hit: {key[:16]}...")
                return data['content']
        
        return None
    
    def _save_to_cache(self, key: str, content: str):
        """Sauvegarde une réponse en cache"""
        if not self.use_cache:
            return
        
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        
        with open(cache_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'content': content
            }, f)
    
    def get(self, url: str, params: dict = None, ttl_hours: int = 24, 
            force_refresh: bool = False, **kwargs) -> Any:
        """
        Requête GET avec cache et délai aléatoire
        
        Args:
            url: URL à requêter
            params: Paramètres de requête
            ttl_hours: Durée de validité du cache
            force_refresh: Ignorer le cache
        """
        cache_key = self._get_cache_key(url, params)
        
        # Vérifier le cache
        if not force_refresh:
            cached = self._get_cached_response(cache_key, ttl_hours)
            if cached:
                import json as json_module
                try:
                    return json_module.loads(cached)
                except:
                    return cached
        
        # Attente aléatoire avant requête
        self._random_delay()
        
        # Rotation périodique des headers
        if random.random() < 0.1:  # 10% de chance de rotation
            self._rotate_headers()
        
        # Exécuter la requête
        response = self.session.get(url, params=params, timeout=15, **kwargs)
        response.raise_for_status()
        
        # Sauvegarder en cache
        content = response.text
        self._save_to_cache(cache_key, content)
        
        # Tenter de parser JSON si applicable
        if response.headers.get('Content-Type', '').startswith('application/json'):
            return response.json()
        
        return content
    
    def post(self, url: str, data: dict = None, **kwargs):
        """Requête POST avec délai aléatoire"""
        self._random_delay()
        
        if random.random() < 0.1:
            self._rotate_headers()
        
        response = self.session.post(url, data=data, timeout=15, **kwargs)
        response.raise_for_status()
        
        return response


def rate_limited(min_delay: float = 2, max_delay: float = 8):
    """Décorateur pour限 rate limiting"""
    last_call = 0
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal last_call
            elapsed = time.time() - last_call
            delay = random.uniform(min_delay, max_delay)
            
            if elapsed < delay:
                time.sleep(delay - elapsed)
            
            last_call = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator