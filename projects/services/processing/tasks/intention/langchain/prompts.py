# prompts.py
from langchain_core.prompts import ChatPromptTemplate

BATCH_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an expert at analyzing user comments and extracting their intention.
        
Valid intention types:
- question: User is asking something
- feedback: User is providing constructive feedback
- complaint: User is expressing dissatisfaction
- suggestion: User is proposing an idea or improvement
- praise: User is expressing appreciation or compliment
- request: User is asking for something specific
- discussion: User is engaging in conversation
- spam: Irrelevant, promotional, or malicious content
- other: Does not fit any above category

Analyze each comment."""
    ),
    (
        "human",
        """Analyze the following comments and classify each one's intention.

Each item contains:
- text: The comment text

Return results in the SAME ORDER as the input.

ITEMS:
{items}"""
    ),
])