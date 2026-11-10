"""Write source hash without timestamps, absolute paths or other varying data."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root / "src/calc.py"
output = root / "dist/build_manifest.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(
    json.dumps({"source": "src/calc.py", "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}, indent=2) + "\n",
    encoding="utf-8",
)
