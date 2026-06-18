from unittest.mock import MagicMock, patch

import pytest

from services.gmail_service import GmailService


@pytest.fixture
def gmail(monkeypatch):
    monkeypatch.setenv("GMAIL_CLIENT_ID", "fake-client-id")
    monkeypatch.setenv("GMAIL_CLIENT_SECRET", "fake-secret")
    monkeypatch.setenv("GMAIL_REFRESH_TOKEN", "fake-token")
    monkeypatch.setenv("DRY_RUN", "true")
    with patch("services.gmail_service.build"):
        return GmailService()


def test_send_email_dry_run_does_not_call_api(gmail):
    mock_service = MagicMock()
    gmail.service = mock_service
    result = gmail.send_email("test@test.com", "Subject", "Body")
    mock_service.users().messages().send.assert_not_called()
    assert isinstance(result, str)


def test_send_email_dry_run_returns_fake_id(gmail):
    result = gmail.send_email("test@test.com", "Subject", "Body")
    assert result is not None
    assert len(result) > 0


def test_send_screening_questions_formats_correctly(gmail):
    questions = [f"Question {i}" for i in range(1, 6)]
    with patch.object(gmail, "send_email", return_value="fake-id") as mock_send:
        gmail.send_screening_questions(
            to="candidate@test.com",
            candidate_name="John",
            job_title="Backend Engineer",
            questions=questions,
        )
    body = mock_send.call_args[0][2]
    for q in questions:
        assert q in body


def test_send_interview_invite_uses_correct_recipient(gmail):
    with patch.object(gmail, "send_email", return_value="fake-id") as mock_send:
        gmail.send_interview_invite("john@test.com", "John Doe", "Backend Engineer")
    assert mock_send.call_args[0][0] == "john@test.com"


def test_send_rejection_email_uses_correct_recipient(gmail):
    with patch.object(gmail, "send_email", return_value="fake-id") as mock_send:
        gmail.send_rejection_email(
            "john@test.com", "John", "Backend Engineer", "Missing Python experience"
        )
    assert mock_send.call_args[0][0] == "john@test.com"


def test_real_send_blocked_in_dry_run(gmail, monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    mock_service = MagicMock()
    gmail.service = mock_service
    gmail.send_email("to@test.com", "Subject", "Body")
    mock_service.users().messages().send.assert_not_called()
