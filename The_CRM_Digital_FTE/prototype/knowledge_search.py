"""
Knowledge Base Search Prototype
Phase: Incubation (TASK-005)

Simple keyword-based search for product documentation.
For prototype: Uses basic string matching and relevance scoring.
Production version will use pgvector with embeddings.
"""

import os
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Represents a single search result."""
    title: str
    content: str
    relevance_score: float
    category: str
    url: str


class KnowledgeBaseSearch:
    """
    Simple knowledge base search using keyword matching.
    Loads product documentation and performs searches.
    """

    def __init__(self, docs_path: str = None):
        """
        Initialize knowledge base search.

        Args:
            docs_path: Path to product documentation file
        """
        self.docs_path = docs_path or os.path.join(
            os.path.dirname(__file__),
            "..",
            "context",
            "product-docs.md"
        )
        self.knowledge_base = []
        self._load_documentation()

    def _load_documentation(self):
        """Load and parse product documentation into searchable chunks."""
        try:
            with open(self.docs_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split documentation into sections based on headers
            sections = self._parse_sections(content)
            self.knowledge_base = sections

            print(f"Loaded {len(self.knowledge_base)} knowledge base articles")

        except FileNotFoundError:
            print(f"Warning: Documentation file not found at {self.docs_path}")
            self.knowledge_base = []

    def _parse_sections(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse markdown documentation into searchable sections.

        Args:
            content: Full markdown content

        Returns:
            List of section dictionaries
        """
        sections = []

        # Split by ## headers (main sections)
        parts = re.split(r'\n## ', content)

        for i, part in enumerate(parts):
            if i == 0:
                # Skip the title and table of contents
                continue

            lines = part.split('\n')
            title = lines[0].strip()
            section_content = '\n'.join(lines[1:]).strip()

            # Determine category from title
            category = self._categorize_section(title)

            # Create URL (simplified for prototype)
            url = f"help.techcorp.com/{title.lower().replace(' ', '-')}"

            sections.append({
                'title': title,
                'content': section_content,
                'category': category,
                'url': url,
                'keywords': self._extract_keywords(title + ' ' + section_content)
            })

            # Also parse subsections (### headers)
            subsections = re.split(r'\n### ', section_content)
            for j, subsection in enumerate(subsections):
                if j == 0:
                    continue

                sub_lines = subsection.split('\n')
                sub_title = sub_lines[0].strip()
                sub_content = '\n'.join(sub_lines[1:]).strip()

                full_title = f"{title} - {sub_title}"
                sub_url = f"help.techcorp.com/{title.lower().replace(' ', '-')}#{sub_title.lower().replace(' ', '-')}"

                sections.append({
                    'title': full_title,
                    'content': sub_content,
                    'category': category,
                    'url': sub_url,
                    'keywords': self._extract_keywords(full_title + ' ' + sub_content)
                })

        return sections

    def _categorize_section(self, title: str) -> str:
        """Categorize section based on title."""
        title_lower = title.lower()

        if any(word in title_lower for word in ['account', 'password', 'login', 'email']):
            return 'authentication'
        elif any(word in title_lower for word in ['billing', 'subscription', 'payment', 'plan']):
            return 'billing'
        elif any(word in title_lower for word in ['task', 'project', 'workflow']):
            return 'features'
        elif any(word in title_lower for word in ['integration', 'slack', 'github', 'google']):
            return 'integrations'
        elif any(word in title_lower for word in ['mobile', 'app', 'ios', 'android']):
            return 'mobile'
        elif any(word in title_lower for word in ['api', 'developer']):
            return 'api'
        else:
            return 'general'

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for search matching."""
        # Convert to lowercase and remove special characters
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)

        # Split into words
        words = text.split()

        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }

        keywords = [word for word in words if word not in stop_words and len(word) > 2]

        return keywords

    def search(
        self,
        query: str,
        max_results: int = 5,
        category: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Search knowledge base for relevant articles.

        Args:
            query: Search query text
            max_results: Maximum number of results to return
            category: Optional category filter

        Returns:
            List of SearchResult objects, sorted by relevance
        """
        if not query or not query.strip():
            return []

        # Extract keywords from query
        query_keywords = self._extract_keywords(query)

        if not query_keywords:
            return []

        # Calculate relevance scores for all articles
        scored_results = []

        for article in self.knowledge_base:
            # Skip if category filter doesn't match
            if category and article['category'] != category:
                continue

            # Calculate relevance score
            score = self._calculate_relevance(query_keywords, article)

            if score > 0:
                scored_results.append({
                    'article': article,
                    'score': score
                })

        # Sort by relevance score (descending)
        scored_results.sort(key=lambda x: x['score'], reverse=True)

        # Convert to SearchResult objects
        results = []
        for item in scored_results[:max_results]:
            article = item['article']
            results.append(SearchResult(
                title=article['title'],
                content=self._truncate_content(article['content']),
                relevance_score=item['score'],
                category=article['category'],
                url=article['url']
            ))

        return results

    def _calculate_relevance(
        self,
        query_keywords: List[str],
        article: Dict[str, Any]
    ) -> float:
        """
        Calculate relevance score between query and article.
        Simple keyword matching for prototype.

        Args:
            query_keywords: List of keywords from query
            article: Article dictionary

        Returns:
            Relevance score (0.0 to 1.0)
        """
        article_keywords = article['keywords']
        title_lower = article['title'].lower()
        content_lower = article['content'].lower()

        score = 0.0
        matched_keywords = 0

        for keyword in query_keywords:
            # Title match (highest weight)
            if keyword in title_lower:
                score += 0.5
                matched_keywords += 1

            # Keyword match (medium weight)
            elif keyword in article_keywords:
                score += 0.3
                matched_keywords += 1

            # Content match (lower weight)
            elif keyword in content_lower:
                score += 0.1
                matched_keywords += 1

        # Normalize score based on query length
        if len(query_keywords) > 0:
            score = score / len(query_keywords)

        # Boost score if multiple keywords matched
        if matched_keywords > 1:
            score *= (1 + (matched_keywords - 1) * 0.1)

        # Cap at 1.0
        return min(score, 1.0)

    def _truncate_content(self, content: str, max_length: int = 500) -> str:
        """Truncate content to max length for display."""
        if len(content) <= max_length:
            return content

        # Truncate at word boundary
        truncated = content[:max_length]
        last_space = truncated.rfind(' ')

        if last_space > 0:
            truncated = truncated[:last_space]

        return truncated + "..."

    def format_results(self, results: List[SearchResult]) -> str:
        """
        Format search results for display.

        Args:
            results: List of SearchResult objects

        Returns:
            Formatted string with all results
        """
        if not results:
            return "No relevant articles found in the knowledge base."

        formatted = []

        for i, result in enumerate(results, 1):
            formatted.append(
                f"**{result.title}** (relevance: {result.relevance_score:.2f})\n"
                f"{result.content}\n"
                f"Learn more: {result.url}\n"
            )

        return "\n---\n\n".join(formatted)


# Example usage and testing
if __name__ == "__main__":
    # Initialize knowledge base
    kb = KnowledgeBaseSearch()

    # Test queries
    test_queries = [
        "how to reset password",
        "export project data",
        "slack integration not working",
        "create recurring tasks",
        "API documentation",
        "mobile app offline mode",
        "billing and subscription",
        "time tracking",
        "gantt chart",
        "team permissions",
        "dark mode",  # Should return no results (feature doesn't exist)
        "invalid query xyz123"  # Should return no results
    ]

    print("=" * 80)
    print("KNOWLEDGE BASE SEARCH TESTS")
    print("=" * 80)

    for query in test_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 80)

        results = kb.search(query, max_results=3)

        if results:
            print(f"Found {len(results)} results:\n")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result.title}")
                print(f"   Relevance: {result.relevance_score:.2f}")
                print(f"   Category: {result.category}")
                print(f"   URL: {result.url}")
                print(f"   Preview: {result.content[:100]}...")
                print()
        else:
            print("No results found.")

        print()

    print("=" * 80)
    print("FORMATTED OUTPUT TEST")
    print("=" * 80)

    # Test formatted output
    query = "how to reset my password"
    results = kb.search(query, max_results=2)
    formatted = kb.format_results(results)

    print(f"\nQuery: '{query}'")
    print("-" * 80)
    print(formatted)
