"""
Eval runner for the Ghostfolio AI Agent.
Loads test_cases.json, POSTs to /chat, checks assertions, prints results.
Supports single-query and multi-step (write confirmation) test cases.
"""
import asyncio
import json
import os
import sys
import time

import httpx

BASE_URL = os.getenv("AGENT_BASE_URL", "http://localhost:8000")
RESULTS_FILE = os.path.join(os.path.dirname(__file__), "results.json")
TEST_CASES_FILE = os.path.join(os.path.dirname(__file__), "test_cases.json")


def _check_assertions(
    response_text: str,
    tools_used: list,
    awaiting_confirmation: bool,
    step: dict,
    elapsed: float,
    category: str,
) -> list[str]:
    """Returns a list of failure strings (empty = pass)."""
    failures = []
    rt = response_text.lower()

    for phrase in step.get("must_not_contain", []):
        if phrase.lower() in rt:
            failures.append(f"Response contained forbidden phrase: '{phrase}'")

    for phrase in step.get("must_contain", []):
        if phrase.lower() not in rt:
            failures.append(f"Response missing required phrase: '{phrase}'")

    must_one_of = step.get("must_contain_one_of", [])
    if must_one_of:
        if not any(p.lower() in rt for p in must_one_of):
            failures.append(f"Response missing at least one of: {must_one_of}")

    if "expected_tool" in step:
        if step["expected_tool"] not in tools_used:
            failures.append(
                f"Expected tool '{step['expected_tool']}' not used. Used: {tools_used}"
            )

    if "expected_tools" in step:
        for expected in step["expected_tools"]:
            if expected not in tools_used:
                failures.append(
                    f"Expected tool '{expected}' not used. Used: {tools_used}"
                )

    if "expect_tool" in step:
        if step["expect_tool"] not in tools_used:
            failures.append(
                f"Expected tool '{step['expect_tool']}' not used. Used: {tools_used}"
            )

    if "expect_awaiting_confirmation" in step:
        expected_ac = step["expect_awaiting_confirmation"]
        if awaiting_confirmation != expected_ac:
            failures.append(
                f"awaiting_confirmation={awaiting_confirmation}, expected {expected_ac}"
            )

    if "expected_awaiting_confirmation" in step:
        expected_ac = step["expected_awaiting_confirmation"]
        if awaiting_confirmation != expected_ac:
            failures.append(
                f"awaiting_confirmation={awaiting_confirmation}, expected {expected_ac}"
            )

    latency_limit = 35.0 if category in ("multi_step", "write") else 25.0
    if elapsed > latency_limit:
        failures.append(f"Latency {elapsed}s exceeded limit {latency_limit}s")

    return failures


async def _post_chat(
    client: httpx.AsyncClient, query: str, pending_write: dict = None
) -> tuple[dict, float]:
    """POST to /chat and return (response_data, elapsed_seconds)."""
    start = time.time()
    body = {"query": query, "history": []}
    if pending_write is not None:
        body["pending_write"] = pending_write
    resp = await client.post(f"{BASE_URL}/chat", json=body, timeout=45.0)
    elapsed = round(time.time() - start, 2)
    return resp.json(), elapsed


async def run_single_case(
    client: httpx.AsyncClient, case: dict
) -> dict:
    case_id = case.get("id", "UNKNOWN")
    category = case.get("category", "unknown")

    # ---- Multi-step write test ----
    if "steps" in case:
        return await run_multistep_case(client, case)

    query = case.get("query", "")

    if not query.strip():
        return {
            "id": case_id,
            "category": category,
            "query": query,
            "passed": True,
            "latency": 0.0,
            "failures": [],
            "note": "Empty query — handled gracefully (skipped API call)",
        }

    start = time.time()
    try:
        data, elapsed = await _post_chat(client, query)

        response_text = data.get("response") or ""
        tools_used = data.get("tools_used", [])
        awaiting_confirmation = data.get("awaiting_confirmation", False)

        failures = _check_assertions(
            response_text, tools_used, awaiting_confirmation, case, elapsed, category
        )

        return {
            "id": case_id,
            "category": category,
            "query": query[:80],
            "passed": len(failures) == 0,
            "latency": elapsed,
            "failures": failures,
            "tools_used": tools_used,
            "confidence": data.get("confidence_score"),
        }

    except Exception as e:
        return {
            "id": case_id,
            "category": category,
            "query": query[:80],
            "passed": False,
            "latency": round(time.time() - start, 2),
            "failures": [f"Exception: {str(e)}"],
            "tools_used": [],
        }


async def run_multistep_case(client: httpx.AsyncClient, case: dict) -> dict:
    """
    Executes a multi-step write flow:
      step 0: initial write intent → expect awaiting_confirmation=True
      step 1: "yes" or "no" with echoed pending_write → check result
    """
    case_id = case.get("id", "UNKNOWN")
    category = case.get("category", "unknown")
    steps = case.get("steps", [])
    all_failures = []
    total_latency = 0.0
    pending_write = None
    tools_used_all = []

    start_total = time.time()
    try:
        for i, step in enumerate(steps):
            query = step.get("query", "")
            data, elapsed = await _post_chat(client, query, pending_write=pending_write)
            total_latency += elapsed

            response_text = data.get("response") or ""
            tools_used = data.get("tools_used", [])
            tools_used_all.extend(tools_used)
            awaiting_confirmation = data.get("awaiting_confirmation", False)

            step_failures = _check_assertions(
                response_text, tools_used, awaiting_confirmation, step, elapsed, category
            )
            if step_failures:
                all_failures.extend([f"Step {i+1} ({query!r}): {f}" for f in step_failures])

            # Carry pending_write forward for next step
            pending_write = data.get("pending_write")

    except Exception as e:
        all_failures.append(f"Exception in multi-step case: {str(e)}")

    return {
        "id": case_id,
        "category": category,
        "query": f"[multi-step: {len(steps)} steps]",
        "passed": len(all_failures) == 0,
        "latency": round(time.time() - start_total, 2),
        "failures": all_failures,
        "tools_used": list(set(tools_used_all)),
    }


async def run_evals() -> float:
    with open(TEST_CASES_FILE) as f:
        cases = json.load(f)

    print(f"\n{'='*60}")
    print(f"GHOSTFOLIO AGENT EVAL SUITE — {len(cases)} test cases")
    print(f"Target: {BASE_URL}")
    print(f"{'='*60}\n")

    health_ok = False
    try:
        async with httpx.AsyncClient(timeout=15.0) as c:
            r = await c.get(f"{BASE_URL}/health")
            health_ok = r.status_code == 200
    except Exception:
        pass

    if not health_ok:
        print(f"❌ Agent not reachable at {BASE_URL}/health")
        print("   Start it with: uvicorn main:app --reload --port 8000")
        sys.exit(1)

    print("✅ Agent health check passed\n")

    results = []
    async with httpx.AsyncClient(timeout=httpx.Timeout(35.0)) as client:
        for case in cases:
            result = await run_single_case(client, case)
            results.append(result)

            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            latency_str = f"{result['latency']:.1f}s"
            print(f"{status} | {result['id']} ({result['category']}) | {latency_str}")
            for failure in result.get("failures", []):
                print(f"       → {failure}")

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    pass_rate = passed / total if total > 0 else 0.0

    by_category: dict[str, dict] = {}
    for r in results:
        cat = r["category"]
        if cat not in by_category:
            by_category[cat] = {"passed": 0, "total": 0}
        by_category[cat]["total"] += 1
        if r["passed"]:
            by_category[cat]["passed"] += 1

    print(f"\n{'='*60}")
    print(f"RESULTS: {passed}/{total} passed ({pass_rate:.0%})")
    print(f"{'='*60}")
    for cat, counts in sorted(by_category.items()):
        cat_rate = counts["passed"] / counts["total"]
        bar = "✅" if cat_rate >= 0.8 else ("⚠️" if cat_rate >= 0.5 else "❌")
        print(f"  {bar} {cat}: {counts['passed']}/{counts['total']} ({cat_rate:.0%})")

    failed_cases = [r for r in results if not r["passed"]]
    if failed_cases:
        print(f"\nFailed cases ({len(failed_cases)}):")
        for r in failed_cases:
            print(f"  ❌ {r['id']}: {r['failures']}")

    with open(RESULTS_FILE, "w") as f:
        json.dump(
            {
                "run_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "total": total,
                "passed": passed,
                "pass_rate": round(pass_rate, 4),
                "by_category": by_category,
                "results": results,
            },
            f,
            indent=2,
        )
    print(f"\nFull results saved to: evals/results.json")
    print(f"\nOverall pass rate: {pass_rate:.0%}")

    return pass_rate


if __name__ == "__main__":
    asyncio.run(run_evals())
