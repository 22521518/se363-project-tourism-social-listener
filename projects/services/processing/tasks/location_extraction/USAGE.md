# Location Extraction Module - Usage Guide

## Quick Start
1. **Enable LLM Support**  
   Copy the example environment file and add your Google/TogetherAI API key.
   ```bash
   cp .env.example .env
   # Edit .env: GOOGLE_API_KEY=your_key
   ```
   
2. **Install Dependencies**  
   From the module directory:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Examples**
   ```bash
   # Test without API key (Gazetteer/Regex)
   python examples/test_without_llm.py
   
   # Test with LLM (requires .env config)
   python examples/test_with_llm.py
   
   # Run full demonstration
   python examples/basic_usage.py
   ```

## Integration Guide

### Minimal Usage
Add the module to your python path and use the convenience function:
```python
import sys
sys.path.append("/path/to/location_extraction")

from pipelines import extract_locations_from_text

result = extract_locations_from_text("Visit Da Nang")
print(result.to_dict())
```

### Advanced Usage (Pipeline)
For full control or processing Kafka events:
```python
from dto import UnifiedTextEvent
from pipelines import ExtractionPipeline

# Create exact event structure
event = UnifiedTextEvent(
    source="youtube",
    source_type="comment",
    external_id="123",
    text="Hanoi is beautiful in autumn"
)

# Process 
pipeline = ExtractionPipeline()
result = pipeline.process(event)
```

### Custom Extractors
Use specific extraction strategies directly:
```python
from extractors import GazetteerLocationExtractor

extractor = GazetteerLocationExtractor()
result = extractor.extract("Ho Chi Minh City")
```

## Troubleshooting
**"No module named 'langchain'"**  
Run `pip install -r requirements.txt`.

**Empty Results?**  
- Without an API key, only exact matches for major Vietnamese cities/landmarks work.
- Add an API key to enable semantic LLM extraction.
