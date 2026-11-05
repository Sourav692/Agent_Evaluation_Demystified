"""Local tracing for the refund agent, used from Week 13 on.

A standard-library span recorder that follows the OpenTelemetry data model. A trace is the
tree of spans for one request. Each span has a 32-hex-digit trace ID, a 16-hex-digit span ID,
its parent's span ID, a name, start and end times, a status (UNSET, OK or ERROR) and
attributes. Attribute names follow the OpenInference semantic conventions, checked against
`openinference-semantic-conventions` 0.1.43 (`openinference.semconv.trace`), so the same spans
read correctly in tools that understand them.

Everything is deterministic. IDs come from a seeded generator and time from a simulated
clock, so a replay produces the same traces on every run. Durations are SIMULATED from the
constants in LATENCY_MS, not measured.

`TracedRuntime` instruments the existing tool runtime without editing it: every tool call
becomes a TOOL span, and search_policy adds a RETRIEVER span listing the chunks it returned.
`trace_request` wraps one agent run in an AGENT span and records the reply step as an LLM
span. The course's agents are deterministic code standing in for a model. The LLM span marks
where a model call would sit, and its `llm.model_name` says that no model ran.
"""

from __future__ import annotations

import contextvars
import hashlib
import json
import random
import re
from contextlib import contextmanager
from dataclasses import dataclass, field

from shared.tools import ToolRuntime

# OpenInference attribute names (openinference.semconv.trace.SpanAttributes, DocumentAttributes).
SPAN_KIND = "openinference.span.kind"          # AGENT, CHAIN, LLM, RETRIEVER, TOOL, ...
INPUT_VALUE, OUTPUT_VALUE = "input.value", "output.value"
TOOL_NAME, TOOL_PARAMETERS = "tool.name", "tool.parameters"
RETRIEVAL_DOCUMENTS = "retrieval.documents"    # flattened: retrieval.documents.0.document.id
DOCUMENT_ID, DOCUMENT_CONTENT = "document.id", "document.content"
SESSION_ID, USER_ID = "session.id", "user.id"
LLM_MODEL_NAME = "llm.model_name"

STAND_IN_MODEL = "deterministic-stand-in (no model call)"
FAILED_OUTCOMES = {"refund_failed", "escalation_failed"}
# SIMULATED durations in milliseconds. A timed-out call costs the caller the whole timeout.
LATENCY_MS = {"get_customer": 30, "get_order": 40, "search_policy": 30, "retrieve": 90,
              "create_refund": 250, "escalate_to_specialist": 150, "compose_reply": 600, "timeout": 5000}

_CURRENT: contextvars.ContextVar = contextvars.ContextVar("current_span", default=None)


class SimClock:
    """Simulated time in milliseconds. Spans read it; the runtime advances it."""

    def __init__(self, now_ms: int = 0):
        self.now_ms = now_ms

    def advance(self, ms: int) -> None:
        self.now_ms += ms


@dataclass
class Span:
    trace_id: str
    span_id: str
    parent_id: str | None
    name: str
    kind: str
    start_ms: int
    end_ms: int | None = None
    status: str = "UNSET"
    status_message: str = ""
    attributes: dict = field(default_factory=dict)


class Tracer:
    """Records spans. The current span lives in a context variable, so children find their parent."""

    def __init__(self, seed: int = 0, clock: SimClock | None = None):
        self._rng = random.Random(seed)
        self.clock = clock or SimClock()
        self.spans: list[Span] = []           # in start order

    def _hex_id(self, bits: int) -> str:
        value = 0
        while value == 0:                     # all-zero IDs are invalid in W3C Trace Context
            value = self._rng.getrandbits(bits)
        return f"{value:0{bits // 4}x}"

    @contextmanager
    def span(self, name: str, kind: str, attributes: dict | None = None, parent: tuple[str, str] | None = None):
        """Start a span as a child of the current one, or of `parent` = (trace_id, span_id) from another process."""
        current = _CURRENT.get()
        if parent:
            trace_id, parent_id = parent
        elif current:
            trace_id, parent_id = current.trace_id, current.span_id
        else:
            trace_id, parent_id = self._hex_id(128), None
        span = Span(trace_id, self._hex_id(64), parent_id, name, kind, self.clock.now_ms,
                    attributes={SPAN_KIND: kind, **(attributes or {})})
        self.spans.append(span)
        token = _CURRENT.set(span)
        try:
            yield span
        except Exception as exc:
            span.status, span.status_message = "ERROR", type(exc).__name__
            raise
        finally:
            _CURRENT.reset(token)
            span.end_ms = self.clock.now_ms

    def trace(self, trace_id: str) -> list[Span]:
        return [s for s in self.spans if s.trace_id == trace_id]


# --- Context propagation across a process boundary (W3C Trace Context `traceparent`) ----------

def traceparent(span: Span, sampled: bool = True) -> str:
    return f"00-{span.trace_id}-{span.span_id}-{'01' if sampled else '00'}"


def parse_traceparent(header: str) -> tuple[str, str, bool]:
    """(trace_id, parent span_id, sampled). Raises ValueError on a malformed header."""
    parts = header.strip().split("-")
    if len(parts) != 4 or parts[0] != "00" or not re.fullmatch(r"[0-9a-f]{32}", parts[1]) \
            or not re.fullmatch(r"[0-9a-f]{16}", parts[2]) or set(parts[1]) == {"0"} or set(parts[2]) == {"0"}:
        raise ValueError(f"malformed traceparent: {header!r}")
    return parts[1], parts[2], parts[3] == "01"


# --- Instrumentation ---------------------------------------------------------------------------

@dataclass
class TracedRuntime(ToolRuntime):
    """The Week 7 runtime, unchanged, with a TOOL span around every call."""

    tracer: Tracer | None = None

    def call(self, name: str, **args):
        attrs = {TOOL_NAME: name, TOOL_PARAMETERS: json.dumps(args, sort_keys=True)}
        with self.tracer.span(name, "TOOL", attrs) as span:
            record = super().call(name, **args)
            self.tracer.clock.advance(LATENCY_MS["timeout"] if record.error == "timeout" else LATENCY_MS.get(name, 50))
            span.attributes[OUTPUT_VALUE] = json.dumps(record.response, sort_keys=True, default=str)
            span.status, span.status_message = ("ERROR", record.error) if record.error else ("OK", "")
        return record

    def _tool_search_policy(self, query: str) -> list[dict]:
        with self.tracer.span("retrieve", "RETRIEVER", {INPUT_VALUE: query}) as span:
            hits = super()._tool_search_policy(query)
            self.tracer.clock.advance(LATENCY_MS["retrieve"])
            for i, hit in enumerate(hits):
                span.attributes[f"{RETRIEVAL_DOCUMENTS}.{i}.{DOCUMENT_ID}"] = hit["chunk_id"]
                span.attributes[f"{RETRIEVAL_DOCUMENTS}.{i}.{DOCUMENT_CONTENT}"] = hit["text"]
            span.status = "OK"
        return hits


def trace_request(tracer: Tracer, agent, message: str, rt: TracedRuntime, attributes: dict | None = None):
    """Run one agent request inside an AGENT span. Returns (AgentResult, root span)."""
    with tracer.span("support_request", "AGENT", {INPUT_VALUE: message, **(attributes or {})}) as root:
        result = agent(message, rt)
        with tracer.span("compose_reply", "LLM", {LLM_MODEL_NAME: STAND_IN_MODEL, INPUT_VALUE: result.outcome}) as llm:
            tracer.clock.advance(LATENCY_MS["compose_reply"])
            llm.attributes[OUTPUT_VALUE] = result.reply
            llm.status = "OK"
        root.attributes.update({OUTPUT_VALUE: result.reply, "refund.outcome_claimed": result.outcome,
                                "refund.order_id": result.order_id or ""})
        root.status = "ERROR" if result.outcome in FAILED_OUTCOMES else "OK"
        root.status_message = result.outcome if root.status == "ERROR" else ""
    return result, root


# --- Sampling and export -----------------------------------------------------------------------

def head_sampled(trace_id: str, rate: float) -> bool:
    """Keep a trace when the low 64 bits of its ID fall under rate x 2^64, as OpenTelemetry's
    TraceIdRatioBased sampler does. Every service makes the same decision for the same trace."""
    return int(trace_id[-16:], 16) < round(rate * 2**64)


EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
CARD_NUMBER = re.compile(r"\b\d(?:[ -]?\d){11,18}\b")
CUSTOMER_ID = re.compile(r"\bcust-\d+\b")


def pseudonym(customer_id: str, salt: str) -> str:
    """A stable stand-in for a customer ID: the same customer gets the same pseudonym in every trace."""
    return "user-" + hashlib.sha256(f"{salt}:{customer_id}".encode()).hexdigest()[:10]


def redact_text(text: str, names: tuple[str, ...] = (), salt: str = "week-13") -> str:
    """Mask emails and card-like numbers, the given names, and pseudonymize customer IDs."""
    text = CARD_NUMBER.sub("<card-number>", EMAIL.sub("<email>", text))
    for name in sorted(names, key=len, reverse=True):
        text = re.sub(rf"\b{re.escape(name)}\b", "<name>", text)
    return CUSTOMER_ID.sub(lambda m: pseudonym(m.group(), salt), text)


def export_span(span: Span, names: tuple[str, ...] = (), salt: str = "week-13") -> dict:
    """The span as it leaves the process: plain JSON, every string attribute redacted."""
    return {"trace_id": span.trace_id, "span_id": span.span_id, "parent_id": span.parent_id,
            "name": span.name, "kind": span.kind, "start_ms": span.start_ms, "end_ms": span.end_ms,
            "status": span.status, "status_message": span.status_message,
            "attributes": {k: redact_text(v, names, salt) if isinstance(v, str) else v
                           for k, v in span.attributes.items()}}
