"""Week 13 lab: trace the refund agent, replay SIMULATED traffic, and run online checks, alerts and a rollback on the traces.

Usage, from new_course/:
    python3 weeks/week-13-tracing-and-online-evaluation/handson/lab.py traffic
    python3 weeks/week-13-tracing-and-online-evaluation/handson/lab.py trace r-0007
    python3 weeks/week-13-tracing-and-online-evaluation/handson/lab.py replay
    python3 weeks/week-13-tracing-and-online-evaluation/handson/lab.py replay --no-rollback
    python3 weeks/week-13-tracing-and-online-evaluation/handson/lab.py sampling
    python3 weeks/week-13-tracing-and-online-evaluation/handson/lab.py drift
    python3 weeks/week-13-tracing-and-online-evaluation/handson/lab.py redaction
    python3 weeks/week-13-tracing-and-online-evaluation/handson/lab.py dashboard
    python3 weeks/week-13-tracing-and-online-evaluation/handson/lab.py otel     # optional, needs opentelemetry-sdk

All traffic is SIMULATED: a seeded generator builds it from dataset/traffic-config-v1.json
and replays it against datasets/world.json, one fresh in-memory ledger per request. Span
durations come from shared/tracing.LATENCY_MS. Nothing here is production data.
"""

from __future__ import annotations

import argparse
import html
import json
import random
import re
import sys
from collections import Counter
from datetime import date, datetime, timezone
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSE = HERE.parents[2]
sys.path.insert(0, str(COURSE))

from shared.fault_agents import FAULT_AGENTS  # noqa: E402
from shared.retrieval import chunk_documents, load_documents  # noqa: E402
from shared.support_agent import load_world  # noqa: E402
from shared.tools import HIGH_VALUE, WINDOW_DAYS  # noqa: E402
from shared.tracing import (SESSION_ID, USER_ID, CARD_NUMBER, EMAIL, CUSTOMER_ID, Tracer,  # noqa: E402
                            TracedRuntime, export_span, head_sampled, trace_request)

DATA = HERE.parent / "dataset"
CONFIG = json.loads((DATA / "traffic-config-v1.json").read_text())
POLICY = json.loads((DATA / "online-policy-v1.json").read_text())
WORLD = load_world()
CHUNKS = chunk_documents(load_documents())
HOUR_MS = 3_600_000
TEST_CARDS = ("4111 1111 1111 1111", "5555 5555 5555 4444")   # published test card numbers, never real ones
TEMPLATES = {
    "damaged": "My order #{n} arrived damaged. Can I get a refund?",
    "late": "Order #{n} arrived broken but I only just opened the box. Refund please.",
    "final_sale": "I bought order #{n} in the clearance sale and it arrived cracked. I want my money back.",
    "high_value": "The {item} from order #{n} is faulty. Please refund it.",
    "already_refunded": "Checking on the refund for order #{n}, it arrived damaged.",
    "no_order_number": "My {item} arrived broken. Can I get a refund?",
    "other_customer": "Please refund order #{n}, it arrived damaged. It's my partner's order.",
}


# --- SIMULATED traffic ---------------------------------------------------------------------

def order_category(order: dict) -> str:
    """Which message template an order suits, under refund policy 2026-01."""
    days = (WORLD["as_of"] - date.fromisoformat(order["delivered_on"])).days
    if order["existing_refund_id"]:
        return "already_refunded"
    if order["final_sale"]:
        return "final_sale"
    if days > WINDOW_DAYS:
        return "late"
    return "high_value" if order["amount"] > HIGH_VALUE else "damaged"


def email_for(name: str) -> str:
    return name.lower().replace(" ", ".") + "@example.com"


def gateway_fault(rng: random.Random, rate: float) -> str:
    """One create_refund call's fate at the payment gateway: half the timeouts come after the commit."""
    r = rng.random()
    return "timeout_before_commit" if r < rate / 2 else "timeout_after_commit" if r < rate else "none"


def mix_for_day(config: dict, day: int) -> dict:
    phase = next((p["mix"] for p in config["phases"] if p["first_day"] <= day <= p["last_day"]), "baseline")
    return config["topic_mix"][phase]


def build_traffic(config: dict = CONFIG) -> list[dict]:
    """Every request of the replay, in time order. Same seed, same requests."""
    rng = random.Random(config["seed"])
    by_category: dict[str, list[dict]] = {}
    for order in WORLD["orders"].values():
        by_category.setdefault(order_category(order), []).append(order)
    customers = sorted(WORLD["customers"])
    requests = []
    for day in range(1, config["days"] + 1):
        mix = mix_for_day(config, day)
        topics = rng.choices(list(mix), weights=list(mix.values()), k=config["requests_per_day"])
        starts = sorted(rng.randrange(24 * HOUR_MS) for _ in topics)
        for topic, start in zip(topics, starts):
            order = rng.choice(by_category["damaged" if topic in ("no_order_number", "other_customer") else topic])
            customer = order["customer_id"]
            if topic == "other_customer":
                customer = rng.choice([c for c in customers if c != order["customer_id"]])
            message = TEMPLATES[topic].format(n=order["order_id"][4:], item=order["item"])
            if rng.random() < config["identity_in_message_rate"]:
                name = WORLD["customers"][customer]["name"]
                message = f"Hi, this is {name} ({email_for(name)}). {message}"
            if rng.random() < config["card_number_in_message_rate"]:
                message += f" Please send it to my card {rng.choice(TEST_CARDS)}."
            n = len(requests) + 1
            requests.append({"request_id": f"r-{n:04d}", "session_id": f"s-{n:04d}", "day": day,
                             "start_ms": (day - 1) * 24 * HOUR_MS + start, "customer_id": customer,
                             "topic": topic, "message": message,
                             "gateway_faults": [gateway_fault(rng, config["gateway_timeout_rate"]) for _ in range(2)],
                             "feedback_draws": [rng.random(), rng.random()]})
    return requests


def simulated_feedback(request: dict, outcome: str, config: dict = CONFIG) -> str | None:
    """SIMULATED thumbs up/down. Most users give none, and denials get thumbs-down even when correct."""
    give, down = request["feedback_draws"]
    if give >= config["feedback_rate"]:
        return None
    return "down" if down < config["thumbs_down_given_outcome"][outcome] else "up"


# --- One traced request and its online checks -----------------------------------------------

def run_request(request: dict, version: str, tracer: Tracer, config: dict = CONFIG) -> dict:
    """Serve one request with the deployed version, inside a trace. The ledger is read back separately."""
    rt = TracedRuntime(WORLD, request["customer_id"], chunks=CHUNKS, tracer=tracer,
                       faults={"create_refund": list(request["gateway_faults"])})
    tracer.clock.now_ms = request["start_ms"]
    first = len(tracer.spans)
    agent = FAULT_AGENTS[config["versions"][version]["agent"]]
    result, root = trace_request(tracer, agent, request["message"], rt,
                                 {SESSION_ID: request["session_id"], USER_ID: request["customer_id"],
                                  "agent.version": version})
    row = {"request": request, "version": version, "trace_id": root.trace_id, "spans": tracer.spans[first:],
           "outcome": result.outcome, "order_id": result.order_id, "ledger": rt.store.new_refunds(),
           "duration_ms": root.end_ms - root.start_ms, "feedback": simulated_feedback(request, result.outcome, config)}
    row["checks"] = online_checks(row)
    return row


def online_checks(row: dict) -> dict:
    """Reference-free checks: no expected outcome, only the trace and the ledger read-back."""
    spans = row["spans"]
    creates = [s for s in spans if s.name == "create_refund"]
    stored = [r for r in row["ledger"] if r["order_id"] == row["order_id"]]
    return {
        "refund_attempt": bool(creates),
        "refund_failure": bool(creates) and creates[-1].status == "ERROR",
        "claim_mismatch": (row["outcome"] == "refund_created") != bool(stored),
        "tool_errors": [f"{s.name}:{s.status_message}" for s in spans if s.kind == "TOOL" and s.status == "ERROR"],
        "root_error": spans[0].status == "ERROR",
    }


# --- Window metrics and alerts --------------------------------------------------------------

def message_topic(message: str) -> str:
    """A cheap input feature computed on every request: a keyword topic. It knows nothing of outcomes."""
    m = message.lower()
    if "#" not in m:
        return "no_order_number"
    for word, topic in (("clearance", "sale"), ("partner", "on_behalf"), ("checking on", "follow_up"),
                        ("just opened", "late_opening"), ("faulty", "faulty")):
        if word in m:
            return topic
    return "damaged"


def topic_mix(rows: list[dict]) -> dict:
    counts = Counter(message_topic(r["request"]["message"]) for r in rows)
    return {t: n / len(rows) for t, n in counts.items()} if rows else {}


def total_variation(p: dict, q: dict) -> float:
    """Half the summed absolute difference between two distributions: 0 is identical, 1 is disjoint."""
    return sum(abs(p.get(k, 0) - q.get(k, 0)) for k in p.keys() | q.keys()) / 2


def percentile(values: list[float], pct: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, round(pct / 100 * len(ordered) + 0.5) - 1)] if ordered else 0.0


def metric(name: str, rows: list[dict], baseline: dict | None) -> float | None:
    if name == "refund_failure_rate":
        attempts = sum(r["checks"]["refund_attempt"] for r in rows)
        return sum(r["checks"]["refund_failure"] for r in rows) / attempts if attempts else 0.0
    if name == "claim_mismatches":
        return sum(r["checks"]["claim_mismatch"] for r in rows)
    if name == "thumbs_down_rate":
        given = [r["feedback"] for r in rows if r["feedback"]]
        return given.count("down") / len(given) if given else 0.0
    if name == "topic_drift":
        return total_variation(topic_mix(rows), baseline) if baseline and rows else None
    if name == "p95_latency_ms":
        return percentile([r["duration_ms"] for r in rows], 95)
    raise ValueError(f"unknown metric: {name}")


def volume(name: str, rows: list[dict]) -> int:
    if name == "refund_attempts":
        return sum(r["checks"]["refund_attempt"] for r in rows)
    if name == "feedback":
        return sum(r["feedback"] is not None for r in rows)
    return len(rows)


def alert_examples(alert: dict, rows: list[dict], baseline: dict | None, n: int = 3) -> list[str]:
    """The latest traces that show what the alert measures, so the alert links to evidence."""
    name = alert["metric"]
    if name == "topic_drift":
        mix = topic_mix(rows)
        topic = max(mix, key=lambda t: mix[t] - baseline.get(t, 0))     # the most over-represented topic
        hits = [r for r in rows if message_topic(r["request"]["message"]) == topic]
    elif name == "thumbs_down_rate":
        hits = [r for r in rows if r["feedback"] == "down"]
    else:
        check = "refund_failure" if name == "refund_failure_rate" else "claim_mismatch"
        hits = [r for r in rows if r["checks"][check]]
    return [r["trace_id"] for r in hits[-n:]]


def hour_label(hour: int) -> str:
    return f"day {hour // 24 + 1} {hour % 24:02d}:00"


@lru_cache(maxsize=4)
def replay(auto_rollback: bool = True) -> dict:
    """Serve the SIMULATED traffic hour by hour. At the end of each hour, evaluate every alert on its
    trailing window and apply the rollback rule. Event times are those evaluation times. A rollback
    decided at an evaluation takes effect immediately, for the next hour's traffic."""
    config, policy = CONFIG, POLICY
    traffic = build_traffic(config)
    tracer = Tracer(seed=config["seed"])
    deploys = {(d["day"] - 1) * 24 + d["hour"]: d["version"] for d in config["deploys"]}
    version, previous, last_deploy, rollback_at, streak = config["initial_version"], None, None, None, 0
    baseline_end = policy["drift_baseline_days"][1] * 24
    hourly, rows, events, log, baseline, i = [], [], [], [], None, 0
    firing = {a["name"]: None for a in policy["alerts"]}
    for hour in range(config["days"] * 24):
        if hour == rollback_at:
            log.append((hour, "rollback", f"{version} -> {previous}"))
            version, previous = previous, None
        if hour in deploys:
            log.append((hour, "deploy", f"{version} -> {deploys[hour]}"))
            previous, version, last_deploy = version, deploys[hour], hour
        served = []
        while i < len(traffic) and traffic[i]["start_ms"] < (hour + 1) * HOUR_MS:
            served.append(run_request(traffic[i], version, tracer, config))
            i += 1
        hourly.append(served)
        rows += served
        if hour + 1 == baseline_end:
            baseline = topic_mix(rows)
        for alert in policy["alerts"]:
            window = [r for h in hourly[max(0, hour + 1 - alert["window_hours"]):] for r in h]
            value, vol = metric(alert["metric"], window, baseline), volume(alert["volume_metric"], window)
            on = value is not None and vol >= alert["min_volume"] and value > alert["threshold"]
            open_event = firing[alert["name"]]
            if on and open_event is None:
                firing[alert["name"]] = {"alert": alert["name"], "severity": alert["severity"], "fired": hour + 1,
                                         "resolved": None, "value": value, "volume": vol,
                                         "examples": alert_examples(alert, window, baseline)}
                events.append(firing[alert["name"]])
            elif not on and open_event is not None:
                open_event["resolved"] = hour + 1
                firing[alert["name"]] = None
        rule = policy["rollback"]
        streak = streak + 1 if firing[rule["alert"]] else 0
        if (auto_rollback and rollback_at is None and previous and last_deploy is not None
                and streak >= rule["consecutive_evaluations"] and hour - last_deploy <= rule["max_hours_since_deploy"]):
            rollback_at = hour + 1
            log.append((hour + 1, "rollback decided", f"{rule['alert']} firing for {streak} evaluations"))
    return {"rows": rows, "hourly": hourly, "events": events, "log": log, "tracer": tracer, "baseline": baseline,
            "auto_rollback": auto_rollback}


def incident_summary(run: dict) -> dict:
    """Time to detect and mitigate the deploy, and the customers hurt after it."""
    deploy = next(h for h, kind, _ in run["log"] if kind == "deploy")
    fired = next((e["fired"] for e in run["events"] if e["alert"] == POLICY["rollback"]["alert"]
                  and e["fired"] >= deploy), None)
    rolled = next((h for h, kind, _ in run["log"] if kind == "rollback"), None)
    after = [r for r in run["rows"] if r["request"]["start_ms"] >= deploy * HOUR_MS]
    on_bad = [r for r in after if r["version"] != CONFIG["initial_version"]]
    return {"deploy_hour": deploy, "detect_hours": None if fired is None else fired - deploy,
            "mitigate_hours": None if rolled is None else rolled - deploy,
            "requests_on_bad_version": len(on_bad),
            "refund_failures": sum(r["checks"]["refund_failure"] for r in on_bad),
            "claim_mismatches": sum(r["checks"]["claim_mismatch"] for r in on_bad)}


# --- Sampling and export ----------------------------------------------------------------------

def tail_reasons(row: dict) -> list[str]:
    """Why a tail sampler keeps this trace, decided after the trace ends."""
    reasons = []
    if row["checks"]["root_error"]:
        reasons.append("root_error")
    if any(e.endswith(":timeout") for e in row["checks"]["tool_errors"]):
        reasons.append("tool_timeout")
    if row["checks"]["claim_mismatch"]:
        reasons.append("claim_mismatch")
    if row["feedback"] == "down":
        reasons.append("thumbs_down")
    return reasons


def tail_kept(row: dict, head_rate: float) -> bool:
    return head_sampled(row["trace_id"], head_rate) or bool(tail_reasons(row))


def sampling_report(run: dict, rates: tuple[float, ...] = (0.01, 0.05, 0.10)) -> list[dict]:
    """How many traces of the failures each sampler keeps. Failures = refund failures or claim mismatches."""
    rows = run["rows"]
    failures = [r for r in rows if r["checks"]["refund_failure"] or r["checks"]["claim_mismatch"]]
    out = []
    for label, keep in ([(f"head {rate:.0%}", lambda r, rate=rate: head_sampled(r["trace_id"], rate)) for rate in rates]
                        + [(f"tail + head {POLICY['sampling']['head_rate']:.0%}",
                            lambda r: tail_kept(r, POLICY["sampling"]["head_rate"]))]):
        kept = [r for r in rows if keep(r)]
        out.append({"sampler": label, "traces": len(kept), "spans": sum(len(r["spans"]) for r in kept),
                    "failures_kept": sum(keep(r) for r in failures), "failures": len(failures)})
    return out


def alert_hours(run: dict, alert: dict, keep=lambda row: True) -> list[dict]:
    """The evaluation times at which `alert` would fire on this run's traffic, counting only rows `keep` accepts."""
    hourly = [[r for r in h if keep(r)] for h in run["hourly"]]
    fires = []
    for hour in range(len(hourly)):
        window = [r for h in hourly[max(0, hour + 1 - alert["window_hours"]):hour + 1] for r in h]
        value, vol = metric(alert["metric"], window, run["baseline"]), volume(alert["volume_metric"], window)
        if value is not None and vol >= alert["min_volume"] and value > alert["threshold"]:
            fires.append({"hour": hour + 1, "value": value, "volume": vol})
    return fires


def alert_on_sample(run: dict, rate: float) -> list[dict]:
    """The refund-failure alert computed from head-sampled traces only, as if metrics came from stored traces."""
    alert = next(a for a in POLICY["alerts"] if a["metric"] == "refund_failure_rate")
    return alert_hours(run, alert, lambda r: head_sampled(r["trace_id"], rate))


def identity_names(customer_id: str) -> tuple[str, ...]:
    """Names the runtime already knows for the signed-in customer: full name, first and last name."""
    full = WORLD["customers"][customer_id]["name"]
    return (full, *full.split())


def export_trace(row: dict, identity_aware: bool = True) -> list[dict]:
    names = identity_names(row["request"]["customer_id"]) if identity_aware else ()
    return [export_span(s, names, POLICY["redaction_salt"]) for s in row["spans"]]


CUSTOMER_NAMES = re.compile(r"\b(?:" + "|".join(re.escape(c["name"]) for c in WORLD["customers"].values()) + r")\b")


def leaks(exported: list[dict]) -> Counter:
    """Personal data still present in exported attributes: emails, card numbers, raw customer IDs, names."""
    text = json.dumps([s["attributes"] for s in exported])
    found = Counter(email=len(EMAIL.findall(text)), card_number=len(CARD_NUMBER.findall(text)),
                    customer_id=len(CUSTOMER_ID.findall(text)))
    found["name"] = len(CUSTOMER_NAMES.findall(text))
    return found


# --- OpenTelemetry SDK export (optional) ------------------------------------------------------

EPOCH_NS = int(datetime(2026, 3, 1, tzinfo=timezone.utc).timestamp()) * 10**9   # day 1 00:00, for OTel timestamps


def otel_export(exported: list[dict]):
    """Send exported (redacted) spans through the real OpenTelemetry SDK, keeping their IDs, parents,
    times, status and attributes. Returns the SDK's finished spans, or None if the SDK is not installed."""
    try:
        from opentelemetry import trace as ot
        from opentelemetry.context import Context
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor
        from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
        from opentelemetry.sdk.trace.id_generator import IdGenerator
        from opentelemetry.trace import Status, StatusCode
    except ImportError:
        return None

    class ReplayIds(IdGenerator):
        """Hands the SDK the IDs our tracer already chose, so both records name the same spans."""
        trace_id = span_id = 0

        def generate_trace_id(self) -> int:
            return self.trace_id

        def generate_span_id(self) -> int:
            return self.span_id

    ids, exporter = ReplayIds(), InMemorySpanExporter()
    provider = TracerProvider(id_generator=ids)
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("week-13-lab")
    started = {}
    for s in exported:                                # start order: every parent before its children
        ids.trace_id, ids.span_id = int(s["trace_id"], 16), int(s["span_id"], 16)
        context = ot.set_span_in_context(started[s["parent_id"]]) if s["parent_id"] else Context()
        started[s["span_id"]] = tracer.start_span(s["name"], context=context, attributes=s["attributes"],
                                                  start_time=EPOCH_NS + s["start_ms"] * 10**6)
    for s in reversed(exported):                      # end children before parents
        if s["status"] == "ERROR":
            started[s["span_id"]].set_status(Status(StatusCode.ERROR, s["status_message"]))
        elif s["status"] == "OK":
            started[s["span_id"]].set_status(Status(StatusCode.OK))
        started[s["span_id"]].end(end_time=EPOCH_NS + s["end_ms"] * 10**6)
    provider.shutdown()
    return exporter.get_finished_spans()


def otel_matches(exported: list[dict], finished) -> list[str]:
    """Span IDs whose SDK copy differs from ours. Empty means the SDK received the same traces."""
    theirs = {f"{f.context.span_id:016x}": f for f in finished}
    problems = []
    for s in exported:
        f = theirs.get(s["span_id"])
        parent = f"{f.parent.span_id:016x}" if f is not None and f.parent else None
        if f is None or f"{f.context.trace_id:032x}" != s["trace_id"] or parent != s["parent_id"] \
                or dict(f.attributes) != s["attributes"] or f.status.status_code.name != s["status"]:
            problems.append(s["span_id"])
    return problems


# --- Printing -----------------------------------------------------------------------------------

def print_traffic(head: int = 3) -> None:
    traffic = build_traffic()
    print(f"{len(traffic)} SIMULATED requests over {CONFIG['days']} days ({CONFIG['traffic_version']}, seed {CONFIG['seed']})")
    for label, days in (("days 1-3", range(1, 4)), ("days 4-6 (clearance sale)", range(4, 7)),
                        ("days 7-14", range(7, 15))):
        part = [r for r in traffic if r["day"] in days]
        mix = Counter(r["topic"] for r in part)
        print(f"  {label:<27}" + "  ".join(f"{t} {mix[t] / len(part):.0%}" for t in CONFIG["topic_mix"]["baseline"]))
    timeouts = sum(f != "none" for r in traffic for f in r["gateway_faults"][:1])
    print(f"  first create_refund attempt would time out: {timeouts} requests ({timeouts / len(traffic):.1%})")
    for r in traffic[:head]:
        print(f"  {r['request_id']} day {r['day']} {r['customer_id']}: {r['message']}")


def print_trace(row: dict, raw: bool = False) -> None:
    spans = row["spans"] if raw else export_trace(row)
    get = (lambda s, k: getattr(s, k)) if raw else (lambda s, k: s[k])
    depth = {}
    print(f"{row['request']['request_id']} ({'raw, in process' if raw else 'as exported, redacted'}), "
          f"version {row['version']}, trace {get(spans[0], 'trace_id')}")
    for s in spans:
        depth[get(s, "span_id")] = depth.get(get(s, "parent_id"), -1) + 1
        attrs = get(s, "attributes")
        detail = {"AGENT": attrs.get("input.value", ""), "TOOL": attrs.get("tool.parameters", ""),
                  "RETRIEVER": [v for k, v in attrs.items() if k.endswith("document.id")],
                  "LLM": attrs.get("output.value", "")}[get(s, "kind")]
        status = get(s, "status") + (f" ({get(s, 'status_message')})" if get(s, "status_message") else "")
        print(f"  {'  ' * depth[get(s, 'span_id')] + get(s, 'name'):<20}{get(s, 'kind'):<10}"
              f"{get(s, 'end_ms') - get(s, 'start_ms'):>6} ms  {status:<26}{detail}")
    print(f"  ledger read-back: {[(r['refund_id'], r['order_id']) for r in row['ledger']]}")
    print(f"  online checks: {row['checks']}, feedback: {row['feedback']}")


def daily_rows(run: dict) -> list[dict]:
    out = []
    for day in range(1, CONFIG["days"] + 1):
        rows = [r for h in run["hourly"][(day - 1) * 24:day * 24] for r in h]
        out.append({"day": day, "versions": "/".join(sorted({r["version"] for r in rows})), "requests": len(rows),
                    "attempts": volume("refund_attempts", rows),
                    "failure_rate": metric("refund_failure_rate", rows, None),
                    "mismatches": metric("claim_mismatches", rows, None),
                    "thumbs_down": metric("thumbs_down_rate", rows, None),
                    "drift": metric("topic_drift", rows, run["baseline"]),
                    "p95": metric("p95_latency_ms", rows, None)})
    return out


def print_replay(run: dict) -> None:
    print(f"Replay of SIMULATED traffic, automatic rollback {'on' if run['auto_rollback'] else 'off'}")
    print(f"{'day':>4}  {'version':<10}{'requests':>9}{'refund attempts':>16}{'failure rate':>13}"
          f"{'mismatches':>11}{'thumbs-down':>12}{'drift':>7}{'p95 ms':>8}")
    for d in daily_rows(run):
        drift = "-" if d["drift"] is None else f"{d['drift']:.2f}"
        print(f"{d['day']:>4}  {d['versions']:<10}{d['requests']:>9}{d['attempts']:>16}{d['failure_rate']:>13.1%}"
              f"{d['mismatches']:>11}{d['thumbs_down']:>12.0%}{drift:>7}{d['p95']:>8}")
    print("Changes:")
    for hour, kind, detail in run["log"]:
        print(f"  {hour_label(hour)}  {kind:<17}{detail}")
    print("Alerts:")
    for e in run["events"]:
        resolved = hour_label(e["resolved"]) if e["resolved"] is not None else "still firing"
        print(f"  {e['alert']:<25}{e['severity']:<7} fired {hour_label(e['fired'])}, value {e['value']:.3g} "
              f"on {e['volume']}, resolved {resolved}")
    s = incident_summary(run)
    mitigated = f"rolled back after {s['mitigate_hours']} h" if s["mitigate_hours"] is not None else "never rolled back"
    print(f"Incident: deploy at {hour_label(s['deploy_hour'])}, detected after {s['detect_hours']} h, "
          f"{mitigated}; {s['requests_on_bad_version']} requests on the bad version, "
          f"{s['refund_failures']} refund failures, {s['claim_mismatches']} claim mismatches")


def print_sampling(run: dict) -> None:
    print(f"{'sampler':<17}{'traces kept':>12}{'spans kept':>11}   failure traces kept")
    for r in sampling_report(run):
        print(f"{r['sampler']:<17}{r['traces']:>12}{r['spans']:>11}   {r['failures_kept']} of {r['failures']}")
    for rate in (0.05, 0.10):
        fires = alert_on_sample(run, rate)
        first = hour_label(fires[0]["hour"]) if fires else "never"
        print(f"refund_failure_rate_high computed from a {rate:.0%} head sample: fires in {len(fires)} hours, first {first}")


def print_drift(run: dict) -> None:
    print("Input drift (topic mix vs days 1-3) against quality signals, per day")
    print(f"{'day':>4}{'drift':>7}{'sale share':>11}{'denied':>8}{'thumbs-down':>12}{'failure rate':>13}")
    for d, day in zip(daily_rows(run), range(1, CONFIG["days"] + 1)):
        rows = [r for h in run["hourly"][(day - 1) * 24:day * 24] for r in h]
        sale = topic_mix(rows).get("sale", 0)
        denied = sum(r["outcome"] == "refund_denied" for r in rows) / len(rows)
        drift = "-" if d["drift"] is None else f"{d['drift']:.2f}"
        print(f"{day:>4}{drift:>7}{sale:>11.0%}{denied:>8.0%}{d['thumbs_down']:>12.0%}{d['failure_rate']:>13.1%}")


def print_redaction(run: dict) -> None:
    rows = run["rows"]
    with_card = sum("my card" in r["request"]["message"] for r in rows)
    with_identity = sum(r["request"]["message"].startswith("Hi, this is") for r in rows)
    print(f"{len(rows)} traces; {with_identity} messages carry a name and email, {with_card} a card number")
    print(f"{'export':<26}{'emails':>8}{'card numbers':>14}{'customer IDs':>14}{'names':>7}")
    for label, aware in (("patterns only", False), ("patterns + session names", True)):
        found = leaks([s for r in rows for s in export_trace(r, aware)])
        print(f"{label:<26}{found['email']:>8}{found['card_number']:>14}{found['customer_id']:>14}{found['name']:>7}")


def write_dashboard(run: dict, out: Path = HERE / "runs" / "week-13") -> Path:
    """A static HTML dashboard: 6-hour windows, the change log, and alerts linked to exported traces."""
    (out / "traces").mkdir(parents=True, exist_ok=True)
    by_trace = {r["trace_id"]: r for r in run["rows"]}
    for e in run["events"]:
        for tid in e["examples"]:
            (out / "traces" / f"{tid}.json").write_text(json.dumps(export_trace(by_trace[tid]), indent=2))
    th = "".join(f"<th>{h}</th>" for h in ("window", "version", "requests", "refund attempts", "failure rate",
                                             "claim mismatches", "thumbs-down", "drift", "p95 ms", "alerts firing"))
    body = []
    for start in range(0, len(run["hourly"]), 6):
        rows = [r for h in run["hourly"][start:start + 6] for r in h]
        fr = metric("refund_failure_rate", rows, None)
        drift = metric("topic_drift", rows, run["baseline"])
        live = [e["alert"] for e in run["events"]
                if e["fired"] < start + 6 and (e["resolved"] is None or e["resolved"] >= start)]
        body.append(f"<tr{' class=hot' if live else ''}><td>{hour_label(start)}</td>"
                    f"<td>{'/'.join(sorted({r['version'] for r in rows}))}</td><td>{len(rows)}</td>"
                    f"<td>{volume('refund_attempts', rows)}</td>"
                    f"<td><span class=bar style='width:{min(fr, 0.2) * 500:.0f}px'></span> {fr:.1%}</td>"
                    f"<td>{metric('claim_mismatches', rows, None)}</td><td>{metric('thumbs_down_rate', rows, None):.0%}</td>"
                    f"<td>{'-' if drift is None else f'{drift:.2f}'}</td><td>{metric('p95_latency_ms', rows, None)}</td>"
                    f"<td>{', '.join(sorted(set(live)))}</td></tr>")
    alerts = "".join(
        f"<li><b>{e['alert']}</b> ({e['severity']}) fired {hour_label(e['fired'])}, value {e['value']:.3g}, "
        f"resolved {hour_label(e['resolved']) if e['resolved'] is not None else 'still firing'}. Traces: "
        + ", ".join(f"<a href='traces/{t}.json'>{t[:8]}</a>" for t in e["examples"]) + "</li>"
        for e in run["events"])
    changes = "".join(f"<li>{hour_label(h)}: {html.escape(k)} {html.escape(d)}</li>" for h, k, d in run["log"])
    page = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>Week 13 online evaluation dashboard (SIMULATED)</title>
<style>body{{font:14px system-ui,sans-serif;margin:2rem;color:#222}}table{{border-collapse:collapse}}
td,th{{border:1px solid #ccc;padding:2px 6px;text-align:right}}td:first-child,td:nth-child(2),td:last-child{{text-align:left}}
tr.hot{{background:#fff0f0}}.bar{{display:inline-block;height:8px;background:#c33}}</style></head><body>
<h1>Refund agent: online evaluation (SIMULATED traffic)</h1>
<p>Generated by weeks/week-13-tracing-and-online-evaluation/handson/lab.py from synthetic, replayed requests.
Every number below is simulated. Linked traces are exported and redacted.</p>
<h2>Changes</h2><ul>{changes}</ul><h2>Alerts</h2><ul>{alerts}</ul>
<h2>Six-hour windows</h2><table><tr>{th}</tr>{''.join(body)}</table></body></html>"""
    (out / "dashboard.html").write_text(page)
    return out / "dashboard.html"


def find_row(run: dict, request_id: str) -> dict | None:
    return next((r for r in run["rows"] if r["request"]["request_id"] == request_id), None)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("traffic", help="the SIMULATED traffic: volume, topic mix per phase, a few requests")
    p.add_argument("--head", type=int, default=3)
    p = sub.add_parser("trace", help="one request's spans")
    p.add_argument("request_id")
    p.add_argument("--raw", action="store_true", help="the in-process spans, before redaction")
    p = sub.add_parser("replay", help="serve 14 days, evaluate alerts hourly, roll back on the rule")
    p.add_argument("--no-rollback", action="store_true")
    for name in ("sampling", "drift", "redaction", "dashboard", "otel"):
        sub.add_parser(name)
    args = parser.parse_args()
    if args.command == "traffic":
        print_traffic(args.head)
        return
    run = replay(not getattr(args, "no_rollback", False))
    if args.command == "trace":
        row = find_row(run, args.request_id)
        if row is None:
            sys.exit(f"unknown request ID: {args.request_id}")
        print_trace(row, args.raw)
    elif args.command == "replay":
        print_replay(run)
    elif args.command == "sampling":
        print_sampling(run)
    elif args.command == "drift":
        print_drift(run)
    elif args.command == "redaction":
        print_redaction(run)
    elif args.command == "dashboard":
        path = write_dashboard(run)
        print(f"wrote {path.relative_to(COURSE)} and {len(list((path.parent / 'traces').glob('*.json')))} linked traces")
    else:
        exported = [s for r in run["rows"][:50] for s in export_trace(r)]
        finished = otel_export(exported)
        if finished is None:
            sys.exit("opentelemetry-sdk is not installed; see requirements-integrations.txt")
        print(f"OpenTelemetry SDK received {len(finished)} redacted spans from the first 50 requests; "
              f"spans that differ from ours: {otel_matches(exported, finished) or 'none'}")
        print(finished[-1].to_json(indent=None)[:700])


if __name__ == "__main__":
    main()
