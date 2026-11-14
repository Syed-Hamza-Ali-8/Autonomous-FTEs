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

## Added in Phase 1 (verified 2026-11-07 against openai-agents 0.24.0)

| Symbol | Verified detail | Tollgate use |
|---|---|---|
| `RunItemStreamEvent.name` | `Literal["message_output_created", "handoff_requested", "handoff_occured", "tool_called", "tool_search_called", "tool_search_output_created", "tool_output", "reasoning_item_created", "mcp_approval_requested", "mcp_approval_response", "mcp_list_tools"]` | `tool_called` -> progress event; `tool_output` -> order_ref events |
| `RawResponsesStreamEvent.data` | Responses stream event; `type == "response.completed"` once per model call | Model calls counted here, independent of provider usage |
| `ToolCallItem.raw_item` | `ResponseFunctionToolCall` (has `.name`) or dict | Tool name for progress labels |
| `RunResultStreaming` | public: `final_output`, `context_wrapper` (`.usage`), `cancel(mode='immediate'\|'after_turn')` | Buffered reply; token accounting; Stop button |
| `Agent.instructions` | `str \| Callable[[RunContextWrapper, Agent], MaybeAwaitable[str]]` | Adds "opened from order X" context |
| `ModelSettings.include_usage` | Sent as `stream_options={"include_usage": ...}` by `OpenAIChatCompletionsModel` (`chatcmpl_helpers.get_stream_options_param`) | **Required**: streamed Chat Completions report no tokens otherwise (budget accounting) |
| `FunctionTool.on_invoke_tool` | `(ctx: ToolContext[Any], input: str) -> Any` | Tests invoke tools exactly as the SDK does |
| `agents.tool_context.ToolContext` | `(context, usage=..., tool_name=..., tool_call_id=..., tool_arguments=..., ...)` | Same |
| `Model` (abstract) | `get_response(...)`, `stream_response(...) -> AsyncIterator[TResponseStreamEvent]`; the run loop needs a `ResponseCompletedEvent` | `tests/fakes.py` ScriptedModel |

Notes:
5. The SDK snapshots agents with `dataclasses.asdict` at run start, which deep-copies dataclass fields. A `Model` must not be a dataclass holding uncopyable objects (found with the test fake).
6. With `strict_mode=True` (default), tool schemas set `additionalProperties: false`; an injected `customer_id` argument is rejected before the tool runs (tested).

## Function-tool argument validation (verified 2026-11-07, Phase 3)

Verified by calling `FunctionTool.on_invoke_tool(ToolContext(...), json)` on `openai-agents==0.24.0` and reading
`agents/tool.py` (`_prepare_arguments`, `_FailureHandlingFunctionToolInvoker.__call__`,
`maybe_invoke_function_tool_failure_error_function`):

- The advertised `params_json_schema` is strict (`additionalProperties: false`, every property required), but the
  pydantic model that validates the arguments is **lax**: unknown fields are silently dropped, and `"3200"`, `12.0`
  and `true` are coerced to `int`. `12.5` and a missing field are rejected.
- A validation failure raises `ModelBehaviorError("Invalid JSON input for tool <name>: <pydantic text>")`
  `from` the `ValidationError`. The message embeds input values, so it must never be logged as is.
- Any exception from validation or the tool body goes to `failure_error_function(ctx, error)` (sync or async); its
  string is returned to the model as the tool output. `ctx` is a `ToolContext` with `tool_name`, `tool_call_id` and
  `tool_arguments` (the raw JSON string).
- `ToolContext(context, tool_name=..., tool_call_id=..., tool_arguments=...)` is how the runner invokes a tool; the
  model-free adversarial suite calls tools the same way.

Consequence (DECISIONS I3): every write tool re-validates `ctx.tool_arguments` with its own strict model
(`extra="forbid"`, strict types) and audits rejections from both layers, recording argument names and error
locations only.
- `function_tool(strict_mode=True)` (the default) makes every parameter `required` in the advertised schema, even ones
  with defaults. Groq validates the model's tool call against that schema server-side and rejects a call that omits
  one (`missing properties: 'amount_cents'`, eval run 20261107T213633Z). Write tools therefore use
  `strict_mode=False` (required = only the parameters without defaults); the gateway's strict re-validation is the
  enforcement either way.

## Sampling seed and system_fingerprint (Phase 4, verified 2026-11-11 against openai-agents 0.24.0)
- `ModelSettings` has **no `seed` field** (fields checked via `ModelSettings.__dataclass_fields__`).
- `OpenAIChatCompletionsModel._fetch_response` merges `model_settings.extra_args` into the
  `chat.completions.create(**create_kwargs)` call (`create_kwargs.update(model_settings.extra_args or {})`), raising
  `TypeError` on a duplicate key. So the seed is sent as `ModelSettings(extra_args={"seed": …})`.
- The streamed path does not surface `system_fingerprint`. The SDK iterates the returned stream (`async for chunk in
  stream`) and reads `stream.response.headers["x-request-id"]` (`_attach_stream_request_id`), so a pass-through proxy
  that keeps `.response` is safe: `tollgate/llm/fingerprints.py`.
