import re


def chunk_text(text: str, size: int = 800, overlap: int = 150) -> list[str]:
    """
    Split text into overlapping chunks.
    Attempts to cut on paragraph or sentence boundaries so the chunk does not break mid-sentence.
    """
    text = text.replace("\x00", "")
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return []

    chunks: list[str] = []
    n = len(text)
    start = 0

    while start < n:
        end = min(start + size, n)

        if end < n:
            window = text[start:end]
            cut = max(window.rfind("\n\n"), window.rfind(". "), window.rfind("\n"))
            # Use boundary cuts only when the chunk is more than half full
            if cut > size * 0.5:
                end = start + cut + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= n:
            break

        # Overlap: the next chunk starts from the end of the previous chunk
        start = max(end - overlap, start + 1)

    return chunks