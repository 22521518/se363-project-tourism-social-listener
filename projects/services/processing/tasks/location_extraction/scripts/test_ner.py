#!/usr/bin/env python
"""
Test script for NER Location Extractor.

Usage:
    python test_ner.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))

from projects.services.processing.tasks.location_extraction.extractors.ner_extractor import NERLocationExtractor


def test_ner_extraction():
    """Test NER extraction with sample Vietnamese text."""
    print("Initializing NER extractor...")
    extractor = NERLocationExtractor()
    
    test_text = "Tôi đi Hà Nội và Paris"
    print(f"\nTest text: {test_text}")
    
    print("\nRunning extraction...")
    result = extractor.extract(test_text)
    
    print(f"\nResult: {result}")
    
    # Validate structure
    assert "locations" in result, "Result must have 'locations' key"
    assert isinstance(result["locations"], list), "'locations' must be a list"
    
    print("\n=== Extracted Locations ===")
    for loc in result["locations"]:
        print(f"  - word: {loc['word']}, score: {loc['score']:.4f}, "
              f"entity_group: {loc['entity_group']}, start: {loc['start']}, end: {loc['end']}")
    
    # Check expected locations
    location_words = [loc["word"] for loc in result["locations"]]
    print(f"\nLocation words found: {location_words}")
    
    # Hà Nội and Paris should be detected
    expected_locations = ["Hà Nội", "Paris"]
    for expected in expected_locations:
        if any(expected in word for word in location_words):
            print(f"✓ Found expected location: {expected}")
        else:
            print(f"✗ Missing expected location: {expected}")
    
    print("\n=== Test Complete ===")
    return result


if __name__ == "__main__":
    test_ner_extraction()
