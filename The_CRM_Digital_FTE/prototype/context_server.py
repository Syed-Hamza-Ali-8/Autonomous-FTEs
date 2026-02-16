"""
MCP Server for Customer Success Context
Phase: Incubation (TASK-009)

Provides context management for the Customer Success AI agent.
Exposes company profile, product docs, escalation rules, and brand voice.
"""

import json
import os
from typing import Dict, Any, List, Optional


class ContextServer:
    """
    MCP-style server for managing agent context.
    Provides access to company profile, product docs, escalation rules, and brand voice.
    """

    def __init__(self, context_dir: str = None):
        """
        Initialize context server.

        Args:
            context_dir: Path to context directory
        """
        self.context_dir = context_dir or os.path.join(
            os.path.dirname(__file__),
            '..',
            'context'
        )
        self.context_cache = {}
        self._load_all_context()

    def _load_all_context(self):
        """Load all context files into memory."""
        context_files = {
            'company_profile': 'company-profile.md',
            'product_docs': 'product-docs.md',
            'escalation_rules': 'escalation-rules.md',
            'brand_voice': 'brand-voice.md',
            'sample_tickets': 'sample-tickets.json'
        }

        for key, filename in context_files.items():
            filepath = os.path.join(self.context_dir, filename)
            if os.path.exists(filepath):
                if filename.endswith('.json'):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        self.context_cache[key] = json.load(f)
                else:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        self.context_cache[key] = f.read()

    def get_company_profile(self) -> str:
        """Get company profile context."""
        return self.context_cache.get('company_profile', '')

    def get_product_docs(self) -> str:
        """Get product documentation."""
        return self.context_cache.get('product_docs', '')

    def get_escalation_rules(self) -> str:
        """Get escalation rules."""
        return self.context_cache.get('escalation_rules', '')

    def get_brand_voice(self) -> str:
        """Get brand voice guidelines."""
        return self.context_cache.get('brand_voice', '')

    def get_sample_tickets(self) -> List[Dict[str, Any]]:
        """Get sample tickets."""
        data = self.context_cache.get('sample_tickets', {})
        return data.get('sample_tickets', [])

    def search_product_docs(self, query: str) -> str:
        """
        Search product documentation for relevant sections.

        Args:
            query: Search query

        Returns:
            Relevant documentation sections
        """
        docs = self.get_product_docs()
        query_lower = query.lower()

        # Simple section extraction based on headers
        sections = []
        current_section = []
        current_header = None

        for line in docs.split('\n'):
            if line.startswith('## '):
                if current_section and current_header:
                    section_text = '\n'.join(current_section)
                    if query_lower in section_text.lower():
                        sections.append(f"{current_header}\n{section_text}")
                current_header = line
                current_section = []
            else:
                current_section.append(line)

        # Add last section
        if current_section and current_header:
            section_text = '\n'.join(current_section)
            if query_lower in section_text.lower():
                sections.append(f"{current_header}\n{section_text}")

        return '\n\n---\n\n'.join(sections[:3]) if sections else "No relevant documentation found."

    def get_escalation_trigger(self, reason: str) -> Optional[Dict[str, Any]]:
        """
        Get escalation trigger details for a specific reason.

        Args:
            reason: Escalation reason

        Returns:
            Escalation trigger details
        """
        rules = self.get_escalation_rules()

        # Parse escalation rules (simplified)
        triggers = {
            'billing_issue': {
                'urgency': 'high',
                'response_time': '4 hours',
                'keywords': ['refund', 'charged twice', 'billing error', 'invoice']
            },
            'sales_opportunity': {
                'urgency': 'high',
                'response_time': '4 hours',
                'keywords': ['enterprise pricing', 'custom pricing', 'partnership']
            },
            'negative_sentiment': {
                'urgency': 'high',
                'response_time': '2 hours',
                'keywords': ['frustrated', 'angry', 'unacceptable', 'switching to']
            },
            'critical_issue': {
                'urgency': 'critical',
                'response_time': '1 hour',
                'keywords': ['data loss', 'security breach', 'tasks disappeared']
            }
        }

        return triggers.get(reason)

    def get_channel_guidelines(self, channel: str) -> Dict[str, Any]:
        """
        Get brand voice guidelines for specific channel.

        Args:
            channel: Channel name (email, whatsapp, web_form)

        Returns:
            Channel-specific guidelines
        """
        guidelines = {
            'email': {
                'tone': 'formal',
                'length': '200-500 words',
                'structure': 'Greeting → Body → Closing → Signature',
                'style': 'Professional, detailed, comprehensive'
            },
            'whatsapp': {
                'tone': 'casual',
                'length': '<300 chars preferred, max 1600',
                'structure': 'Brief greeting → Direct answer → Quick offer',
                'style': 'Concise, conversational, friendly',
                'emojis': '1-2 per message'
            },
            'web_form': {
                'tone': 'semi-formal',
                'length': '150-300 words',
                'structure': 'Acknowledgment → Body → Resources → Offer',
                'style': 'Structured, helpful, actionable'
            }
        }

        return guidelines.get(channel, guidelines['web_form'])

    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of available context."""
        return {
            'company_profile': bool(self.context_cache.get('company_profile')),
            'product_docs': bool(self.context_cache.get('product_docs')),
            'escalation_rules': bool(self.context_cache.get('escalation_rules')),
            'brand_voice': bool(self.context_cache.get('brand_voice')),
            'sample_tickets_count': len(self.get_sample_tickets()),
            'context_dir': self.context_dir
        }

    def get_full_context_for_agent(self) -> str:
        """
        Get full context formatted for agent consumption.

        Returns:
            Formatted context string
        """
        parts = []

        parts.append("# CUSTOMER SUCCESS AGENT CONTEXT\n")

        parts.append("## COMPANY PROFILE\n")
        parts.append(self.get_company_profile())
        parts.append("\n---\n")

        parts.append("## ESCALATION RULES\n")
        parts.append(self.get_escalation_rules())
        parts.append("\n---\n")

        parts.append("## BRAND VOICE GUIDELINES\n")
        parts.append(self.get_brand_voice())
        parts.append("\n---\n")

        parts.append("## PRODUCT DOCUMENTATION (SUMMARY)\n")
        docs = self.get_product_docs()
        parts.append(docs[:2000] + "...\n[Full documentation available via search]")

        return '\n'.join(parts)


# Example usage and testing
if __name__ == "__main__":
    print("=" * 80)
    print("CONTEXT SERVER TESTING")
    print("=" * 80)
    print()

    # Initialize context server
    server = ContextServer()

    # Test 1: Get context summary
    print("Test 1: Context Summary")
    print("-" * 80)
    summary = server.get_context_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    print()

    # Test 2: Get channel guidelines
    print("Test 2: Channel Guidelines")
    print("-" * 80)
    for channel in ['email', 'whatsapp', 'web_form']:
        guidelines = server.get_channel_guidelines(channel)
        print(f"\n{channel.upper()}:")
        for key, value in guidelines.items():
            print(f"  {key}: {value}")
    print()

    # Test 3: Search product docs
    print("Test 3: Search Product Documentation")
    print("-" * 80)
    queries = ['password reset', 'data export', 'API documentation']
    for query in queries:
        print(f"\nQuery: '{query}'")
        result = server.search_product_docs(query)
        print(f"Found: {len(result)} characters")
        print(f"Preview: {result[:200]}...")
    print()

    # Test 4: Get escalation triggers
    print("Test 4: Escalation Triggers")
    print("-" * 80)
    reasons = ['billing_issue', 'sales_opportunity', 'negative_sentiment', 'critical_issue']
    for reason in reasons:
        trigger = server.get_escalation_trigger(reason)
        if trigger:
            print(f"\n{reason}:")
            print(f"  Urgency: {trigger['urgency']}")
            print(f"  Response Time: {trigger['response_time']}")
            print(f"  Keywords: {', '.join(trigger['keywords'][:3])}")
    print()

    # Test 5: Get full context
    print("Test 5: Full Context for Agent")
    print("-" * 80)
    full_context = server.get_full_context_for_agent()
    print(f"Total context length: {len(full_context)} characters")
    print(f"Preview:\n{full_context[:500]}...")
    print()

    print("=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)
