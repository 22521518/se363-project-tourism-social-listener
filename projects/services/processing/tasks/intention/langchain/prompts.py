# prompts.py
# Prompt templates for intention extraction

from langchain.prompts import PromptTemplate


# Prompt for batch processing with context
BATCH_INTENTION_PROMPT = PromptTemplate(
    input_variables=["items"],
    template="""
    You are an intention extraction system.

    Each input item has the following structure:
    {
        "text": string,
        "video_title": string
    }

    For EACH item, extract from text:
    - intention_type: one of [question, feedback, complaint, suggestion, praise, request, discussion, spam, other]
    - sentiment: one of [positive, negative, neutral, mixed]

    Rules:
    - Process ALL items
    - Preserve ORDER exactly
    - Return STRICT JSON only
    - Do NOT add explanations
    - Do NOT change or merge items

    INPUT ITEMS:
    {items}

    OUTPUT FORMAT (JSON ARRAY):
    [
    {
        "intention_type": "...",
        "sentiment": "...",
    }
    ]
    """
)



# Validation definitions
VALID_INTENTIONS = [
    "question",
    "feedback", 
    "complaint",
    "suggestion",
    "praise",
    "request",
    "discussion",
    "spam",
    "other"
]

VALID_SENTIMENTS = [
    "positive",
    "negative",
    "neutral",
    "mixed"
]

INTENTION_DESCRIPTIONS = {
    "question": "User is asking for information, clarification, or help",
    "feedback": "User is providing constructive feedback or opinions",
    "complaint": "User is expressing dissatisfaction, problems, or criticism",
    "suggestion": "User is proposing ideas, improvements, or recommendations",
    "praise": "User is expressing appreciation, gratitude, or positive feedback",
    "request": "User is asking for specific content, features, or actions",
    "discussion": "User is engaging in conversation, debate, or dialogue",
    "spam": "Content is irrelevant, promotional, or low-quality",
    "other": "Does not fit into the above categories"
}

SENTIMENT_DESCRIPTIONS = {
    "positive": "Optimistic, happy, supportive, or encouraging tone",
    "negative": "Critical, upset, disappointed, or frustrated tone",
    "neutral": "Objective, factual, or emotionally balanced tone",
    "mixed": "Contains both positive and negative emotional elements"
}


def get_prompt(prompt_type: str = "default") -> PromptTemplate:
    """
    Get a prompt template by type.
    
    Args:
        prompt_type: Type of prompt to retrieve
                    Options: 'default', 'detailed', 'simple', 'batch'
    
    Returns:
        PromptTemplate instance
    """
    prompts = {
        "default":BATCH_INTENTION_PROMPT,
    }
    
    return prompts.get(prompt_type, BATCH_INTENTION_PROMPT)


def validate_intention(intention: str) -> str:
    """
    Validate and normalize intention type.
    
    Args:
        intention: Raw intention string
        
    Returns:
        Validated intention or 'other' if invalid
    """
    intention_lower = intention.lower().strip()
    return intention_lower if intention_lower in VALID_INTENTIONS else "other"


def validate_sentiment(sentiment: str) -> str:
    """
    Validate and normalize sentiment type.
    
    Args:
        sentiment: Raw sentiment string
        
    Returns:
        Validated sentiment or 'neutral' if invalid
    """
    sentiment_lower = sentiment.lower().strip()
    return sentiment_lower if sentiment_lower in VALID_SENTIMENTS else "neutral"


