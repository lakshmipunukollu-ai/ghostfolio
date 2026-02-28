# Finance AI Agent — Public Eval Dataset

183 test cases for AI agents built on personal finance and portfolio management software.

Built on top of Ghostfolio — an open source wealth management platform.

Released publicly as a resource for developers building finance AI agents.

## Test Categories

| Category | Count |
|----------|-------|
| Happy Path | 20 |
| Edge Cases | 14 |
| Adversarial | 14 |
| Multi-Step | 13 |
| Other | 122 |
| **Total** | **183** |

## How To Run
```bash
git clone https://github.com/lakshmipunukollu-ai/ghostfolio
cd ghostfolio
git checkout submission/final
pip install -r agent/requirements.txt
python -m pytest agent/evals/ -v
```

## Test Structure

Every test in test_eval_dataset.py follows:
```python
# TYPE: happy_path | edge_case | adversarial | multi_step
# INPUT: what is being tested
# EXPECTED: what the tool should return
# CRITERIA: the specific assertion
def test_name():
    from tools.tool_name import function_name
    result = function_name(params)
    assert "key" in result
```

## Results

- Tests: 183
- Pass rate: 100%
- Runtime: ~30 seconds

## Contribute

Submit a PR with new test cases.
Follow the TYPE/INPUT/EXPECTED/CRITERIA pattern.

## License

MIT

## Author

Priya Lakshmipunukollu — AgentForge, February 2026
https://github.com/lakshmipunukollu-ai/ghostfolio
