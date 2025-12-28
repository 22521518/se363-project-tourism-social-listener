"""
Gazetteer-based Location Extractor.

Uses a pre-defined list of locations for rule-based matching.
This is the first fallback when LLM extraction fails.
"""

import re
import logging
from typing import Any, Dict, List, Set, Tuple

from .base import LocationExtractor

logger = logging.getLogger(__name__)


# Common countries (focused on Southeast Asia and popular tourist destinations)
COUNTRIES: Dict[str, Set[str]] = {
    "Vietnam": {"vietnam", "việt nam", "viet nam", "vn"},
    "Thailand": {"thailand", "thái lan", "thai lan", "th"},
    "Singapore": {"singapore", "sing", "sg"},
    "Malaysia": {"malaysia", "mã lai", "ma lai", "my"},
    "Indonesia": {"indonesia", "indo"},
    "Philippines": {"philippines", "phi líp pin", "ph"},
    "Japan": {"japan", "nhật bản", "nhat ban", "jp"},
    "South Korea": {"south korea", "korea", "hàn quốc", "han quoc", "kr"},
    "China": {"china", "trung quốc", "trung quoc", "cn"},
    "Taiwan": {"taiwan", "đài loan", "dai loan"},
    "Hong Kong": {"hong kong", "hồng kông"},
    "United States": {"united states", "usa", "us", "america", "mỹ", "my"},
    "United Kingdom": {"united kingdom", "uk", "england", "britain", "anh"},
    "France": {"france", "pháp", "phap"},
    "Germany": {"germany", "đức", "duc"},
    "Australia": {"australia", "úc", "uc"},
    "Canada": {"canada"},
    "India": {"india", "ấn độ", "an do"},
    "Cambodia": {"cambodia", "campuchia", "cam pu chia"},
    "Laos": {"laos", "lào"},
    "Myanmar": {"myanmar", "burma", "miến điện", "mien dien"},
}

# Major cities (focused on Vietnam and popular tourist destinations)
CITIES: Dict[str, Tuple[Set[str], str]] = {
    # Vietnam cities
    "Ho Chi Minh City": ({"ho chi minh", "hcm", "saigon", "sài gòn", "sai gon", "tp.hcm", "tphcm"}, "Vietnam"),
    "Hanoi": ({"hanoi", "hà nội", "ha noi"}, "Vietnam"),
    "Da Nang": ({"da nang", "đà nẵng", "da nang"}, "Vietnam"),
    "Nha Trang": ({"nha trang"}, "Vietnam"),
    "Hoi An": ({"hoi an", "hội an"}, "Vietnam"),
    "Hue": ({"hue", "huế"}, "Vietnam"),
    "Phu Quoc": ({"phu quoc", "phú quốc"}, "Vietnam"),
    "Dalat": ({"dalat", "đà lạt", "da lat"}, "Vietnam"),
    "Vung Tau": ({"vung tau", "vũng tàu"}, "Vietnam"),
    "Can Tho": ({"can tho", "cần thơ"}, "Vietnam"),
    "Hai Phong": ({"hai phong", "hải phòng"}, "Vietnam"),
    "Quy Nhon": ({"quy nhon", "quy nhơn"}, "Vietnam"),
    "Mui Ne": ({"mui ne", "mũi né"}, "Vietnam"),
    "Sapa": ({"sapa", "sa pa"}, "Vietnam"),
    "Ha Long": ({"ha long", "hạ long"}, "Vietnam"),
    # Thailand cities
    "Bangkok": ({"bangkok", "krung thep"}, "Thailand"),
    "Phuket": ({"phuket"}, "Thailand"),
    "Chiang Mai": ({"chiang mai"}, "Thailand"),
    "Pattaya": ({"pattaya"}, "Thailand"),
    # Singapore (city-state)
    "Singapore": ({"singapore", "sg"}, "Singapore"),
    # Malaysia cities
    "Kuala Lumpur": ({"kuala lumpur", "kl"}, "Malaysia"),
    "Penang": ({"penang"}, "Malaysia"),
    # Indonesia cities
    "Bali": ({"bali"}, "Indonesia"),
    "Jakarta": ({"jakarta"}, "Indonesia"),
    # Japan cities
    "Tokyo": ({"tokyo"}, "Japan"),
    "Osaka": ({"osaka"}, "Japan"),
    "Kyoto": ({"kyoto"}, "Japan"),
    # Other major cities
    "Seoul": ({"seoul"}, "South Korea"),
    "Beijing": ({"beijing", "peking"}, "China"),
    "Shanghai": ({"shanghai"}, "China"),
    "Hong Kong": ({"hong kong"}, "Hong Kong"),
    "Taipei": ({"taipei"}, "Taiwan"),
    "Paris": ({"paris"}, "France"),
    "London": ({"london"}, "United Kingdom"),
    "New York": ({"new york", "nyc"}, "United States"),
    "Los Angeles": ({"los angeles", "la"}, "United States"),
    "Sydney": ({"sydney"}, "Australia"),
}

# Famous landmarks
LANDMARKS: Dict[str, Tuple[Set[str], str]] = {
    # Vietnam landmarks
    "Ha Long Bay": ({"ha long bay", "vịnh hạ long", "vinh ha long"}, "Vietnam"),
    "Cu Chi Tunnels": ({"cu chi", "củ chi", "địa đạo củ chi"}, "Vietnam"),
    "Mekong Delta": ({"mekong delta", "đồng bằng sông cửu long"}, "Vietnam"),
    "Ben Thanh Market": ({"ben thanh", "bến thành"}, "Vietnam"),
    "Notre Dame Cathedral Saigon": ({"notre dame", "nhà thờ đức bà"}, "Vietnam"),
    "Golden Bridge": ({"golden bridge", "cầu vàng"}, "Vietnam"),
    "Ba Na Hills": ({"ba na", "bà nà"}, "Vietnam"),
    # Thailand landmarks
    "Grand Palace": ({"grand palace", "hoàng cung"}, "Thailand"),
    "Wat Pho": ({"wat pho"}, "Thailand"),
    # Other landmarks
    "Eiffel Tower": ({"eiffel tower", "tháp eiffel"}, "France"),
    "Great Wall": ({"great wall", "vạn lý trường thành"}, "China"),
    "Mount Fuji": ({"mount fuji", "fuji", "núi phú sĩ"}, "Japan"),
    "Angkor Wat": ({"angkor wat"}, "Cambodia"),
}


class GazetteerLocationExtractor(LocationExtractor):
    """
    Gazetteer-based location extractor using predefined location lists.
    
    This is the first fallback when LLM extraction fails.
    Uses simple string matching against known locations.
    """
    
    def __init__(self):
        """Initialize the gazetteer extractor."""
        self._countries = COUNTRIES
        self._cities = CITIES
        self._landmarks = LANDMARKS
    
    @property
    def name(self) -> str:
        return "gazetteer"
    
    def extract(self, text: str) -> Dict[str, Any]:
        """
        Extract locations using gazetteer matching.
        
        Args:
            text: Input text to extract locations from.
            
        Returns:
            Extraction result dictionary.
        """
        if not text or not text.strip():
            return self._empty_result()
        
        text_lower = text.lower()
        locations: List[Dict[str, Any]] = []
        seen_names: Set[str] = set()
        
        # Search for landmarks (most specific first)
        for name, (aliases, country) in self._landmarks.items():
            if self._find_match(text_lower, aliases):
                if name not in seen_names:
                    locations.append({
                        "name": name,
                        "type": "landmark",
                        "confidence": 0.85
                    })
                    seen_names.add(name)
        
        # Search for cities
        for name, (aliases, country) in self._cities.items():
            if self._find_match(text_lower, aliases):
                if name not in seen_names:
                    locations.append({
                        "name": name,
                        "type": "city",
                        "confidence": 0.80
                    })
                    seen_names.add(name)
        
        # Search for countries
        for name, aliases in self._countries.items():
            if self._find_match(text_lower, aliases):
                if name not in seen_names:
                    locations.append({
                        "name": name,
                        "type": "country",
                        "confidence": 0.75
                    })
                    seen_names.add(name)
        
        # Determine primary location (highest confidence)
        primary_location = None
        if locations:
            locations.sort(key=lambda x: x["confidence"], reverse=True)
            primary_location = {
                "name": locations[0]["name"],
                "confidence": locations[0]["confidence"]
            }
        
        # Calculate overall score
        overall_score = 0.0
        if locations:
            overall_score = sum(loc["confidence"] for loc in locations) / len(locations)
        
        return {
            "locations": locations,
            "primary_location": primary_location,
            "overall_score": overall_score,
            "meta": {
                "extractor": "gazetteer",
                "fallback_used": True
            }
        }
    
    def _find_match(self, text: str, aliases: Set[str]) -> bool:
        """Check if any alias is found in the text."""
        for alias in aliases:
            # Use word boundary matching to avoid partial matches
            pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return an empty but valid result."""
        return {
            "locations": [],
            "primary_location": None,
            "overall_score": 0.0,
            "meta": {
                "extractor": "gazetteer",
                "fallback_used": True
            }
        }
