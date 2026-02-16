"""
Prototype Testing Script
Phase: Incubation (TASK-007)

Tests the prototype with all 50 sample tickets and documents results.
Integrates: agent.py, knowledge_search.py, formatters.py
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Add prototype directory to path
sys.path.insert(0, os.path.dirname(__file__))

from agent import MessageProcessor
from knowledge_search import KnowledgeBaseSearch
from formatters import ResponseFormatter


class PrototypeTester:
    """
    Tests the Customer Success AI prototype with sample tickets.
    Tracks metrics and identifies edge cases.
    """

    def __init__(self):
        """Initialize tester with all components."""
        self.processor = MessageProcessor()
        self.kb_search = KnowledgeBaseSearch()
        self.formatter = ResponseFormatter()

        self.results = []
        self.edge_cases = []
        self.metrics = {
            'total_tickets': 0,
            'successful': 0,
            'failed': 0,
            'escalated': 0,
            'resolved_by_ai': 0,
            'avg_processing_time_ms': 0,
            'by_channel': {
                'email': {'total': 0, 'escalated': 0},
                'whatsapp': {'total': 0, 'escalated': 0},
                'web_form': {'total': 0, 'escalated': 0}
            },
            'by_category': {}
        }

    def load_sample_tickets(self) -> List[Dict[str, Any]]:
        """Load sample tickets from JSON file."""
        tickets_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'context',
            'sample-tickets.json'
        )

        with open(tickets_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data['sample_tickets']

    def test_all_tickets(self):
        """Run all sample tickets through the prototype."""
        print("=" * 80)
        print("PROTOTYPE TESTING - ALL SAMPLE TICKETS")
        print("=" * 80)
        print()

        tickets = self.load_sample_tickets()
        self.metrics['total_tickets'] = len(tickets)

        for i, ticket in enumerate(tickets, 1):
            print(f"Testing ticket {i}/{len(tickets)}: {ticket['id']}")
            print("-" * 80)

            result = self.test_single_ticket(ticket)
            self.results.append(result)

            # Update metrics
            self._update_metrics(result)

            # Check for edge cases
            self._check_edge_cases(ticket, result)

            print()

        # Calculate final metrics
        self._calculate_final_metrics()

        # Print summary
        self.print_summary()

        # Save results
        self.save_results()

    def test_single_ticket(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test a single ticket through the prototype.

        Returns:
            Result dictionary with processing details
        """
        start_time = datetime.now()

        # Process message
        process_result = self.processor.process_message(ticket)

        # If not escalated, try knowledge base search
        kb_results = None
        if process_result.get('success') and not process_result.get('should_escalate'):
            query = ticket.get('subject', '') + ' ' + ticket.get('body', '')
            kb_results = self.kb_search.search(query, max_results=3)

        # Format response for channel
        if process_result.get('success'):
            formatted_response = self.formatter.format_response(
                process_result['response'],
                ticket['channel'],
                ticket.get('customer_name', 'there'),
                ticket['id']
            )
        else:
            formatted_response = None

        elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        result = {
            'ticket_id': ticket['id'],
            'channel': ticket['channel'],
            'category': ticket.get('category', 'unknown'),
            'priority': ticket.get('priority', 'medium'),
            'success': process_result.get('success', False),
            'escalated': process_result.get('should_escalate', False),
            'escalation_reason': process_result.get('escalation_reason'),
            'processing_time_ms': elapsed_ms,
            'kb_results_count': len(kb_results) if kb_results else 0,
            'kb_top_relevance': kb_results[0].relevance_score if kb_results else 0.0,
            'response_length': len(formatted_response) if formatted_response else 0,
            'raw_response': process_result.get('response', ''),
            'formatted_response': formatted_response,
            'error': process_result.get('error')
        }

        # Print result summary
        print(f"  Channel: {result['channel']}")
        print(f"  Category: {result['category']}")
        print(f"  Success: {result['success']}")
        print(f"  Escalated: {result['escalated']}")
        if result['escalated']:
            print(f"  Escalation Reason: {result['escalation_reason']}")
        print(f"  KB Results: {result['kb_results_count']}")
        if result['kb_results_count'] > 0:
            print(f"  Top Relevance: {result['kb_top_relevance']:.2f}")
        print(f"  Processing Time: {result['processing_time_ms']}ms")
        print(f"  Response Length: {result['response_length']} chars")

        return result

    def _update_metrics(self, result: Dict[str, Any]):
        """Update metrics based on test result."""
        if result['success']:
            self.metrics['successful'] += 1
        else:
            self.metrics['failed'] += 1

        if result['escalated']:
            self.metrics['escalated'] += 1
        else:
            self.metrics['resolved_by_ai'] += 1

        # Update channel metrics
        channel = result['channel']
        self.metrics['by_channel'][channel]['total'] += 1
        if result['escalated']:
            self.metrics['by_channel'][channel]['escalated'] += 1

        # Update category metrics
        category = result['category']
        if category not in self.metrics['by_category']:
            self.metrics['by_category'][category] = {'total': 0, 'escalated': 0}
        self.metrics['by_category'][category]['total'] += 1
        if result['escalated']:
            self.metrics['by_category'][category]['escalated'] += 1

    def _check_edge_cases(self, ticket: Dict[str, Any], result: Dict[str, Any]):
        """Identify and document edge cases."""
        edge_case = None

        # Edge case 1: No KB results found
        if not result['escalated'] and result['kb_results_count'] == 0:
            edge_case = {
                'type': 'no_kb_results',
                'ticket_id': ticket['id'],
                'description': 'No knowledge base results found for query',
                'query': ticket.get('subject', '') + ' ' + ticket.get('body', '')[:100]
            }

        # Edge case 2: Low relevance KB results
        elif not result['escalated'] and result['kb_top_relevance'] < 0.5:
            edge_case = {
                'type': 'low_relevance_kb',
                'ticket_id': ticket['id'],
                'description': f'Low relevance KB results (score: {result["kb_top_relevance"]:.2f})',
                'query': ticket.get('subject', '') + ' ' + ticket.get('body', '')[:100]
            }

        # Edge case 3: Very short message (WhatsApp)
        elif ticket['channel'] == 'whatsapp' and len(ticket['body']) < 20:
            edge_case = {
                'type': 'very_short_message',
                'ticket_id': ticket['id'],
                'description': f'Very short WhatsApp message ({len(ticket["body"])} chars)',
                'message': ticket['body']
            }

        # Edge case 4: Very long message (Email)
        elif ticket['channel'] == 'email' and len(ticket['body']) > 500:
            edge_case = {
                'type': 'very_long_message',
                'ticket_id': ticket['id'],
                'description': f'Very long email message ({len(ticket["body"])} chars)',
                'message': ticket['body'][:100] + '...'
            }

        # Edge case 5: Multiple issues in one ticket
        elif '?' in ticket['body'] and ticket['body'].count('?') > 2:
            edge_case = {
                'type': 'multiple_questions',
                'ticket_id': ticket['id'],
                'description': f'Multiple questions in one ticket ({ticket["body"].count("?")} questions)',
                'message': ticket['body'][:100] + '...'
            }

        # Edge case 6: Escalated but low priority
        elif result['escalated'] and ticket.get('priority') == 'low':
            edge_case = {
                'type': 'escalated_low_priority',
                'ticket_id': ticket['id'],
                'description': 'Escalated ticket with low priority',
                'reason': result['escalation_reason']
            }

        # Edge case 7: High priority but not escalated
        elif not result['escalated'] and ticket.get('priority') == 'high':
            edge_case = {
                'type': 'high_priority_not_escalated',
                'ticket_id': ticket['id'],
                'description': 'High priority ticket not escalated',
                'category': ticket.get('category')
            }

        # Edge case 8: Billing category not escalated
        elif ticket.get('category') == 'billing' and not result['escalated']:
            edge_case = {
                'type': 'billing_not_escalated',
                'ticket_id': ticket['id'],
                'description': 'Billing issue not escalated (should be escalated)',
                'message': ticket['body'][:100]
            }

        # Edge case 9: Feature request
        elif ticket.get('category') == 'feature_request':
            edge_case = {
                'type': 'feature_request',
                'ticket_id': ticket['id'],
                'description': 'Feature request handling',
                'escalated': result['escalated']
            }

        # Edge case 10: Positive feedback
        elif ticket.get('category') == 'feedback' and 'thank' in ticket['body'].lower():
            edge_case = {
                'type': 'positive_feedback',
                'ticket_id': ticket['id'],
                'description': 'Positive feedback/thank you message',
                'escalated': result['escalated']
            }

        # Edge case 11: Response too long for channel
        elif result['response_length'] > self.formatter.max_lengths.get(ticket['channel'], 2000):
            edge_case = {
                'type': 'response_too_long',
                'ticket_id': ticket['id'],
                'description': f'Response exceeds channel limit ({result["response_length"]} chars)',
                'channel': ticket['channel']
            }

        # Edge case 12: Processing time too high
        elif result['processing_time_ms'] > 1000:
            edge_case = {
                'type': 'slow_processing',
                'ticket_id': ticket['id'],
                'description': f'Processing time exceeded 1 second ({result["processing_time_ms"]}ms)',
                'channel': ticket['channel']
            }

        if edge_case:
            self.edge_cases.append(edge_case)

    def _calculate_final_metrics(self):
        """Calculate final aggregate metrics."""
        if self.metrics['successful'] > 0:
            total_time = sum(r['processing_time_ms'] for r in self.results if r['success'])
            self.metrics['avg_processing_time_ms'] = total_time / self.metrics['successful']

        # Calculate escalation rate
        self.metrics['escalation_rate'] = (
            self.metrics['escalated'] / self.metrics['total_tickets'] * 100
            if self.metrics['total_tickets'] > 0 else 0
        )

        # Calculate resolution rate
        self.metrics['resolution_rate'] = (
            self.metrics['resolved_by_ai'] / self.metrics['total_tickets'] * 100
            if self.metrics['total_tickets'] > 0 else 0
        )

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print()

        print(f"Total Tickets Tested: {self.metrics['total_tickets']}")
        print(f"Successful: {self.metrics['successful']}")
        print(f"Failed: {self.metrics['failed']}")
        print(f"Escalated: {self.metrics['escalated']} ({self.metrics['escalation_rate']:.1f}%)")
        print(f"Resolved by AI: {self.metrics['resolved_by_ai']} ({self.metrics['resolution_rate']:.1f}%)")
        print(f"Avg Processing Time: {self.metrics['avg_processing_time_ms']:.0f}ms")
        print()

        print("BY CHANNEL:")
        print("-" * 80)
        for channel, stats in self.metrics['by_channel'].items():
            if stats['total'] > 0:
                esc_rate = stats['escalated'] / stats['total'] * 100
                print(f"  {channel.upper()}: {stats['total']} tickets, {stats['escalated']} escalated ({esc_rate:.1f}%)")
        print()

        print("BY CATEGORY:")
        print("-" * 80)
        for category, stats in sorted(self.metrics['by_category'].items()):
            if stats['total'] > 0:
                esc_rate = stats['escalated'] / stats['total'] * 100
                print(f"  {category}: {stats['total']} tickets, {stats['escalated']} escalated ({esc_rate:.1f}%)")
        print()

        print(f"EDGE CASES IDENTIFIED: {len(self.edge_cases)}")
        print("-" * 80)
        edge_case_types = {}
        for ec in self.edge_cases:
            ec_type = ec['type']
            edge_case_types[ec_type] = edge_case_types.get(ec_type, 0) + 1

        for ec_type, count in sorted(edge_case_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {ec_type}: {count}")
        print()

        # Assessment
        print("ASSESSMENT:")
        print("-" * 80)

        target_escalation = 25.0
        if self.metrics['escalation_rate'] <= target_escalation:
            print(f"✓ Escalation rate ({self.metrics['escalation_rate']:.1f}%) is within target (<{target_escalation}%)")
        else:
            print(f"✗ Escalation rate ({self.metrics['escalation_rate']:.1f}%) exceeds target (<{target_escalation}%)")

        target_processing = 3000  # 3 seconds
        if self.metrics['avg_processing_time_ms'] <= target_processing:
            print(f"✓ Avg processing time ({self.metrics['avg_processing_time_ms']:.0f}ms) is within target (<{target_processing}ms)")
        else:
            print(f"✗ Avg processing time ({self.metrics['avg_processing_time_ms']:.0f}ms) exceeds target (<{target_processing}ms)")

        if len(self.edge_cases) >= 20:
            print(f"✓ Identified {len(self.edge_cases)} edge cases (target: ≥20)")
        else:
            print(f"✗ Only identified {len(self.edge_cases)} edge cases (target: ≥20)")

        print()

    def save_results(self):
        """Save test results to file."""
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'specs')
        os.makedirs(output_dir, exist_ok=True)

        # Save detailed results
        results_file = os.path.join(output_dir, 'prototype-test-results.json')
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'metrics': self.metrics,
                'results': self.results,
                'edge_cases': self.edge_cases
            }, f, indent=2)

        print(f"Results saved to: {results_file}")

        # Save edge cases document
        edge_cases_file = os.path.join(output_dir, 'edge-cases.md')
        self._save_edge_cases_document(edge_cases_file)
        print(f"Edge cases documented in: {edge_cases_file}")

    def _save_edge_cases_document(self, filepath: str):
        """Save edge cases as markdown document."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# Edge Cases Identified During Prototype Testing\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write(f"**Total Edge Cases:** {len(self.edge_cases)}\n\n")
            f.write("---\n\n")

            # Group by type
            by_type = {}
            for ec in self.edge_cases:
                ec_type = ec['type']
                if ec_type not in by_type:
                    by_type[ec_type] = []
                by_type[ec_type].append(ec)

            for ec_type, cases in sorted(by_type.items()):
                f.write(f"## {ec_type.replace('_', ' ').title()} ({len(cases)} cases)\n\n")

                for i, case in enumerate(cases, 1):
                    f.write(f"### Case {i}: {case['ticket_id']}\n\n")
                    f.write(f"**Description:** {case['description']}\n\n")

                    for key, value in case.items():
                        if key not in ['type', 'ticket_id', 'description']:
                            f.write(f"- **{key}:** {value}\n")

                    f.write("\n")

                f.write("---\n\n")


# Run tests
if __name__ == "__main__":
    tester = PrototypeTester()
    tester.test_all_tickets()
