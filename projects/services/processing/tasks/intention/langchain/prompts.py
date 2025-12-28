# prompts.py
from langchain_core.prompts import ChatPromptTemplate

BATCH_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You extract intention from user comments."
        ),
        (
            "human",
            """
Each item contains:
- text
- video_title

Analyze ALL items.
Preserve order.
Return one result per item.

ITEMS:
{items}
"""
        ),
    ]
)
