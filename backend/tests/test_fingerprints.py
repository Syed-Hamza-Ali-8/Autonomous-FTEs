"""system_fingerprint is recorded once per model call, and the stream reaches the SDK unchanged (12.4)."""

from types import SimpleNamespace
from typing import Any

from openai import AsyncOpenAI

from tollgate.llm import fingerprints


class FakeStream:
    def __init__(self, chunks: list[Any]) -> None:
        self._chunks = chunks
        self.response = SimpleNamespace(headers={"x-request-id": "req_1"})

    def __aiter__(self) -> Any:
        return self._gen()

    async def _gen(self) -> Any:
        for c in self._chunks:
            yield c


def client_returning(stream: FakeStream) -> AsyncOpenAI:
    client = AsyncOpenAI(api_key="test", base_url="http://127.0.0.1:9")

    async def create(*a: Any, **k: Any) -> Any:
        return stream

    setattr(client.chat.completions, "create", create)  # noqa: B010
    return fingerprints.instrument(client)


async def drain(client: AsyncOpenAI) -> tuple[list[Any], Any]:
    out = await client.chat.completions.create(model="m", messages=[], stream=True)
    return [c async for c in out], out


async def test_one_fingerprint_per_call_and_the_stream_is_unchanged() -> None:
    chunks = [SimpleNamespace(system_fingerprint=None), SimpleNamespace(system_fingerprint="fp_a"),
              SimpleNamespace(system_fingerprint="fp_a")]  # fmt: skip
    client = client_returning(FakeStream(chunks))
    seen: list[str] = []
    token = fingerprints.CURRENT.set(seen)
    try:
        got, stream = await drain(client)
        await drain(client)
    finally:
        fingerprints.CURRENT.reset(token)
    assert got == chunks  # every chunk, in order, untouched
    assert stream.response.headers["x-request-id"] == "req_1"  # the SDK reads this for the request id
    assert seen == ["fp_a", "fp_a"]  # one per call


async def test_a_call_without_a_fingerprint_is_visible_and_outside_a_turn_nothing_is_kept() -> None:
    client = client_returning(FakeStream([SimpleNamespace(system_fingerprint=None)]))
    seen: list[str] = []
    token = fingerprints.CURRENT.set(seen)
    try:
        await drain(client)
    finally:
        fingerprints.CURRENT.reset(token)
    assert seen == ["unreported"]
    await drain(client)  # no current turn: recorded nowhere, and no error
    assert seen == ["unreported"]
