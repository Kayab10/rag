# document_loader.py - Loads text and metadata from supported document types.
#
# Input  : file path (str | Path)
# Output : list of dicts  →  {"text": "...", "metadata": {"file_name": "...", "page_number": 1}}

from pathlib import Path
from typing import Any


# ── Type alias ────────────────────────────────────────────────────────────────
# Each "document" is a dict with two keys:
#   text     : the extracted string content
#   metadata : source info (file name, page number, etc.)
Document = dict[str, Any]


# ── Internal helpers ──────────────────────────────────────────────────────────

def _load_txt(path: Path) -> list[Document]:
    """Load a plain-text or markdown file as a single document."""
    text = path.read_text(encoding="utf-8")
    return [
        {
            "text": text,
            "metadata": {
                "file_name": path.name,
                "page_number": 1,   # flat files have no pages; use 1 as default
            },
        }
    ]


def _load_pdf(path: Path) -> list[Document]:
    """Load a PDF file, returning one document per page."""
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise ImportError("pypdf is required for PDF loading. Run: pip install pypdf") from e

    reader = PdfReader(str(path))
    documents: list[Document] = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():          # skip blank pages
            documents.append(
                {
                    "text": text,
                    "metadata": {
                        "file_name": path.name,
                        "page_number": page_number,
                    },
                }
            )

    return documents


# ── Public API ────────────────────────────────────────────────────────────────

# Map each supported extension to its loader function
_LOADERS = {
    ".txt": _load_txt,
    ".md": _load_txt,   # markdown is plain text for our purposes
    ".pdf": _load_pdf,
}

SUPPORTED_EXTENSIONS = list(_LOADERS.keys())


def load_document(file_path: str | Path) -> list[Document]:
    """
    Load a document from *file_path* and return extracted text + metadata.

    Parameters
    ----------
    file_path : str | Path
        Absolute or relative path to the file.

    Returns
    -------
    list[Document]
        Each item is {"text": "...", "metadata": {"file_name": "...", "page_number": N}}.
        PDFs return one item per page; .txt/.md return a single item.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the file extension is not supported.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = path.suffix.lower()
    if ext not in _LOADERS:
        raise ValueError(
            f"Unsupported file type '{ext}'. "
            f"Supported types: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    loader = _LOADERS[ext]  # loader is a var that store function from above
    documents = loader(path)

    return documents


def load_documents_from_folder(folder_path: str | Path) -> list[Document]:
    """
    Recursively load all supported documents from *folder_path*.

    Skips files with unsupported extensions silently.

    Parameters
    ----------
    folder_path : str | Path
        Path to the directory to scan.

    Returns
    -------
    list[Document]
        Combined list of documents from all supported files found.
    """
    folder = Path(folder_path)

    if not folder.is_dir():
        raise NotADirectoryError(f"Not a directory: {folder}")

    documents: list[Document] = []

    for file_path in sorted(folder.rglob("*")):
        if file_path.is_file() and file_path.suffix.lower() in _LOADERS:
            documents.extend(load_document(file_path))

    return documents
