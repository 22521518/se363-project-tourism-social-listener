"""
Example: Basic usage of the Location Extraction module.

Run this script from the location_extraction directory:
    python examples/basic_usage.py

Make sure to:
1. Install requirements: pip install -r requirements.txt
2. Copy .env.example to .env and add your API key
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dto import UnifiedTextEvent
from pipelines import ExtractionPipeline, extract_locations_from_text


def example_simple_text():
    """Extract locations from a simple text string."""
    print("=" * 60)
    print("Example 1: Simple Text Extraction")
    print("=" * 60)
    
    text = "I visited Ho Chi Minh City and Da Nang last summer"
    
    result = extract_locations_from_text(text)
    
    print(f"Input: {text}")
    print(f"\nExtracted Locations:")
    for loc in result.locations:
        print(f"  - {loc.name} ({loc.type}): {loc.confidence:.2f}")
    
    if result.primary_location:
        print(f"\nPrimary Location: {result.primary_location.name}")
    
    print(f"Overall Score: {result.overall_score:.2f}")
    print(f"Extractor Used: {result.meta.extractor}")
    print(f"Fallback Used: {result.meta.fallback_used}")


def example_vietnamese_text():
    """Extract locations from Vietnamese text."""
    print("\n" + "=" * 60)
    print("Example 2: Vietnamese Text Extraction")
    print("=" * 60)
    
    text = "Tôi đã đến Đà Nẵng và Hội An vào mùa hè năm ngoái"
    
    result = extract_locations_from_text(text)
    
    print(f"Input: {text}")
    print(f"\nExtracted Locations:")
    for loc in result.locations:
        print(f"  - {loc.name} ({loc.type}): {loc.confidence:.2f}")
    
    print(f"Extractor Used: {result.meta.extractor}")


def example_unified_event():
    """Process a UnifiedTextEvent (simulating Kafka message)."""
    print("\n" + "=" * 60)
    print("Example 3: UnifiedTextEvent Processing")
    print("=" * 60)
    
    # Create an event (simulating what comes from Kafka)
    event = UnifiedTextEvent(
        source="youtube",
        source_type="comment",
        external_id="comment_123456",
        text="Just came back from Ha Long Bay, absolutely stunning!",
        language="en",
        metadata={"video_id": "abc123", "channel": "travel_vlog"}
    )
    
    # Create pipeline and process
    pipeline = ExtractionPipeline()
    result = pipeline.process(event)
    
    print(f"Source: {event.source}/{event.source_type}")
    print(f"External ID: {event.external_id}")
    print(f"Text: {event.text}")
    print(f"\nExtracted Locations:")
    for loc in result.locations:
        print(f"  - {loc.name} ({loc.type}): {loc.confidence:.2f}")
    
    # Convert to dict for JSON serialization
    print(f"\nAs JSON dict:")
    import json
    print(json.dumps(result.to_dict(), indent=2))


def example_validated_record():
    """Show that validated records are skipped."""
    print("\n" + "=" * 60)
    print("Example 4: Validated Record (Skipped)")
    print("=" * 60)
    
    # Create a validated event (should be skipped)
    event = UnifiedTextEvent(
        source="facebook",
        source_type="post",
        external_id="post_789",
        text="Traveling to Paris next week!",
        validated=True,  # This record was already validated
        validated_by="admin_user"
    )
    
    pipeline = ExtractionPipeline()
    result = pipeline.process(event)
    
    print(f"Text: {event.text}")
    print(f"Validated: {event.validated}")
    print(f"Locations extracted: {len(result.locations)}")
    print("(No extraction performed - record already validated)")


def example_no_llm_fallback():
    """Show fallback when LLM is not available."""
    print("\n" + "=" * 60)
    print("Example 5: Fallback Extractors (No LLM)")
    print("=" * 60)
    
    from extractors import GazetteerLocationExtractor, RegexLocationExtractor
    
    # Use only gazetteer (no LLM)
    pipeline = ExtractionPipeline(
        llm_extractor=None,  # Disable LLM
        gazetteer_extractor=GazetteerLocationExtractor(),
        regex_extractor=RegexLocationExtractor()
    )
    
    event = UnifiedTextEvent(
        source="direct",
        source_type="text",
        external_id="test_1",
        text="The beach in Nha Trang is beautiful"
    )
    
    result = pipeline.process(event)
    
    print(f"Text: {event.text}")
    print(f"Extractor Used: {result.meta.extractor}")
    print(f"Fallback Used: {result.meta.fallback_used}")
    print(f"Locations: {[loc.name for loc in result.locations]}")


if __name__ == "__main__":
    print("\n🌍 Location Extraction Module - Examples\n")
    
    example_simple_text()
    example_vietnamese_text()
    example_unified_event()
    example_validated_record()
    example_no_llm_fallback()
    
    print("\n" + "=" * 60)
    print("✅ All examples completed!")
    print("=" * 60)
