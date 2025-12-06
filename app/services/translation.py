"""
Translation client for Travliaq-Translate service.
Translates POI names to English for better Wikidata matching.
Focuses on French → English translation with robust detection.
"""
from __future__ import annotations
from typing import Optional, Tuple
import httpx
import re


class TranslationClient:
    """Client for Travliaq-Translate service with French/English detection."""
    
    # Common English words for POI names
    ENGLISH_WORDS = {
        'the', 'of', 'in', 'at', 'on', 'for', 'and', 'or', 'with', 'to', 'from', 'by',
        'tower', 'castle', 'church', 'museum', 'palace', 'park', 'square', 'bridge',
        'station', 'street', 'avenue', 'road', 'lane', 'place', 'garden', 'hall',
        'cathedral', 'abbey', 'monument', 'memorial', 'gallery', 'theatre', 'theater',
        'library', 'university', 'college', 'school', 'hospital', 'hotel', 'restaurant',
        'market', 'plaza', 'center', 'centre', 'building', 'house', 'mansion', 'villa',
        'beach', 'bay', 'lake', 'river', 'mountain', 'hill', 'valley', 'forest',
        'national', 'royal', 'grand', 'old', 'new', 'great', 'big', 'little', 'saint',
        'north', 'south', 'east', 'west', 'upper', 'lower', 'central',
        'falls', 'springs', 'heights', 'point', 'island', 'islands',
    }
    
    # French indicator words
    FRENCH_WORDS = {
        'de', 'la', 'le', 'les', 'du', 'des', 'aux', 'sur', 'sous', 'dans', 'par',
        'château', 'église', 'cathédrale', 'musée', 'jardin', 'rue', 'pont',
        'tour', 'palais', 'abbaye', 'plage', 'lac', 'montagne', 'forêt',
        'notre', 'dame', 'sainte', 'grande', 'petit', 'petite', 'vieux', 'vieille',
        'arc', 'triomphe', 'sacré', 'coeur', 'cœur', 'basilique', 'quartier',
        'champs', 'élysées', 'louvre', 'versailles', 'invalides', 'opéra',
        'gare', 'hôtel', 'ville', 'mairie', 'bibliothèque', 'théâtre',
    }
    
    # French diacritics
    FRENCH_DIACRITICS = set('àâäéèêëïîôùûüçœæ')
    
    def __init__(self, base_url: str, http_client: httpx.AsyncClient):
        self.base_url = base_url.rstrip("/")
        self.http = http_client or httpx.AsyncClient()
    
    def _has_french_diacritics(self, text: str) -> bool:
        """Check if text contains French diacritical marks."""
        return any(c.lower() in self.FRENCH_DIACRITICS for c in text)
    
    def _count_indicators(self, text: str) -> Tuple[int, int]:
        """Count English vs French indicator words."""
        words = re.findall(r'\b\w+\b', text.lower())
        english_count = sum(1 for w in words if w in self.ENGLISH_WORDS)
        french_count = sum(1 for w in words if w in self.FRENCH_WORDS)
        return english_count, french_count
    
    def is_french(self, text: str) -> bool:
        """
        Detect if text is likely French.
        Returns True if French, False if English or unknown.
        """
        if not text or len(text.strip()) == 0:
            return False
        
        # Check for French diacritics (strong indicator)
        if self._has_french_diacritics(text):
            return True
        
        # Count indicator words
        english_count, french_count = self._count_indicators(text)
        
        # If more French words than English
        if french_count > english_count:
            return True
        
        # If equal but has French articles (le, la, les, du, des)
        words = text.lower().split()
        french_articles = {'le', 'la', 'les', 'du', 'des', 'de'}
        if french_count == english_count and any(w in french_articles for w in words):
            return True
        
        return False
    
    async def translate_to_english(self, text: str) -> str:
        """
        Translate French text to English.
        If already English, returns as-is.
        
        Args:
            text: Text to translate (POI name, city name, etc.)
            
        Returns:
            English version of the text
        """
        if not text or len(text.strip()) == 0:
            return text
        
        # If not French, return as-is
        if not self.is_french(text):
            return text
        
        # Translate French → English
        try:
            response = await self.http.post(
                f"{self.base_url}/translate",
                json={
                    "text": text,
                    "source_language": "FR",
                    "target_language": "EN",
                },
                headers={"Content-Type": "application/json"},
                timeout=5.0,
            )
            
            if response.status_code == 200:
                data = response.json()
                translated = data.get("translated_text") or data.get("text")
                if translated and translated.strip() and translated != text:
                    return translated
        except Exception:
            pass
        
        return text
    
    async def translate_poi_name(self, poi_name: str, city: str) -> Tuple[str, str]:
        """Translate both POI name and city to English."""
        translated_poi = await self.translate_to_english(poi_name)
        translated_city = await self.translate_to_english(city)
        return translated_poi, translated_city
