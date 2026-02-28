"""
Runs the eval suite and saves results to a JSON history file for regression tracking.
"""
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_and_save_evals():
    """Runs the eval suite and saves results to a JSON history file for regression tracking."""
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)

    # Run pytest from project root (parent of agent)
    project_root = Path(__file__).parent.parent.parent
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "agent/evals",
            "-v",
            "--tb=short",
            "-q",
        ],
        capture_output=True,
        text=True,
        cwd=project_root,
    )

    # Parse results from pytest output
    output = result.stdout + result.stderr
    lines = output.split("\n")

    passed = sum(1 for l in lines if " PASSED" in l)
    failed = sum(1 for l in lines if " FAILED" in l)
    errors = sum(1 for l in lines if " ERROR" in l)

    # Fallback: parse summary line like "182 passed, 1 warning in 30.32s"
    if passed == 0 and failed == 0 and "passed" in output.lower():
        m = re.search(r"(\d+)\s+passed", output)
        if m:
            passed = int(m.group(1))
        m = re.search(r"(\d+)\s+failed", output)
        if m:
            failed = int(m.group(1))
        m = re.search(r"(\d+)\s+error", output, re.I)
        if m:
            errors = int(m.group(1))

    total = passed + failed + errors
    pass_rate = round(passed / total * 100, 1) if total > 0 else 0

    run_record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "total": total,
        "pass_rate_pct": pass_rate,
        "status": "PASS" if pass_rate >= 80 else "FAIL",
        "regression": False,
    }

    # Load history
    history_file = results_dir / "eval_history.json"
    history = []
    if history_file.exists():
        try:
            history = json.loads(history_file.read_text())
        except Exception:
            history = []

    # Check for regression
    if history:
        last = history[-1]
        if pass_rate < last.get("pass_rate_pct", 100):
            run_record["regression"] = True
            run_record["regression_detail"] = (
                f"Pass rate dropped from "
                f"{last['pass_rate_pct']}% to {pass_rate}%"
            )

    history.append(run_record)
    history_file.write_text(json.dumps(history, indent=2))

    # Also save latest run separately
    latest_file = results_dir / "latest_run.json"
    latest_file.write_text(json.dumps(run_record, indent=2))

    print(f"\n{'='*50}")
    print(f"EVAL RUN: {run_record['timestamp']}")
    print(f"Passed:   {passed}/{total} ({pass_rate}%)")
    print(f"Status:   {run_record['status']}")
    if run_record.get("regression"):
        print(f"⚠️  REGRESSION: {run_record['regression_detail']}")
    print(f"History:  {len(history)} runs saved")
    print(f"{'='*50}\n")

    return run_record


if __name__ == "__main__":
    run_and_save_evals()
