import sys
import os
import json
import asyncio
# Ensure repo root is on sys.path for imports when running this script directly
sys.path.insert(0, os.getcwd())
from main import system_diagnostics


def main():
    diag = asyncio.run(system_diagnostics())
    with open('reports/final_readiness_matrix.json', 'w', encoding='utf-8') as f:
        json.dump(diag, f, indent=2, ensure_ascii=False)

    ci_readiness = {
        'integration_ready': diag.get('integration_ready'),
        'integration_score': diag.get('integration_score'),
        'readiness_reason': diag.get('readiness_reason')
    }
    with open('reports/final_ci_readiness.json', 'w', encoding='utf-8') as f:
        json.dump(ci_readiness, f, indent=2, ensure_ascii=False)

    print('Reports written to reports/final_readiness_matrix.json and reports/final_ci_readiness.json')

if __name__ == '__main__':
    main()
