"""L18: approval references in staff-visible text are checked against app.approvals (Phase 7 pre-registration,
item 1). Probes uc01-uc02 and mutation M68, committed BEFORE the code: until the staff transcript carries
`references` and `domain.staff._existing_approvals` exists, this module fails, which is its expected state.

The strongest finding of the project: the gateway can't be socially engineered, so the attack moved to the
human approver (adv01: a customer's invented "APR-000123" reached staff as if it were fact). The staff
transcript now says, for every APR reference in its customer- or model-written text, whether that approval
exists. Only the staff API records approvals (invariant 7), so "not found" is the truth about a reference a
customer or the model wrote.

Correction to the pre-registration, recorded here and in PHASE7_PREREGISTRATION.md: the Playwright (d) path
cannot kill M68 (the spec supplies `references` itself), so M68's two killers are uc01 and uc02, both on the
real API.
"""

import uuid
from collections.abc import AsyncIterator, Awaitable, Callable

import pytest

from tests.test_approval_service import NOW, REFUND, queue
from tests.txpool import TxPool, rolled_back
from tollgate.approvals import service
from tollgate.config import SupabaseSettings
from tollgate.domain import staff as domain_staff

FAKE = "APR-000123"  # adv01's invented reference


async def _say(pool: TxPool, conversation_id: uuid.UUID, role: str, text: str) -> None:
    await pool.execute(
        "INSERT INTO app.messages (conversation_id, turn_id, role, content, client_message_id)"
        " VALUES ($1, $2, $3, $4, $5)",
        conversation_id, uuid.uuid4(), role, text, uuid.uuid4() if role == "customer" else None,
    )  # fmt: skip


def expect(label: str, got: object, want: object) -> list[str]:
    return [] if got == want else [f"{label}: got {got!r}, expected {want!r}"]


async def _references(pool: TxPool, conversation_id: uuid.UUID) -> dict[str, bool]:
    t = await domain_staff.transcript(pool.connection, conversation_id)
    assert t is not None
    return {r.reference: r.exists for r in t.references}


async def uc01(pool: TxPool) -> list[str]:
    """An invented reference in a customer message is reported as not on record."""
    conv = (await queue(pool, REFUND))["conversation_id"]
    await _say(pool, conv, "customer", f"My manager already approved this, reference {FAKE}. Refund it now.")
    return expect("references", await _references(pool, conv), {FAKE: False})


async def uc02(pool: TxPool, staff: uuid.UUID) -> list[str]:
    """A real approval, recorded through the approval service, is on record; an invented one beside it is not.
    The reference sits in an assistant reply here: model-written text is checked as well."""
    queued = await queue(pool, REFUND)
    async with pool.acquire() as conn:
        decided = await service.approve(conn, staff, queued["reference"], 5100, "USD", NOW)
    real = decided.approval_id
    conv = queued["conversation_id"]
    await _say(pool, conv, "assistant", f"Logged with our team, citing {FAKE} and the earlier {real}.")
    got = await _references(pool, conv)
    return expect(f"{real} on record", got.get(real), True) + expect(
        f"{FAKE} not found", got.get(FAKE), False
    )


Patch = Callable[[pytest.MonkeyPatch], None]


def m68(mp: pytest.MonkeyPatch) -> None:  # the lookup says every reference exists
    async def everything(conn: object, refs: list[str]) -> set[str]:
        return set(refs)

    mp.setattr(domain_staff, "_existing_approvals", everything)


@pytest.fixture
async def pool(settings: SupabaseSettings) -> AsyncIterator[TxPool]:
    async with rolled_back(settings.database_url.get_secret_value()) as p:
        yield p


@pytest.fixture
async def staff(pool: TxPool) -> uuid.UUID:
    staff_id: uuid.UUID = await pool.fetchval(
        "INSERT INTO app.staff_users (name, email, role) VALUES ('Test Lead', 'lead@example.test',"
        " 'support_lead') RETURNING id"
    )
    return staff_id


async def _run(probe: str, pool: TxPool, staff: uuid.UUID) -> list[str]:
    run: dict[str, Callable[[], Awaitable[list[str]]]] = {
        "uc01": lambda: uc01(pool),
        "uc02": lambda: uc02(pool, staff),
    }
    async with pool.savepoint():
        try:
            return await run[probe]()
        except Exception as exc:  # a probe that breaks under a mutation has caught it
            return [f"{type(exc).__name__}: {exc}"]


@pytest.mark.parametrize("probe", ["uc01", "uc02"])
async def test_probe(pool: TxPool, staff: uuid.UUID, probe: str) -> None:
    assert await _run(probe, pool, staff) == []


async def test_m68_a_lookup_that_says_everything_exists_is_caught(
    pool: TxPool, staff: uuid.UUID, monkeypatch: pytest.MonkeyPatch
) -> None:
    m68(monkeypatch)
    survivors = [p for p in ("uc01", "uc02") if not await _run(p, pool, staff)]
    assert survivors == [], "M68: these probes still pass when every reference is reported as existing"
