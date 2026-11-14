"""af06, as narrowed by the owner (DECISIONS I9): no tool can reach or name approval state.

(a) STRUCTURAL, writes: no module a tool imports, directly or transitively, contains SQL that writes approval
    state (updates or deletes action requests, or any write to an approvals table). Creating a request is
    queueing, not deciding: the database refuses a request created already decided
    (`action_requests_born_undecided`). Extended by amendment A2-P4 (tightened, nothing narrowed):
    (a1) no tool-reachable INSERT, UPDATE, DELETE or MERGE of `app.approvals`;
    (a2) no tool-reachable UPDATE of `action_requests` that sets `status` to approved or executed, or to any
         value that isn't a literal non-approving status (a parameter could be 'approved').
    Identifiers match quoted or unquoted, with or without the `app.` schema, across lines.
(b) STRUCTURAL, parameters: no tool parameter maps to an approval column. A write tool's parameters are
    exactly the fields of the gateway's strict argument model (asserted), so the mapping is exact; none of
    those fields may be an approval column. Read tools take no part in a write path (checked by (a)).
(c) SECONDARY tripwire: tool and parameter names about approving, rejecting, approvals, overrides, status or
    decisions, with an explicit allowlist that says why each exception is safe.
"""

import ast
import re
from pathlib import Path
from typing import Any

PACKAGE_NAME = "tollgate"
# Tables whose rows ARE approval state, and the action-request columns that record a decision.
APPROVAL_TABLES = ("approvals",)  # created in Phase 4; any column of it counts
DECISION_COLUMNS = ("status", "decision", "reasons", "decided_at")
REFERENCE_COLUMNS = ("action_request_id", "approval_id")  # a parameter naming a request or approval


def _table(name: str) -> str:
    """`app.name`, `"app"."name"`, `app."name"` or bare `name` (search_path), never a longer identifier."""
    return rf'(?:"?app"?\s*\.\s*)?"?{name}"?(?![\w"])'


# (a1) any write to the decisions log
APPROVALS_WRITE = re.compile(
    rf"\b(?:INSERT\s+INTO|UPDATE|DELETE\s+FROM|MERGE\s+INTO)\s+{_table('approvals')}", re.IGNORECASE
)
# (a) any update or delete of an action request (creating one is queueing, not deciding)
REQUEST_WRITE = re.compile(rf"\b(?:UPDATE|DELETE\s+FROM)\s+{_table('action_requests')}", re.IGNORECASE)
# (a2) the dangerous direction, named explicitly: status set to approved/executed, or to anything not a
# literal non-approving status
DECIDING_UPDATE = re.compile(
    rf"\bUPDATE\s+{_table('action_requests')}[^;]*?\bSET\b[^;]*?(?<![\w.])\"?status\"?\s*="
    r"(?!\s*'(?:pending_approval|rejected|expired)')",
    re.IGNORECASE | re.DOTALL,
)
APPROVAL_WRITE = (APPROVALS_WRITE, REQUEST_WRITE)  # check (a), as before: either kind of write
TRIPWIRE_WORDS = ("approve", "reject", "approval", "override", "status", "decision", "decided")
TRIPWIRE_ALLOWLIST = {
    ("get_my_orders", "status"): (
        "order-status filter on a READ tool: it flows only into the SELECT in domain.orders.list_orders"
        " (app.orders.status); domain/orders.py writes nothing, and check (a) shows no tool reaches"
        " approval writes"
    ),
}


def _module_file(root: Path, module: str) -> Path | None:
    parts = module.split(".")
    if parts[0] != root.name:
        return None
    base = root.parent.joinpath(*parts)
    for candidate in (base.with_suffix(".py"), base / "__init__.py"):
        if candidate.exists():
            return candidate
    return None


def _imports(path: Path, root: Path) -> set[Path]:
    found: set[Path] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module] + [f"{node.module}.{a.name}" for a in node.names]
        for name in names:
            if (target := _module_file(root, name)) is not None:
                found.add(target)
    return found


def import_closure(entries: list[Path], root: Path) -> set[Path]:
    seen: set[Path] = set()
    todo = list(entries)
    while todo:
        path = todo.pop()
        if path in seen:
            continue
        seen.add(path)
        todo += _imports(path, root) - seen
    return seen


def sql_strings(path: Path) -> list[str]:
    return [
        n.value
        for n in ast.walk(ast.parse(path.read_text()))
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
    ]


def writers(
    paths: set[Path] | list[Path], root: Path, patterns: tuple[re.Pattern[str], ...]
) -> dict[str, list[str]]:
    """module -> SQL fragments matching any of `patterns`, over the string constants of `paths`."""
    hits: dict[str, list[str]] = {}
    for path in sorted(paths):
        found = [m.group(0) for s in sql_strings(path) for p in patterns for m in p.finditer(s)]
        if found:
            hits[path.relative_to(root.parent).as_posix()] = found
    return hits


def approval_writers_reachable(tool_modules: list[Path], root: Path) -> dict[str, list[str]]:
    """(a): module -> approval-writing SQL fragments, over everything the tool modules import."""
    return writers(import_closure(tool_modules, root), root, APPROVAL_WRITE)


def approvals_log_writers_reachable(tool_modules: list[Path], root: Path) -> dict[str, list[str]]:
    """(a1): tool-reachable writes to the decisions log."""
    return writers(import_closure(tool_modules, root), root, (APPROVALS_WRITE,))


def deciding_updates_reachable(tool_modules: list[Path], root: Path) -> dict[str, list[str]]:
    """(a2): tool-reachable updates that could move a request into approved or executed."""
    return writers(import_closure(tool_modules, root), root, (DECIDING_UPDATE,))


def approval_columns(columns: dict[str, list[str]]) -> set[str]:
    """Approval columns from the live schema: every column of an approvals table, the action-request
    decision columns, and names that reference a request or approval."""
    out = set(REFERENCE_COLUMNS)
    for table in APPROVAL_TABLES:
        out |= set(columns.get(table, []))
    missing = set(DECISION_COLUMNS) - set(columns.get("action_requests", []))
    if missing:  # the list must not go stale silently
        raise AssertionError(f"action_requests no longer has decision columns {missing}")
    return out | set(DECISION_COLUMNS)


def field_names(model: Any) -> set[str]:
    """Every field name of a pydantic model, nested models included."""
    names: set[str] = set()
    for name, info in model.model_fields.items():
        names.add(name)
        ann = info.annotation
        if isinstance(ann, type) and hasattr(ann, "model_fields"):
            names |= field_names(ann)
    return names


def param_names(schema: object) -> set[str]:
    names: set[str] = set()
    if isinstance(schema, dict):
        for k, v in schema.items():
            if k == "properties" and isinstance(v, dict):
                names |= set(v)
            names |= param_names(v)
    elif isinstance(schema, list):
        for v in schema:
            names |= param_names(v)
    return names


def parameter_mapping_problems(
    write_tools: dict[str, Any], args_models: dict[str, Any], columns: set[str]
) -> list[str]:
    """(b): each write tool's parameters equal its gateway model's fields, and none is an approval column."""
    out = []
    for name, tool in write_tools.items():
        advertised, accepted = param_names(tool.params_json_schema), field_names(args_models[name])
        if advertised != accepted:
            out.append(f"{name}: advertised {sorted(advertised)} != gateway fields {sorted(accepted)}")
        out += [f"{name}({p}) maps to approval column {p}" for p in sorted(accepted & columns)]
    return out


def tripwire(tools: dict[str, Any]) -> list[str]:
    """(c): suspicious names, minus the documented allowlist."""
    hits = []
    for name, tool in tools.items():
        if any(w in name.lower() for w in TRIPWIRE_WORDS):
            hits.append(f"tool {name}")
        for p in sorted(param_names(tool.params_json_schema)):
            if any(w in p.lower() for w in TRIPWIRE_WORDS) and (name, p) not in TRIPWIRE_ALLOWLIST:
                hits.append(f"{name}({p})")
    return hits
