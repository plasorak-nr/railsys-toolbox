"""Guard against module/function naming collisions.

This prevents patterns like ``foo.py`` defining ``def foo(...)`` at top level,
which can confuse API autodoc tooling when packages re-export symbols.
"""

import ast
from pathlib import Path

# Intentional CLI entrypoint pattern: rsys_toolbox/main.py defines a Typer
# command function named ``main``.
ALLOWED_MODULE_FUNCTION_COLLISIONS = {"main"}


def _find_top_level_module_function_collisions(package_root: Path) -> list[str]:
    """Return collisions where top-level function name equals module stem.

    Args:
        package_root: Root directory of the Python package to inspect.

    Returns:
        A list of human-readable collision descriptions.

    """
    collisions: list[str] = []
    for py_file in package_root.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue

        module_name = py_file.stem
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == module_name and module_name not in ALLOWED_MODULE_FUNCTION_COLLISIONS:
                rel_path = py_file.relative_to(package_root.parent).as_posix()
                collisions.append(f"{rel_path}:{node.lineno} -> function '{node.name}' matches module '{module_name}.py'")

    return collisions


def test_no_top_level_function_name_matches_module_name() -> None:
    """Prevent module/function same-name collisions in package source."""
    package_root = Path(__file__).resolve().parents[1] / "rsys_toolbox"
    collisions = _find_top_level_module_function_collisions(package_root)

    assert not collisions, "\n".join([
        "Found top-level function/module name collisions:",
        *collisions,
        "Rename the function or module to avoid API autodoc ambiguity.",
    ])
