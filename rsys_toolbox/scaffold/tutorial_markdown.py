"""Helpers for extracting and executing Python code blocks from markdown.

This is primarily used to keep tutorial tests aligned with the tutorial pages
themselves, so the documentation remains the single source of truth.
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any

import yaml


def discover_mkdocs_section_pages(mkdocs_file: Path, section_name: str) -> list[Path]:
    """Resolve markdown pages listed under a named MkDocs nav section.

    Args:
        mkdocs_file: Path to the MkDocs configuration file.
        section_name: Navigation section name to resolve.

    Returns:
        Markdown file paths in nav order for the requested section.

    Raises:
        ValueError: If the section is not present in the MkDocs nav.

    """
    config = yaml.safe_load(mkdocs_file.read_text(encoding="utf-8"))
    nav = config.get("nav", [])
    docs_dir = mkdocs_file.parent / "docs"

    for item in nav:
        if isinstance(item, dict) and section_name in item:
            return _resolve_nav_entry(item[section_name], docs_dir)

    raise ValueError(f"Section {section_name!r} not found in {mkdocs_file}")


def extract_python_blocks(markdown_file: Path) -> list[str]:
    """Extract fenced Python code blocks from a markdown file.

    Args:
        markdown_file: Markdown file to scan.

    Returns:
        A list of dedented Python code block strings in source order.

    """
    blocks: list[str] = []
    current_block: list[str] = []
    in_python_block = False

    for line in markdown_file.read_text(encoding="utf-8").splitlines(keepends=True):
        stripped = line.strip()

        if not in_python_block and stripped == "```python":
            in_python_block = True
            current_block = []
            continue

        if in_python_block and stripped == "```":
            block = textwrap.dedent("".join(current_block))
            sanitized = _sanitize_notebook_only_lines(block)
            if sanitized.strip():
                blocks.append(sanitized)
            in_python_block = False
            continue

        if in_python_block:
            current_block.append(line)

    return blocks


def execute_markdown_python(markdown_files: list[Path], namespace: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute fenced Python code blocks from markdown files in order.

    Args:
        markdown_files: Markdown files whose Python blocks should be executed.
        namespace: Optional shared globals dict used for execution.

    Returns:
        The execution namespace after all blocks have run.

    """
    exec_namespace: dict[str, Any] = {} if namespace is None else namespace

    for markdown_file in markdown_files:
        for block_index, block in enumerate(extract_python_blocks(markdown_file), start=1):
            compiled = compile(block, f"{markdown_file}#block-{block_index}", "exec")
            exec(compiled, exec_namespace)

    return exec_namespace


def discover_tutorial_pages(mkdocs_file: Path | None = None) -> list[Path]:
    """Return tutorial pages from the MkDocs navigation in nav order.

    Args:
        mkdocs_file: Path to the MkDocs YAML configuration file. Defaults to
            ``mkdocs.yaml`` in the current working directory.

    Returns:
        Ordered list of tutorial markdown page paths.

    """
    resolved_mkdocs = mkdocs_file or Path("mkdocs.yaml")
    return discover_mkdocs_section_pages(resolved_mkdocs, "Tutorial")


def _sanitize_notebook_only_lines(block: str) -> str:
    """Remove notebook-only syntax so blocks can be executed as plain Python.

    Args:
        block: A string containing one or more lines of Python code, potentially
            including notebook-only magic commands.

    Returns:
        The block with notebook-only lines (e.g. IPython magics) stripped out.

    """
    kept_lines = [line for line in block.splitlines() if not line.lstrip().startswith("%")]
    return "\n".join(kept_lines) + ("\n" if kept_lines else "")


def _resolve_nav_entry(entry: object, docs_dir: Path) -> list[Path]:
    """Flatten a MkDocs nav entry into markdown paths.

    Args:
        entry: A MkDocs nav entry, which may be a ``str`` (file path), a
            ``list`` of entries, or a ``dict`` mapping section titles to entries.
        docs_dir: Root directory relative to which string entries are resolved.

    Returns:
        Resolved absolute paths to markdown files under ``docs_dir``.

    Raises:
        TypeError: If ``entry`` is not a ``str``, ``list``, or ``dict``.

    """
    if isinstance(entry, str):
        return [docs_dir / entry]

    if isinstance(entry, list):
        resolved: list[Path] = []
        for item in entry:
            resolved.extend(_resolve_nav_entry(item, docs_dir))
        return resolved

    if isinstance(entry, dict):
        resolved = []
        for value in entry.values():
            resolved.extend(_resolve_nav_entry(value, docs_dir))
        return resolved

    raise TypeError(f"Unsupported MkDocs nav entry type: {type(entry)!r}")
