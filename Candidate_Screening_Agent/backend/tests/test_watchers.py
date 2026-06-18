import asyncio
from unittest.mock import MagicMock, patch

import pytest

from watchers.base_watcher import BaseWatcher
from watchers.gmail_watcher import GmailApplicationWatcher


@pytest.mark.asyncio
async def test_gmail_watcher_skips_processed_ids():
    with patch("watchers.gmail_watcher.build"), patch("watchers.gmail_watcher.Credentials"):
        watcher = GmailApplicationWatcher.__new__(GmailApplicationWatcher)
        watcher.processed_ids = {"msg_already_done"}
        watcher.logger = MagicMock()

        mock_messages = [{"id": "msg_already_done"}, {"id": "msg_new"}]
        watcher.service = MagicMock()
        watcher.service.users().messages().list().execute.return_value = {"messages": mock_messages}

        result = await watcher.check_for_updates()
        assert all(m["id"] != "msg_already_done" for m in result)
        assert len(result) == 1


@pytest.mark.asyncio
async def test_gmail_watcher_skips_no_pdf_attachment():
    with patch("watchers.gmail_watcher.build"), patch("watchers.gmail_watcher.Credentials"):
        watcher = GmailApplicationWatcher.__new__(GmailApplicationWatcher)
        watcher.processed_ids = set()
        watcher.logger = MagicMock()
        watcher.redis = MagicMock()
        watcher.processed_ids_file = MagicMock()
        watcher.processed_ids_file.exists.return_value = False

        msg_no_pdf = {
            "id": "msg_no_pdf",
            "payload": {
                "headers": [
                    {"name": "From", "value": "applicant@test.com"},
                    {"name": "Subject", "value": "Application"},
                ],
                "parts": [{"filename": "cover_letter.txt", "body": {"data": ""}}],
            },
            "snippet": "Please find my application",
        }
        watcher.service = MagicMock()
        watcher.service.users().messages().get().execute.return_value = msg_no_pdf

        with patch.object(watcher, "_save_processed_ids"):
            await watcher.handle_item({"id": "msg_no_pdf"})

        watcher.redis.lpush.assert_not_called()


@pytest.mark.asyncio
async def test_base_watcher_continues_on_error():
    class TestWatcher(BaseWatcher):
        call_count = 0

        async def check_for_updates(self):
            self.call_count += 1
            if self.call_count == 1:
                raise ConnectionError("Simulated network error")
            return []

        async def handle_item(self, item):
            pass

    watcher = TestWatcher(check_interval=0)
    watcher.logger = MagicMock()

    async def run_briefly():
        task = asyncio.create_task(watcher.run())
        await asyncio.sleep(0.05)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    await run_briefly()
    watcher.logger.error.assert_called()
    assert watcher.call_count >= 2
