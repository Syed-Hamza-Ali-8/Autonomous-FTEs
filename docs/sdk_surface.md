# OpenAI Agents SDK — verified surface

Every SDK symbol Tollgate depends on, verified by introspecting the **installed** package (Rule 0.1.2).
Re-verify and update this file whenever `openai-agents` is upgraded. Nothing here was written from memory.

- **Verified against:** `openai-agents==0.24.0` (`agents.__version__`), `openai==3.46.0`
- **Date:** 2026-11-07
- **Method:** `dir(agents)` and `inspect.signature(...)` via `uv run python` in `backend/`

## Provider wiring (Section 2.2)

| Symbol | Module | Verified signature | Tollgate use |
|---|---|---|---|
| `OpenAIChatCompletionsModel` | `agents.models.openai_chatcompletions` | `(model: str \| ChatModel, openai_client: AsyncOpenAI, should_replay_reasoning_content=None, strict_feature_validation: bool = False, buffer_streamed_tool_calls: bool = False)` | One instance per model slot (`MODEL_FAST`, `MODEL_STRONG`) on a Groq/Gemini `AsyncOpenAI` client |
| `set_default_openai_client` | `agents` | `(client: AsyncOpenAI, use_for_tracing: bool = True)` | If used, pass `use_for_tracing=False` |
| `set_default_openai_api` | `agents` | `(api: Literal['chat_completions', 'responses'])` | `'chat_completions'` (Groq/Gemini are Chat Completions compatible) |
| `set_tracing_disabled` | `agents.tracing` | `(disabled: bool)` | `True` at startup; tracing is local (`run_log`, `tool_calls`) |
| `RunConfig.tracing_disabled` | `agents.run_config` | field, `bool = False` | Also set `True` per run (belt and braces) |

## Agents, tools, handoffs

| Symbol | Verified signature (abridged to the params we use) | Tollgate use |
|---|---|---|
| `Agent` | `(name: str, handoff_description=None, tools=[], instructions: str \| Callable \| None = None, handoffs=[], model: str \| Model \| None = None, model_settings=ModelSettings(), input_guardrails=[], output_guardrails=[], output_type=None, hooks=None, tool_use_behavior='run_llm_again', reset_tool_choice=True)` | Agents in `agents_def/` |
| `function_tool` | `(func=None, *, name_override=None, description_override=None, docstring_style=None, use_docstring_info=True, failure_error_function=<default>, strict_mode=True, is_enabled=True, needs_approval=False, tool_input_guardrails=None, tool_output_guardrails=None, timeout=None, ...)` | Thin wrappers in `tools/` |
| `handoff` | `(agent, tool_name_override=None, tool_description_override=None, on_handoff=None, input_type=None, input_filter=None, nest_handoff_history=None, is_enabled=True)` | Phase 5 handoffs |
| `RunContextWrapper` | dataclass; public fields `context`, `usage`, `turn_input`, `tool_input` | Tools read `ctx.context` (the authenticated customer); first tool param |
| `ModelSettings` | `(temperature=None, tool_choice=None, parallel_tool_calls=None, max_tokens=None, include_usage=None, extra_body=None, retry=None, timeout=None, ...)` | Per-agent settings |

## Running and streaming

| Symbol | Verified signature | Tollgate use |
|---|---|---|
| `Runner.run` | `(starting_agent, input, *, context=None, max_turns=10, hooks=None, run_config=None, error_handlers=None, previous_response_id=None, auto_previous_response_id=False, conversation_id=None, session=None) -> RunResult` | Eval / non-streamed runs |
| `Runner.run_streamed` | `(starting_agent, input, context=None, max_turns=10, hooks=None, run_config=None, ..., session=None, *, error_handlers=None) -> RunResultStreaming` | `/v1/chat` |
| `RunResultStreaming.stream_events` | `(self) -> AsyncIterator[StreamEvent]` | SSE progress events |
| `StreamEvent` | `RawResponsesStreamEvent \| RunItemStreamEvent \| AgentUpdatedStreamEvent` | Map to SSE events; final text is buffered (DECISIONS C1) |
| `Usage` | dataclass: `requests, input_tokens, input_tokens_details, output_tokens, output_tokens_details, total_tokens, request_usage_entries` | Token accounting (`llm/budget.py`) |

## Guardrails

| Symbol | Verified signature | Tollgate use |
|---|---|---|
| `input_guardrail` | `(func=None, *, name=None, run_in_parallel=True)` | Possibly for `guardrails/input.py` (signal only) |
| `output_guardrail` | `(func=None, *, name=None)` | Not chosen yet for the claim check; see note 2 |
| `GuardrailFunctionOutput` | `(output_info: Any, tripwire_triggered: bool)` | |

## Exceptions (present in `agents`)
`AgentsException`, `MaxTurnsExceeded`, `ModelBehaviorError`, `UserError`, `InputGuardrailTripwireTriggered`, `OutputGuardrailTripwireTriggered`. Wrap them in Tollgate's typed errors (`errors.py`); no silent fallbacks.

## Notes and decisions
1. **`function_tool(needs_approval=...)` exists, but Tollgate does NOT use it.** The SDK's approval flow lives inside the agent run. Tollgate's approvals are a deterministic gateway decision persisted in `app.approvals` and settled only through the staff API (invariants 5–7). Using the SDK flag would put approval inside the model loop.
2. The claim check (Section 9.5, DECISIONS C1, C8) must run on the buffered final text before release. Whether it is implemented as an SDK `output_guardrail` or directly in `runner.py` gets decided in Phase 6, after reading the guardrail source. Either way the check itself is deterministic Python.
3. `max_turns` defaults to 10 on `Runner.run` / `run_streamed`. Set it explicitly. The handoff cap (DECISIONS D10) is enforced separately in the runner.
4. `RunConfig.tool_not_found_behavior` defaults to `'raise_error'`. Keep it (no silent fallbacks).
