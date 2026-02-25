import yaml


def generate_matrix():
    with open('evals/labeled_scenarios.yaml') as f:
        scenarios = yaml.safe_load(f)

    tools = ['portfolio_analysis', 'transaction_query', 'compliance_check',
             'market_data', 'tax_estimate', 'transaction_categorize']
    difficulties = ['straightforward', 'ambiguous', 'edge_case', 'adversarial']

    # Build matrix: difficulty x tool
    matrix = {d: {t: 0 for t in tools} for d in difficulties}

    for s in scenarios:
        diff = s.get('difficulty', 'straightforward')
        for tool in s.get('expected_tools', []):
            if tool in tools and diff in matrix:
                matrix[diff][tool] += 1

    # Print matrix
    header = f"{'':20}" + "".join(f"{t[:12]:>14}" for t in tools)
    print(header)
    print("-" * (20 + 14 * len(tools)))

    for diff in difficulties:
        row = f"{diff:20}"
        for tool in tools:
            count = matrix[diff][tool]
            row += f"{'--' if count == 0 else str(count):>14}"
        print(row)

    # Highlight gaps
    print("\nCOVERAGE GAPS (empty cells = write tests here):")
    for diff in difficulties:
        for tool in tools:
            if matrix[diff][tool] == 0:
                print(f"  Missing: {diff} x {tool}")


if __name__ == "__main__":
    generate_matrix()
