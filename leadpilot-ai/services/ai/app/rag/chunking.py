import re
from typing import List, Dict, Any


def split_markdown_by_headings(content: str) -> List[Dict[str, Any]]:
    """
    Split markdown document by headings (#, ##, ###), keeping track of the heading path.
    """
    lines = content.split('\n')
    sections: List[Dict[str, Any]] = []
    current_heading = "General"
    current_lines: List[str] = []

    heading_pattern = re.compile(r'^(#{1,4})\s+(.+)$')

    for line in lines:
        match = heading_pattern.match(line)
        if match:
            if current_lines:
                text = '\n'.join(current_lines).strip()
                if text:
                    sections.append({
                        "heading": current_heading,
                        "text": text
                    })
                current_lines = []
            current_heading = match.group(2).strip()
        else:
            current_lines.append(line)

    if current_lines:
        text = '\n'.join(current_lines).strip()
        if text:
            sections.append({
                "heading": current_heading,
                "text": text
            })

    return sections


def chunk_text(
    sections: List[Dict[str, Any]],
    chunk_size: int = 800,
    chunk_overlap: int = 100
) -> List[Dict[str, Any]]:
    """
    Produce chunks of target size (600 to 900 chars) with overlap, preserving heading metadata.
    """
    chunks: List[Dict[str, Any]] = []

    for sec in sections:
        heading = sec["heading"]
        text = sec["text"]

        if len(text) <= chunk_size:
            chunks.append({
                "content": f"### {heading}\n{text}",
                "heading": heading,
                "char_count": len(text)
            })
            continue

        # Split into smaller windows with overlap
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk_slice = text[start:end]

            # Try to break on newline or space rather than mid-word
            if end < len(text):
                last_space = chunk_slice.rfind(' ')
                if last_space > chunk_size // 2:
                    chunk_slice = chunk_slice[:last_space]
                    end = start + last_space

            chunk_content = f"### {heading}\n{chunk_slice.strip()}"
            chunks.append({
                "content": chunk_content,
                "heading": heading,
                "char_count": len(chunk_content)
            })

            start = end - chunk_overlap

    return chunks
