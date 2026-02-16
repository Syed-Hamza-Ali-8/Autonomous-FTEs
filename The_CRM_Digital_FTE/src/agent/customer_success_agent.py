"""
Customer Success Agent - Production Implementation
Phase 2: Specialization

OpenAI Agents SDK implementation with function tools.
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..database.models import (
    Customer, Conversation, Message, Ticket, KnowledgeBase
)


class CustomerSuccessAgent:
    """
    Production Customer Success AI Agent using OpenAI Agents SDK.
    Handles customer inquiries across email, WhatsApp, and web form channels.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the agent.

        Args:
            db: Database session
        """
        self.db = db
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

        # Escalation thresholds
        self.sentiment_threshold = float(os.getenv("ESCALATION_SENTIMENT_THRESHOLD", "0.3"))
        self.kb_relevance_threshold = float(os.getenv("ESCALATION_KB_RELEVANCE_THRESHOLD", "0.5"))

        # System prompt
        self.system_prompt = self._build_system_prompt()

        # Function tools
        self.tools = self._define_tools()

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the agent."""
        return """You are a Customer Success AI agent for TechCorp, a SaaS company that provides TaskFlow Pro, a project management and collaboration platform.

Your role is to:
1. Help customers with questions about TaskFlow Pro
2. Search the knowledge base for relevant information
3. Create support tickets for tracking
4. Escalate complex issues to human agents when necessary
5. Provide excellent customer service across all channels (Email, WhatsApp, Web Form)

Guidelines:
- Always be helpful, professional, and empathetic
- Search the knowledge base before responding
- Create a ticket at the start of every conversation
- Escalate billing issues, sales inquiries, negative sentiment, and critical bugs
- Adapt your communication style to the channel (formal for email, casual for WhatsApp)
- Keep responses concise and actionable
- Include relevant links to help articles

When to escalate:
- Billing or refund requests
- Enterprise pricing inquiries
- Negative sentiment or frustrated customers
- Data loss or security issues
- When knowledge base search returns no relevant results
- When customer explicitly requests human support

Company Information:
- Product: TaskFlow Pro (project management & collaboration)
- Support Email: support@techcorp.com
- Help Center: help.techcorp.com
- Plans: Free, Starter ($12/user/month), Professional ($24/user/month), Enterprise (custom)
"""

    def _define_tools(self) -> List[Dict[str, Any]]:
        """Define function tools for the agent."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_knowledge_base",
                    "description": "Search product documentation for relevant information. Use this when the customer asks questions about product features, how to use something, or needs technical information.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query text"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results to return",
                                "default": 5
                            },
                            "category": {
                                "type": "string",
                                "description": "Optional category filter",
                                "enum": ["authentication", "billing", "features", "integrations", "mobile", "api", "general"]
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_ticket",
                    "description": "Create a support ticket for tracking. ALWAYS create a ticket at the start of every conversation. Include the source channel for proper tracking.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_id": {
                                "type": "string",
                                "description": "Customer UUID"
                            },
                            "issue": {
                                "type": "string",
                                "description": "Brief description of the issue"
                            },
                            "priority": {
                                "type": "string",
                                "description": "Ticket priority",
                                "enum": ["low", "medium", "high"]
                            },
                            "channel": {
                                "type": "string",
                                "description": "Source channel",
                                "enum": ["email", "whatsapp", "web_form"]
                            },
                            "category": {
                                "type": "string",
                                "description": "Optional ticket category",
                                "enum": ["general", "technical", "billing", "feedback", "bug_report"]
                            }
                        },
                        "required": ["customer_id", "issue", "priority", "channel"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_customer_history",
                    "description": "Get customer's complete interaction history across ALL channels. Use this to understand context from previous conversations, even if they happened on a different channel.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_id": {
                                "type": "string",
                                "description": "Customer UUID"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of messages to retrieve",
                                "default": 20
                            }
                        },
                        "required": ["customer_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "escalate_to_human",
                    "description": "Escalate conversation to human support. Use this when: customer asks about pricing or refunds, customer sentiment is negative, you cannot find relevant information, or customer explicitly requests human help.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticket_id": {
                                "type": "string",
                                "description": "Ticket UUID"
                            },
                            "reason": {
                                "type": "string",
                                "description": "Escalation reason",
                                "enum": [
                                    "pricing_inquiry",
                                    "refund_request",
                                    "legal_mention",
                                    "negative_sentiment",
                                    "profanity_detected",
                                    "knowledge_search_failed",
                                    "explicit_human_request"
                                ]
                            },
                            "urgency": {
                                "type": "string",
                                "description": "Escalation urgency",
                                "enum": ["low", "normal", "high", "critical"],
                                "default": "normal"
                            },
                            "notes": {
                                "type": "string",
                                "description": "Additional notes for human agent"
                            }
                        },
                        "required": ["ticket_id", "reason"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "send_response",
                    "description": "Send response to customer via their preferred channel. The response will be automatically formatted for the channel (Email: formal with greeting/signature, WhatsApp: concise and conversational, Web: semi-formal).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticket_id": {
                                "type": "string",
                                "description": "Ticket UUID"
                            },
                            "message": {
                                "type": "string",
                                "description": "Response message (will be formatted for channel)"
                            },
                            "channel": {
                                "type": "string",
                                "description": "Target channel",
                                "enum": ["email", "whatsapp", "web_form"]
                            },
                            "include_ticket_reference": {
                                "type": "boolean",
                                "description": "Whether to include ticket reference in response",
                                "default": True
                            }
                        },
                        "required": ["ticket_id", "message", "channel"]
                    }
                }
            }
        ]

    async def process_message(
        self,
        customer_id: UUID,
        conversation_id: UUID,
        message_content: str,
        channel: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process incoming customer message.

        Args:
            customer_id: Customer UUID
            conversation_id: Conversation UUID
            message_content: Message content
            channel: Channel (email, whatsapp, web_form)
            metadata: Optional metadata

        Returns:
            Processing result with response and actions taken
        """
        start_time = datetime.now()

        # Store customer message
        customer_message = Message(
            conversation_id=conversation_id,
            role="customer",
            content=message_content,
            channel=channel,
            metadata=metadata or {}
        )
        self.db.add(customer_message)
        await self.db.flush()

        # Build conversation history
        conversation_history = await self._build_conversation_history(conversation_id)

        # Call OpenAI with function tools
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    *conversation_history,
                    {"role": "user", "content": message_content}
                ],
                tools=self.tools,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=1000
            )

            # Process response and tool calls
            result = await self._process_response(
                response,
                customer_id,
                conversation_id,
                channel
            )

            # Store agent response
            if result.get("response"):
                agent_message = Message(
                    conversation_id=conversation_id,
                    role="agent",
                    content=result["response"],
                    channel=channel,
                    metadata={"tool_calls": result.get("tool_calls", [])}
                )
                self.db.add(agent_message)

            await self.db.commit()

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return {
                "success": True,
                "response": result.get("response"),
                "tool_calls": result.get("tool_calls", []),
                "escalated": result.get("escalated", False),
                "processing_time_ms": processing_time
            }

        except Exception as e:
            await self.db.rollback()
            return {
                "success": False,
                "error": str(e),
                "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000
            }

    async def _build_conversation_history(
        self,
        conversation_id: UUID,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """Build conversation history for context."""
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.timestamp.desc())
            .limit(limit)
        )
        messages = result.scalars().all()

        # Reverse to get chronological order
        messages = list(reversed(messages))

        history = []
        for msg in messages:
            history.append({
                "role": msg.role if msg.role != "agent" else "assistant",
                "content": msg.content
            })

        return history

    async def _process_response(
        self,
        response: Any,
        customer_id: UUID,
        conversation_id: UUID,
        channel: str
    ) -> Dict[str, Any]:
        """Process OpenAI response and execute tool calls."""
        message = response.choices[0].message
        tool_calls = message.tool_calls or []

        result = {
            "response": message.content,
            "tool_calls": [],
            "escalated": False
        }

        # Execute tool calls
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            tool_result = await self._execute_tool(
                function_name,
                function_args,
                customer_id,
                conversation_id,
                channel
            )

            result["tool_calls"].append({
                "function": function_name,
                "arguments": function_args,
                "result": tool_result
            })

            # Check if escalated
            if function_name == "escalate_to_human":
                result["escalated"] = True

        return result

    async def _execute_tool(
        self,
        function_name: str,
        arguments: Dict[str, Any],
        customer_id: UUID,
        conversation_id: UUID,
        channel: str
    ) -> Any:
        """Execute a function tool."""
        if function_name == "search_knowledge_base":
            return await self._search_knowledge_base(**arguments)
        elif function_name == "create_ticket":
            return await self._create_ticket(conversation_id=conversation_id, **arguments)
        elif function_name == "get_customer_history":
            return await self._get_customer_history(**arguments)
        elif function_name == "escalate_to_human":
            return await self._escalate_to_human(**arguments)
        elif function_name == "send_response":
            return await self._send_response(**arguments)
        else:
            return {"error": f"Unknown function: {function_name}"}

    async def _search_knowledge_base(
        self,
        query: str,
        max_results: int = 5,
        category: Optional[str] = None
    ) -> str:
        """Search knowledge base using semantic search."""
        # Generate embedding for query
        embedding_response = await self.client.embeddings.create(
            model=self.embedding_model,
            input=query
        )
        query_embedding = embedding_response.data[0].embedding

        # Search using pgvector
        # Note: This uses raw SQL for vector similarity search
        sql = """
            SELECT id, title, content, category, url,
                   1 - (embedding <=> :query_embedding::vector) as similarity
            FROM knowledge_base
            WHERE (:category IS NULL OR category = :category)
            ORDER BY embedding <=> :query_embedding::vector
            LIMIT :max_results
        """

        result = await self.db.execute(
            sql,
            {
                "query_embedding": str(query_embedding),
                "category": category,
                "max_results": max_results
            }
        )
        articles = result.fetchall()

        if not articles:
            return "No relevant articles found in the knowledge base."

        # Format results
        formatted_results = []
        for article in articles:
            formatted_results.append(
                f"**{article.title}** (relevance: {article.similarity:.2f})\n"
                f"{article.content[:300]}...\n"
                f"Learn more: {article.url}\n"
            )

        return "\n---\n\n".join(formatted_results)

    async def _create_ticket(
        self,
        customer_id: str,
        conversation_id: UUID,
        issue: str,
        priority: str,
        channel: str,
        category: str = "general"
    ) -> str:
        """Create a support ticket."""
        ticket = Ticket(
            customer_id=UUID(customer_id),
            conversation_id=conversation_id,
            subject=issue[:500],
            status="open",
            priority=priority,
            category=category,
            channel=channel
        )
        self.db.add(ticket)
        await self.db.flush()

        return f"Ticket created: {ticket.id}"

    async def _get_customer_history(
        self,
        customer_id: str,
        limit: int = 20
    ) -> str:
        """Get customer's conversation history."""
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.customer_id == UUID(customer_id))
            .order_by(Conversation.created_at.desc())
            .limit(limit)
        )
        conversations = result.scalars().all()

        if not conversations:
            return "No previous conversations found for this customer."

        history = []
        for conv in conversations:
            # Get message count
            msg_count_result = await self.db.execute(
                select(func.count(Message.id))
                .where(Message.conversation_id == conv.id)
            )
            msg_count = msg_count_result.scalar()

            history.append(
                f"**{conv.channel.upper()} Conversation** - {conv.created_at.strftime('%Y-%m-%d')}\n"
                f"Status: {conv.status}\n"
                f"Messages: {msg_count}\n"
            )

        return "\n".join(history)

    async def _escalate_to_human(
        self,
        ticket_id: str,
        reason: str,
        urgency: str = "normal",
        notes: Optional[str] = None
    ) -> str:
        """Escalate ticket to human support."""
        # Update ticket status
        result = await self.db.execute(
            select(Ticket).where(Ticket.id == UUID(ticket_id))
        )
        ticket = result.scalar_one_or_none()

        if ticket:
            ticket.status = "escalated"
            ticket.escalated_at = datetime.now()
            ticket.escalation_reason = reason
            ticket.metadata["urgency"] = urgency
            if notes:
                ticket.metadata["escalation_notes"] = notes

            await self.db.flush()

        return f"Escalated to human support. Reference: {ticket_id}"

    async def _send_response(
        self,
        ticket_id: str,
        message: str,
        channel: str,
        include_ticket_reference: bool = True
    ) -> str:
        """Send response to customer (placeholder - actual sending handled by channel integrations)."""
        # This is a placeholder - actual message sending is handled by channel-specific integrations
        # The formatted response will be picked up by the channel integration layer
        return f"Response queued for sending via {channel}"
