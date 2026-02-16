"""
Load Knowledge Base Script
Populates the knowledge base with product documentation and generates embeddings.
"""

import os
import asyncio
import json
from uuid import uuid4
from typing import List, Dict, Any

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_db_context
from src.database.models import KnowledgeBase


async def load_knowledge_base():
    """Load knowledge base from context files."""
    print("Loading knowledge base...")

    # Initialize OpenAI client
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    embedding_model = "text-embedding-3-small"

    # Load product documentation
    with open("context/product-docs.md", "r") as f:
        product_docs = f.read()

    # Parse documentation into articles
    articles = parse_documentation(product_docs)
    print(f"Parsed {len(articles)} articles from documentation")

    # Generate embeddings and store in database
    async with get_db_context() as db:
        for article in articles:
            print(f"Processing: {article['title']}")

            # Generate embedding
            embedding_response = await client.embeddings.create(
                model=embedding_model,
                input=article['content']
            )
            embedding = embedding_response.data[0].embedding

            # Check if article already exists
            result = await db.execute(
                select(KnowledgeBase).where(KnowledgeBase.title == article['title'])
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing article
                existing.content = article['content']
                existing.embedding = embedding
                existing.category = article['category']
                existing.metadata = article.get('metadata', {})
                print(f"  Updated existing article")
            else:
                # Create new article
                kb_entry = KnowledgeBase(
                    id=uuid4(),
                    title=article['title'],
                    content=article['content'],
                    embedding=embedding,
                    category=article['category'],
                    metadata=article.get('metadata', {})
                )
                db.add(kb_entry)
                print(f"  Created new article")

        await db.commit()

    print(f"\nKnowledge base loaded successfully!")
    print(f"Total articles: {len(articles)}")


def parse_documentation(content: str) -> List[Dict[str, Any]]:
    """
    Parse markdown documentation into structured articles.

    Args:
        content: Markdown content

    Returns:
        List of article dictionaries
    """
    articles = []
    current_article = None
    current_content = []
    current_category = "general"

    lines = content.split('\n')

    for line in lines:
        # Detect category headers (## Category)
        if line.startswith('## '):
            current_category = line[3:].strip().lower().replace(' ', '_')
            continue

        # Detect article headers (### Title)
        if line.startswith('### '):
            # Save previous article
            if current_article:
                current_article['content'] = '\n'.join(current_content).strip()
                articles.append(current_article)

            # Start new article
            title = line[4:].strip()
            current_article = {
                'title': title,
                'category': current_category,
                'metadata': {}
            }
            current_content = []
            continue

        # Accumulate content
        if current_article:
            current_content.append(line)

    # Save last article
    if current_article:
        current_article['content'] = '\n'.join(current_content).strip()
        articles.append(current_article)

    return articles


async def verify_knowledge_base():
    """Verify knowledge base was loaded correctly."""
    print("\nVerifying knowledge base...")

    async with get_db_context() as db:
        result = await db.execute(select(KnowledgeBase))
        articles = result.scalars().all()

        print(f"Total articles in database: {len(articles)}")

        # Count by category
        categories = {}
        for article in articles:
            cat = article.category
            categories[cat] = categories.get(cat, 0) + 1

        print("\nArticles by category:")
        for cat, count in sorted(categories.items()):
            print(f"  {cat}: {count}")

        # Show sample articles
        print("\nSample articles:")
        for article in articles[:5]:
            print(f"  - {article.title} ({article.category})")
            print(f"    Content length: {len(article.content)} chars")
            print(f"    Embedding dimensions: {len(article.embedding) if article.embedding else 0}")


if __name__ == "__main__":
    asyncio.run(load_knowledge_base())
    asyncio.run(verify_knowledge_base())
