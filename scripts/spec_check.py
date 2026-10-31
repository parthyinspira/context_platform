#!/usr/bin/env python3
"""Check the structure of a spec change folder. Usage: spec_check.py spec/changes/kan-<n>-<slug> [--stage plan|verify]"""
import re
import sys
from pathlib import Path


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    stage = "verify" if "--stage=verify" in sys.argv or "verify" in sys.argv else "plan"
    if not args:
        print("usage: spec_check.py <change-folder> [--stage=verify]")
        return 2
    folder = Path(args[0])
    errors: list[str] = []

    if not re.fullmatch(r"kan-\d+-[a-z0-9-]+", folder.name):
        errors.append(f"folder name '{folder.name}' must match kan-<n>-<slug>")
    for name in ("proposal.md", "tasks.md"):
        if not (folder / name).is_file():
            errors.append(f"missing {name}")
    deltas = sorted((folder / "specs").glob("*.md")) if (folder / "specs").is_dir() else []
    if not deltas:
        errors.append("missing specs/<capability>.md delta")
    for d in deltas:
        text = d.read_text()
        if not re.search(r"^## (ADDED|MODIFIED|REMOVED) Requirements", text, re.M):
            errors.append(f"{d.name}: no ADDED/MODIFIED/REMOVED section")
        for block in re.split(r"^### Requirement:", text, flags=re.M)[1:]:
            title = block.splitlines()[0].strip()
            if "SHALL" not in block and "Reason:" not in block:
                errors.append(f"{d.name}: requirement '{title}' has no SHALL")
            if "#### Scenario:" not in block and "Reason:" not in block:
                errors.append(f"{d.name}: requirement '{title}' has no scenario")

    proposal = folder / "proposal.md"
    if proposal.is_file():
        p = proposal.read_text()
        if "Acceptance criteria" not in p:
            errors.append("proposal.md: no Acceptance criteria section")
        if "Approved by:" not in p or re.search(r"Approved by:\s*<", p) or re.search(r"Approved by:\s*$", p, re.M):
            errors.append("proposal.md: plan not approved (fill 'Approved by')")

    if stage == "verify":
        tasks = folder / "tasks.md"
        if tasks.is_file() and re.search(r"^- \[ \]", tasks.read_text(), re.M):
            errors.append("tasks.md: unticked tasks remain")
        v = folder / "verification.md"
        if not v.is_file():
            errors.append("missing verification.md")
        else:
            vt = v.read_text()
            if not re.search(r"^Status:\s*PASS", vt, re.M):
                errors.append("verification.md: status is not PASS")
            if "| | | |" in vt:
                errors.append("verification.md: empty evidence rows remain")

    if errors:
        print("spec_check FAILED")
        for e in errors:
            print(" -", e)
        return 1
    print(f"spec_check OK ({stage}): {folder}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
