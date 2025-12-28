"""
Example: Test with LLM (Google Gemini).

Make sure to:
1. Install requirements: pip install -r requirements.txt
2. Set GOOGLE_API_KEY in .env file

Run:
    python examples/test_with_llm.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from dto import UnifiedTextEvent
from pipelines import ExtractionPipeline


def main():
    print("🤖 Testing Location Extraction WITH LLM (Google Gemini)\n")
    
    # Create pipeline (will use LLM if API key is configured)
    pipeline = ExtractionPipeline()
    
    # Test cases - these work best with LLM
    test_texts = [
        "I'm planning a trip to the coffee shops in District 1, Saigon",
        "The ancient town of Hoi An is known for its lanterns",
        "We hiked up Fansipan, the highest peak in Vietnam",
        "The Cu Chi tunnels give insight into Vietnam War history",
        "Mekong Delta boat tours are amazing",
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
            for loc in result.locations:
                print(f"   📍 {loc.name} ({loc.type}) - confidence: {loc.confidence:.2f}")
        else:
            print(f"   ❌ No locations found")
        
        if result.primary_location:
            print(f"   🎯 Primary: {result.primary_location.name}")
        
        print(f"   📊 Extractor: {result.meta.extractor}, Fallback: {result.meta.fallback_used}\n")


if __name__ == "__main__":
    main()
