"""Execute a supplied serial-GPU model, not an archived performance table."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from reference import search

parser = argparse.ArgumentParser()
parser.add_argument('input', type=Path)
args = parser.parse_args()
case = json.loads(args.input.read_text(encoding='utf-8'))
print(json.dumps(search(case, case['beneficiary'], case.get('k', 3)), indent=2))
