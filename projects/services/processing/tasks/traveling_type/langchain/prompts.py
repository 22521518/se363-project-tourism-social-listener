# prompts.py
from langchain_core.prompts import ChatPromptTemplate

BATCH_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an expert at analyzing travel-related comments and identifying the type of travel being discussed.

Valid traveling types:
- business: Work-related travel, conferences, business trips
- leisure: General vacation, sightseeing, relaxation
- adventure: Hiking, extreme sports, outdoor activities
- backpacking: Budget travel with backpack, hostels, long-term travel
- luxury: High-end hotels, fine dining, premium experiences
- budget: Cost-conscious travel, finding deals, cheap accommodation
- solo: Traveling alone, solo traveler experiences
- group: Organized group tours, traveling with friends
- family: Family vacation, traveling with children
- romantic: Honeymoon, couples' getaway, romantic experiences
- other: Does not fit any above category or unclear

Analyze each comment to determine the traveling type being discussed or experienced."""
    ),
    (
        "human",
        """Analyze the following comments and classify each one's traveling type.

Each item contains:
- text: The comment text

Return results in the SAME ORDER as the input.

ITEMS:
{items}"""
    ),
])