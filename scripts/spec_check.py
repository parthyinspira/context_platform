#!/usr/bin/env python3
"""Check the structure of a spec change folder.

Usage: spec_check.py spec/changes/kan-<n>-<slug> [--stage=verify]

Full mode: proposal.md, tasks.md, specs/<capability>.md deltas (and verification.md at verify stage).
Lite mode (folder has plan.md and no proposal.md): plan.md and verification.md only.
"""
import re
import sys
from pathlib import Path

EMPTY_ROW = re.compile(r"^\|(\s*\|)+\s*$", re.M)


def approved(text: str) -> bool:
    m = re.search(r"Approved by:[ \t]*(.*)", text)
    if not m:
        return False
    value = m.group(1).strip()
    return bool(value) and not value.startswith("<")


def check_verification(folder: Path, errors: list[str]) -> None:
    v = folder / "verification.md"
    if not v.is_file():
        errors.append("missing verification.md")
        return
    vt = v.read_text()
    if not re.search(r"^Status:\s*PASS", vt, re.M):
        errors.append("verification.md: status is not PASS")
    if "| | | |" in vt or EMPTY_ROW.search(vt):
        errors.append("verification.md: empty evidence rows remain")


def check_full(folder: Path, stage: str, errors: list[str]) -> None:
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
        if not approved(p):
            errors.append("proposal.md: plan not approved (fill 'Approved by')")
    if stage == "verify":
        tasks = folder / "tasks.md"
        if tasks.is_file() and re.search(r"^- \[ \]", tasks.read_text(), re.M):
            errors.append("tasks.md: unticked tasks remain")
        check_verification(folder, errors)


def check_lite(folder: Path, stage: str, errors: list[str]) -> None:
    plan = folder / "plan.md"
    text = plan.read_text()
    if "Acceptance criteria" not in text:
        errors.append("plan.md: no Acceptance criteria section")
    if not re.search(r"^- \[[ xX]\]", text, re.M):
        errors.append("plan.md: no task checklist")
    if not approved(text):
        errors.append("plan.md: plan not approved (fill 'Approved by')")
    if stage == "verify":
        if re.search(r"^- \[ \]", text, re.M):
            errors.append("plan.md: unticked tasks remain")
        check_verification(folder, errors)


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
    lite = (folder / "plan.md").is_file() and not (folder / "proposal.md").is_file()
    if lite:
        check_lite(folder, stage, errors)
    else:
        check_full(folder, stage, errors)
    if errors:
        print("spec_check FAILED")
        for e in errors:
            print(" -", e)
        return 1
    print(f"spec_check OK ({'lite ' if lite else ''}{stage}): {folder}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
