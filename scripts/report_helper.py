"""Helper for creating JustTheGist reports with model metadata."""

from datetime import datetime
from pathlib import Path


def create_report_with_metadata(
    title: str,
    content: str,
    extraction_model: str,
    synthesis_model: str,
    source_url: str = None,
    output_dir: str = "docs"
) -> Path:
    """Create a markdown report with model metadata.

    Args:
        title: Report title
        content: Main report content (markdown)
        extraction_model: Model used for extraction
        synthesis_model: Model used for synthesis
        source_url: Optional source URL
        output_dir: Output directory

    Returns:
        Path to created report file
    """
    # Create safe filename
    safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)
    safe_title = safe_title.replace(" ", "_")
    filename = f"{safe_title}.md"

    # Build frontmatter
    frontmatter = f"""---
title: {title}
date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
extraction_model: {extraction_model}
synthesis_model: {synthesis_model}
"""
    if source_url:
        frontmatter += f"source: {source_url}\n"

    frontmatter += "---\n\n"

    # Combine frontmatter and content
    full_content = frontmatter + content

    # Write file
    output_path = Path(output_dir) / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(full_content, encoding='utf-8')

    print(f"[+] Report saved to: {output_path}")
    print(f"    Extraction: {extraction_model}")
    print(f"    Synthesis: {synthesis_model}")

    return output_path


# Example usage
if __name__ == "__main__":
    report = create_report_with_metadata(
        title="Understanding FlaUI",
        content="""
# Understanding FlaUI

## Overview
FlaUI is a .NET library for UI automation...

## Key Features
- Cross-platform support
- WPF/WinForms compatibility
""",
        extraction_model="gemini",
        synthesis_model="codex",
        source_url="https://example.com/flaui-tutorial"
    )
    print(f"\nCreated: {report}")
