import json
from unittest.mock import AsyncMock, patch

import pytest

from screening_agent import analyze_reply, generate_screening_questions, score_candidate


class MockRunResult:
    def __init__(self, output: str):
        self.final_output = output


@pytest.mark.asyncio
async def test_score_candidate_returns_valid_dict(sample_cv_text, sample_rubric_path, sample_score):
    with patch("screening_agent.Runner.run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = MockRunResult(json.dumps(sample_score))
        result = await score_candidate(sample_cv_text, sample_rubric_path)

    assert isinstance(result, dict)
    assert result["total_score"] == 82
    assert result["must_haves_met"] is True
    assert result["recommendation"] == "advance"
    assert "strengths" in result
    assert "red_flags" in result


@pytest.mark.asyncio
async def test_score_candidate_retries_on_invalid_json(sample_cv_text, sample_rubric_path, sample_score):
    with patch("screening_agent.Runner.run", new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = [
            MockRunResult("```json\nNot valid JSON```"),
            MockRunResult(json.dumps(sample_score)),
        ]
        result = await score_candidate(sample_cv_text, sample_rubric_path)

    assert mock_run.call_count == 2
    assert result["total_score"] == 82


@pytest.mark.asyncio
async def test_score_candidate_raises_after_two_failures(sample_cv_text, sample_rubric_path):
    with patch("screening_agent.Runner.run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = MockRunResult("This is not JSON at all")
        with pytest.raises(Exception):
            await score_candidate(sample_cv_text, sample_rubric_path)


@pytest.mark.asyncio
async def test_score_candidate_disqualified(sample_cv_text, sample_rubric_path, disqualified_score):
    with patch("screening_agent.Runner.run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = MockRunResult(json.dumps(disqualified_score))
        result = await score_candidate(sample_cv_text, sample_rubric_path)

    assert result["must_haves_met"] is False
    assert result["recommendation"] == "reject"
    assert result["disqualification_reason"] is not None


@pytest.mark.asyncio
async def test_generate_questions_returns_five(sample_cv_text, sample_rubric_path, sample_questions):
    with patch("screening_agent.Runner.run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = MockRunResult(json.dumps(sample_questions))
        result = await generate_screening_questions(sample_cv_text, sample_rubric_path)

    assert isinstance(result, list)
    assert len(result) == 5
    assert all(isinstance(q, str) for q in result)


@pytest.mark.asyncio
async def test_generate_questions_uses_groq_model(sample_cv_text, sample_rubric_path, sample_questions):
    with patch("screening_agent.Runner.run", new_callable=AsyncMock) as mock_run:
        with patch("screening_agent.get_groq_model", return_value="grok-3-mini") as mock_model:
            mock_run.return_value = MockRunResult(json.dumps(sample_questions))
            await generate_screening_questions(sample_cv_text, sample_rubric_path)
            mock_model.assert_called()


@pytest.mark.asyncio
async def test_analyze_reply_returns_valid_dict(sample_questions, sample_score):
    reply_text = "Great questions! Here are my answers: ..."
    mock_analysis = {
        "reply_score_delta": 6,
        "final_score": 88,
        "answer_quality": "high",
        "notable_answers": ["Excellent answer on Q1 about scaling"],
        "updated_recommendation": "advance",
        "brief_summary": "Candidate answered all questions with depth and clarity.",
    }
    with patch("screening_agent.Runner.run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = MockRunResult(json.dumps(mock_analysis))
        result = await analyze_reply(sample_questions, reply_text, sample_score)

    assert result["final_score"] == 88
    assert result["answer_quality"] == "high"
    assert result["updated_recommendation"] == "advance"
    assert "brief_summary" in result


@pytest.mark.asyncio
async def test_analyze_reply_score_delta_applied(sample_questions, sample_score):
    mock_analysis = {
        "reply_score_delta": -5,
        "final_score": 77,
        "answer_quality": "medium",
        "notable_answers": [],
        "updated_recommendation": "review",
        "brief_summary": "Answers were vague and lacked depth.",
    }
    with patch("screening_agent.Runner.run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = MockRunResult(json.dumps(mock_analysis))
        result = await analyze_reply(sample_questions, "Short vague answers", sample_score)

    assert result["reply_score_delta"] == -5
    assert result["updated_recommendation"] == "review"
