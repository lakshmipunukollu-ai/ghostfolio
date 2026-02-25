import asyncio, yaml, httpx, time, json
from datetime import datetime

BASE = "http://localhost:8000"


async def run_check(client, case):
    if not case.get('query') and case.get('query') != '':
        return {**case, 'passed': True, 'note': 'skipped'}

    start = time.time()
    try:
        resp = await client.post(f"{BASE}/chat",
            json={"query": case.get('query', ''), "history": []},
            timeout=30.0)
        data = resp.json()
        elapsed = time.time() - start

        response_text = data.get('response', '').lower()
        tools_used = data.get('tools_used', [])

        failures = []

        # Check 1: Tool selection
        for tool in case.get('expected_tools', []):
            if tool not in tools_used:
                failures.append(f"TOOL SELECTION: Expected '{tool}' — got {tools_used}")

        # Check 2: Content validation (must_contain)
        for phrase in case.get('must_contain', []):
            if phrase.lower() not in response_text:
                failures.append(f"CONTENT: Missing required phrase '{phrase}'")

        # Check 3: must_contain_one_of
        one_of = case.get('must_contain_one_of', [])
        if one_of and not any(p.lower() in response_text for p in one_of):
            failures.append(f"CONTENT: Must contain one of {one_of}")

        # Check 4: Negative validation (must_not_contain)
        for phrase in case.get('must_not_contain', []):
            if phrase.lower() in response_text:
                failures.append(f"NEGATIVE: Contains forbidden phrase '{phrase}'")

        # Check 5: Latency (30s budget for complex multi-tool queries)
        limit = 30.0
        if elapsed > limit:
            failures.append(f"LATENCY: {elapsed:.1f}s exceeded {limit}s")

        passed = len(failures) == 0
        return {
            'id': case['id'],
            'category': case.get('category', ''),
            'difficulty': case.get('difficulty', ''),
            'subcategory': case.get('subcategory', ''),
            'passed': passed,
            'latency': round(elapsed, 2),
            'tools_used': tools_used,
            'failures': failures,
            'query': case.get('query', '')[:60]
        }

    except Exception as e:
        return {
            'id': case['id'],
            'passed': False,
            'failures': [f"EXCEPTION: {str(e)}"],
            'latency': 0,
            'tools_used': []
        }


async def main():
    # Load both files
    with open('evals/golden_sets.yaml') as f:
        golden = yaml.safe_load(f)
    with open('evals/labeled_scenarios.yaml') as f:
        scenarios = yaml.safe_load(f)

    print("=" * 60)
    print("GHOSTFOLIO AGENT — GOLDEN SETS")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # Run golden sets first
        golden_results = []
        for case in golden:
            r = await run_check(client, case)
            golden_results.append(r)
            status = "✅ PASS" if r['passed'] else "❌ FAIL"
            print(f"{status} | {r['id']} | {r.get('latency',0):.1f}s | tools: {r.get('tools_used', [])}")
            if not r['passed']:
                for f in r['failures']:
                    print(f"       → {f}")

        golden_pass = sum(r['passed'] for r in golden_results)
        print(f"\nGOLDEN SETS: {golden_pass}/{len(golden_results)} passed")

        if golden_pass < len(golden_results):
            print("\n⚠️  GOLDEN SET FAILURES — something is fundamentally broken.")
            print("Fix these before looking at labeled scenarios.\n")

            # Still save partial results and continue to scenarios for full picture
            all_results = {
                'timestamp': datetime.utcnow().isoformat(),
                'golden_sets': golden_results,
                'labeled_scenarios': [],
                'summary': {
                    'golden_pass_rate': f"{golden_pass}/{len(golden_results)}",
                    'scenario_pass_rate': "not run",
                }
            }
            with open('evals/golden_results.json', 'w') as f:
                json.dump(all_results, f, indent=2)
            print(f"Partial results → evals/golden_results.json")
            return

        print("\n✅ All golden sets passed. Running labeled scenarios...\n")
        print("=" * 60)
        print("LABELED SCENARIOS — COVERAGE ANALYSIS")
        print("=" * 60)

        # Run labeled scenarios
        scenario_results = []
        for case in scenarios:
            r = await run_check(client, case)
            scenario_results.append(r)
            status = "✅ PASS" if r['passed'] else "❌ FAIL"
            diff = case.get('difficulty', '')
            cat = case.get('subcategory', '')
            print(f"{status} | {r['id']} | {diff:15} | {cat:30} | {r.get('latency',0):.1f}s")
            if not r['passed']:
                for f in r['failures']:
                    print(f"       → {f}")

        scenario_pass = sum(r['passed'] for r in scenario_results)

        # Results by difficulty
        print(f"\n{'='*60}")
        print(f"RESULTS BY DIFFICULTY:")
        for diff in ['straightforward', 'ambiguous', 'edge_case', 'adversarial']:
            subset = [r for r in scenario_results if r.get('difficulty') == diff]
            if subset:
                p = sum(r['passed'] for r in subset)
                print(f"  {diff:20}: {p}/{len(subset)}")

        print(f"\nSCENARIOS: {scenario_pass}/{len(scenario_results)} passed")
        print(f"OVERALL: {golden_pass + scenario_pass}/{len(golden_results) + len(scenario_results)} passed")

        # Save results
        all_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'golden_sets': golden_results,
            'labeled_scenarios': scenario_results,
            'summary': {
                'golden_pass_rate': f"{golden_pass}/{len(golden_results)}",
                'scenario_pass_rate': f"{scenario_pass}/{len(scenario_results)}",
            }
        }
        with open('evals/golden_results.json', 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"\nFull results → evals/golden_results.json")


asyncio.run(main())
