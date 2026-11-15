"""IP06 - daily update script (trial).

Reads the Git history of the PGA GenGA archive and writes one record per
recorded version to data/versions.json. The dashboard reads that file.

Run:  python3 update.py <path to the cloned genai-eu-versions folder>
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "genai-eu-versions"
OUTPUT = Path("data/versions.json")

KINDS = {
    "First record": "first record",
    "Record new changes": "policy change",
    "Apply technical or declaration upgrade": "technical",
}


def kind_of(message):
    for start, kind in KINDS.items():
        if message.startswith(start):
            return kind
    return None  # README updates etc. - not a policy version


log = subprocess.run(
    ["git", "-C", str(REPO), "log", "--date=short",
     "--format=@%ad|%h|%s", "--name-only"],
    capture_output=True, text=True, check=True,
).stdout

records = []
date = commit = kind = None
for line in log.splitlines():
    if line.startswith("@"):                      # a commit line
        date, commit, message = line[1:].split("|", 2)
        kind = kind_of(message)
    elif line.endswith(".md") and "/" in line and kind:   # a document file
        provider, document = line.split("/", 1)
        records.append({
            "provider": provider,
            "document": document[:-3],            # drop ".md"
            "date": date,
            "commit": commit,
            "kind": kind,
        })

result = {
    "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    "source": "https://github.com/OpenTermsArchive/genai-eu-versions",
    "providers": len({r["provider"] for r in records}),
    "documents": len({(r["provider"], r["document"]) for r in records}),
    "versions": len(records),
    "latest_change": max(r["date"] for r in records),
    "records": records,
}

OUTPUT.parent.mkdir(exist_ok=True)
OUTPUT.write_text(json.dumps(result, indent=1, ensure_ascii=False))
print(f"{result['providers']} providers, {result['documents']} documents, "
      f"{result['versions']} versions, latest change {result['latest_change']}")
