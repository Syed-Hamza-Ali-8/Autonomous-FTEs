import asyncio
import json
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, AsyncOpenAI as AgentsAsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled

load_dotenv()
set_tracing_disabled(disabled=True)  # Required — no OpenAI key for tracing

logger = logging.getLogger(__name__)


def get_groq_client() -> AsyncOpenAI:
    """Create Groq client instance."""
    return AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1"),
    )


def get_groq_model(model_name: str = None):
    """
    Factory function to create Groq model instance.
    Groq is OpenAI-API-compatible. Only base_url and api_key differ from OpenAI.
    """
    if model_name is None:
        model_name = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    client = get_groq_client()
    return OpenAIChatCompletionsModel(
        model=model_name,
        openai_client=client,
    )


async def score_candidate(cv_text: str, rubric_path: str) -> dict:
    """
    Score a candidate's CV using Groq. Uses rubric if available, otherwise uses default criteria.

    Args:
        cv_text: Extracted text from candidate's CV
        rubric_path: Path to the job rubric markdown file (optional)

    Returns:
        dict with scoring results including total_score, must_haves_met,
        recommendation, strengths, weaknesses, etc.
    """
    # Try to load rubric, use default if not found
    rubric_content = ""
    rubric_section = ""
    try:
        if rubric_path and Path(rubric_path).exists():
            rubric_content = Path(rubric_path).read_text()
            rubric_section = f"RUBRIC:\n{rubric_content}\n\n"
    except Exception:
        pass

    prompt = f"""You are an expert technical recruiter. Score this CV based on standard hiring criteria.

{rubric_section}CV:
{cv_text}

Scoring criteria (if no rubric provided):
- Skills (40 pts): Technical skills, tools, languages relevant to the role
- Experience (25 pts): Work experience, seniority, achievements
- Projects (20 pts): Portfolio, side projects, contributions
- Communication (15 pts): Clarity, articulation, written communication

Return ONLY valid JSON with the word JSON in your response, no code blocks, no prose, no explanations. Just the raw JSON object.

Required fields:
- total_score (integer 0-100)
- must_haves_met (boolean)
- disqualification_reason (string or null)
- skill_score (integer)
- experience_score (integer)
- project_score (integer)
- communication_score (integer)
- bonuses_applied (array of strings)
- red_flags (array of strings)
- strengths (array of strings)
- weaknesses (array of strings)
- recommendation (string: "advance" | "reject" | "review")
- confidence (string: "high" | "medium" | "low")
- summary (string)

Ensure all scores add up correctly."""

    client = get_groq_client()
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    for attempt in range(2):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content.strip()
            # Strip markdown code blocks if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                if content.startswith("json"):
                    content = content[4:].strip()
            data = json.loads(content)
            logger.info(f"Candidate scored: {data.get('total_score')}/100")
            return data
        except json.JSONDecodeError as e:
            if attempt == 0:
                logger.warning(f"JSON parse error, retrying: {e}")
                prompt += "\n\nCRITICAL: Return ONLY raw JSON. No markdown code blocks. No ``` markers. Just the JSON object starting with {{."
            else:
                logger.error(f"Failed to parse JSON after 2 attempts: {e}")
                raise Exception(f"Failed to parse JSON from model after 2 attempts: {e}")


async def generate_screening_questions(cv_text: str, rubric_path: str) -> list[str]:
    """
    Generate 5 personalized screening questions using Groq.

    Args:
        cv_text: Extracted text from candidate's CV
        rubric_path: Path to the job rubric markdown file (optional)

    Returns:
        list of exactly 5 screening questions
    """
    rubric_content = ""
    rubric_section = ""
    try:
        if rubric_path and Path(rubric_path).exists():
            rubric_content = Path(rubric_path).read_text()
            rubric_section = f"RUBRIC:\n{rubric_content}\n\n"
    except Exception:
        pass

    prompt = f"""You are an expert technical recruiter. Generate exactly 5 personalized screening questions for this candidate.

{rubric_section}CV:
{cv_text}

Requirements:
- Reference specific items from the candidate's CV
- Ask about technical depth, not just surface knowledge
- Include at least one behavioral question
- Keep questions concise (1-2 sentences each)

Return ONLY a JSON array of 5 strings. No markdown, no code blocks, no prose.

Example format:
["Question 1 here?", "Question 2 here?", "Question 3 here?", "Question 4 here?", "Question 5 here?"]"""

    client = get_groq_client()
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    for attempt in range(2):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                if content.startswith("json"):
                    content = content[4:].strip()
            data = json.loads(content)
            if isinstance(data, list) and len(data) == 5:
                return data
            # If wrapped in object, try to extract array
            if isinstance(data, dict):
                for v in data.values():
                    if isinstance(v, list) and len(v) >= 3:
                        return v[:5]
            raise ValueError(f"Unexpected format: {type(data)}")
        except (json.JSONDecodeError, ValueError) as e:
            if attempt == 0:
                logger.warning(f"Question parse error, retrying: {e}")
                prompt += "\n\nCRITICAL: Return ONLY a JSON array like [\"q1\", \"q2\", \"q3\", \"q4\", \"q5\"]."
            else:
                logger.error(f"Failed to parse questions: {e}")
                return [
                    "Describe your most challenging technical project and how you handled it?",
                    "How do you approach learning new technologies quickly?",
                    "Tell me about a time you disagreed with a technical decision. How did you resolve it?",
                    "What is your experience with the key requirements in our rubric?",
                    "How do you ensure code quality in your projects?"
                ]


async def analyze_reply(questions: list[str], reply_text: str, original_score: dict) -> dict:
    """
    Analyze candidate's reply to screening questions using Groq.

    Args:
        questions: List of screening questions that were sent
        reply_text: Candidate's reply text
        original_score: Original scoring dict from score_candidate()

    Returns:
        dict with reply analysis including reply_score_delta, final_score,
        answer_quality, notable_answers, updated_recommendation, brief_summary
    """
    questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])

    prompt = f"""You are an expert technical recruiter. Analyze the candidate's replies to screening questions.

ORIGINAL SCORE: {original_score.get('total_score', 0)}

QUESTIONS:
{questions_text}

CANDIDATE REPLY:
{reply_text}

Evaluate:
- Answer quality (depth, clarity, relevance)
- Technical knowledge demonstrated
- Communication skills
- Red flags or concerns

Return ONLY valid JSON with the word JSON in your response, no code blocks, no prose.

Required fields:
- reply_score_delta (integer -20 to +20, adjustment to original score)
- final_score (integer 0-100, original_score + reply_score_delta)
- answer_quality (string: "high" | "medium" | "low")
- notable_answers (array of strings, key insights from answers)
- updated_recommendation (string: "advance" | "reject" | "review")
- brief_summary (string, 1-2 sentences summarizing the reply quality)"""

    client = get_groq_client()
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    for attempt in range(2):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                if content.startswith("json"):
                    content = content[4:].strip()
            data = json.loads(content)
            return data
        except json.JSONDecodeError as e:
            if attempt == 0:
                logger.warning(f"Reply analysis parse error, retrying: {e}")
                prompt += "\n\nCRITICAL: Return ONLY raw JSON. No markdown, no code blocks."
            else:
                logger.error(f"Failed to parse reply analysis: {e}")
                return {
                    "reply_score_delta": 0,
                    "final_score": original_score.get("total_score", 50),
                    "answer_quality": "medium",
                    "notable_answers": [],
                    "updated_recommendation": "review",
                    "brief_summary": "Unable to analyze reply quality."
                }
