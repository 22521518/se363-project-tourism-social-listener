"""
Extraction Router - Decides extraction strategy based on content type.

This module maps content_type to:
- Expected tourism sections to extract
- LLM extraction instructions
- Crawl strategy (single vs deep)
"""
from dataclasses import dataclass, field
from typing import List, Literal


@dataclass
class ExtractionConfig:
    """Configuration for extraction strategy."""
    content_type: str
    expected_sections: List[str]
    llm_instruction: str
    crawl_strategy: Literal["single", "deep"] = "single"
    extraction_strategy: Literal["css", "llm"] = "llm"


# Mapping of content types to expected sections
CONTENT_TYPE_SECTIONS = {
    "forum": ["comments", "travel_experiences", "discussions"],
    "review": ["reviews", "ratings", "information"],
    "blog": ["blog_sections", "information", "travel_tips"],
    "agency": ["agency_info", "pricing", "tour_details", "included_services"],
    "auto": ["reviews", "comments", "information", "blog_sections", "agency_info", "pricing"],
}


# LLM instructions for each content type
LLM_INSTRUCTIONS = {
    "forum": """
Extract ONLY tourism-related forum content including:
- Travel discussions and experiences
- User comments about destinations, hotels, restaurants
- Travel tips and recommendations shared by community members
- Questions and answers about tourism

Return as structured JSON with 'comments' array containing 'author' and 'text' fields.
Do NOT include off-topic discussions or advertisements.
""",
    "review": """
Extract ONLY tourism-related reviews including:
- Hotel, restaurant, attraction reviews
- Author/reviewer name
- Rating score (numeric if available)
- Review text content
- Location/destination information

Return as structured JSON with 'reviews' array containing 'author', 'text', and 'rating' fields.
Also extract 'title' and general 'information' about the place.
Do NOT summarize or paraphrase - extract the actual review text.
""",
    "blog": """
Extract ONLY tourism-related blog content including:
- Article title
- Section headings and their content
- Travel destinations mentioned
- Travel experiences and tips
- Accommodation and food recommendations

Return as structured JSON with 'title', 'information', and 'blog_sections' array 
containing 'heading' and 'text' for each section.
Do NOT include comment sections or advertisements.
""",
    "agency": """
Extract ONLY travel agency/tour information including:
- Tour name
- Price information
- Duration
- Included services list
- Destination details
- Itinerary information

Return as structured JSON with 'agency_info' object containing 
'tour_name', 'price', 'duration', and 'included_services' array.
Also extract general 'information' about the tour.
Do NOT include website navigation or unrelated content.
""",
    "auto": """
Extract ALL tourism-related information from this page including:
- Reviews (author, text, rating)
- Comments/discussions (author, text)
- Blog content (heading, text sections)
- Tour/agency info (tour_name, price, duration, included_services)
- General information about destinations, hotels, restaurants
- Travel tips and recommendations

Return as structured JSON with all applicable fields populated.
Only include tourism/travel related content.
Do NOT include advertisements, navigation menus, or unrelated content.
Do NOT summarize or paraphrase - extract actual text content.
""",
}


def get_extraction_config(content_type: str) -> ExtractionConfig:
    """
    Get extraction configuration based on content type.
    
    Args:
        content_type: One of 'forum', 'review', 'blog', 'agency', 'auto'
        
    Returns:
        ExtractionConfig with appropriate settings
    """
    # Validate content_type
    if content_type not in CONTENT_TYPE_SECTIONS:
        content_type = "auto"
    
    expected_sections = CONTENT_TYPE_SECTIONS[content_type]
    llm_instruction = LLM_INSTRUCTIONS[content_type]
    
    # Determine crawl strategy
    # Forums and blogs may need deep crawl for pagination
    crawl_strategy: Literal["single", "deep"] = "single"
    if content_type in ("forum", "blog"):
        # TODO: Implement deep crawl detection logic
        # For now, use single page crawl
        crawl_strategy = "single"
    
    return ExtractionConfig(
        content_type=content_type,
        expected_sections=expected_sections,
        llm_instruction=llm_instruction.strip(),
        crawl_strategy=crawl_strategy,
        extraction_strategy="llm",
    )


def detect_sections_from_content(extracted_data: dict) -> List[str]:
    """
    Detect which sections were actually extracted from the content.
    
    Args:
        extracted_data: The extracted content dictionary
        
    Returns:
        List of section names that have content
    """
    detected = []
    
    if extracted_data.get("reviews") and len(extracted_data["reviews"]) > 0:
        detected.append("review")
    
    if extracted_data.get("comments") and len(extracted_data["comments"]) > 0:
        detected.append("comment")
    
    if extracted_data.get("information"):
        detected.append("information")
    
    if extracted_data.get("blog_sections") and len(extracted_data["blog_sections"]) > 0:
        detected.append("blog")
    
    if extracted_data.get("agency_info"):
        agency = extracted_data["agency_info"]
        if any([agency.get("tour_name"), agency.get("price"), agency.get("duration")]):
            detected.append("agency")
            if agency.get("price"):
                detected.append("pricing")
    
    return detected
