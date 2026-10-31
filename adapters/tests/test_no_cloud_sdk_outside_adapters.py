"""Enforces CLAUDE.md: "No direct imports of cloud SDKs outside adapters/."""
import ast
from pathlib import Path

CLOUD_SDK_MODULES = {
    "google.cloud",
    "boto3",
    "azure",
    "anthropic",
    "openai",
}
REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = ["api", "ui", "scheduler", "embeddings", "migrations", "scripts"]


def _imports_in(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_no_cloud_sdk_imports_outside_adapters() -> None:
    violations = []
    for scan_dir in SCAN_DIRS:
        root = REPO_ROOT / scan_dir
        if not root.is_dir():
            continue
        for py_file in root.rglob("*.py"):
            for imported in _imports_in(py_file):
                if any(imported == sdk or imported.startswith(sdk + ".") for sdk in CLOUD_SDK_MODULES):
                    violations.append(f"{py_file}: {imported}")
    assert violations == [], f"cloud SDK imports found outside adapters/: {violations}"
