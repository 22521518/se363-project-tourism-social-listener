"""
Example: Test the module without LLM API key.

Uses only the Gazetteer and Regex extractors (no API key needed).

Run:
    python examples/test_without_llm.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dto import UnifiedTextEvent
from extractors import GazetteerLocationExtractor, RegexLocationExtractor
from pipelines import ExtractionPipeline


def main():
    print("🧪 Testing Location Extraction WITHOUT LLM (no API key needed)\n")
    
    # Create pipeline with only fallback extractors
    pipeline = ExtractionPipeline(
        llm_extractor=None,  # No LLM
        gazetteer_extractor=GazetteerLocationExtractor(),
        regex_extractor=RegexLocationExtractor()
    )
    
    # Test cases
    test_texts = [
        "I love visiting Ho Chi Minh City",
        "Da Nang has beautiful beaches",
        "Ha Long Bay is a UNESCO World Heritage Site",
        "We traveled from Hanoi to Sapa",
        "Bangkok and Singapore are amazing cities",
        "The Eiffel Tower in Paris is stunning",
        "Tôi đã đến Đà Nẵng và Hội An",  # Vietnamese
        "No location mentioned here",
    ]
    
    for text in test_texts:
        event = UnifiedTextEvent(
            source="test",
            source_type="text",
            external_id="test",
            text=text
        )
        
        result = pipeline.process(event)
        
        print(f"📝 Text: {text}")
        if result.locations:
            locs = ", ".join([f"{l.name} ({l.type})" for l in result.locations])
            print(f"   ✅ Found: {locs}")
        else:
            print(f"   ❌ No locations found")
        print(f"   📊 Extractor: {result.meta.extractor}\n")


if __name__ == "__main__":
    main()
