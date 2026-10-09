"""Data acquisition service: find the source documents, extract their text, chunk it."""
import hashlib
import os
import re
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import pymupdf

from . import config

BULLET = re.compile(r"^\s*(?:[•●▪■◦∙·]|[*\-–]\s)")
HEADING = re.compile(r"^[A-Z][A-Z &/]{2,38}$")


# Resume chunks are terse ("Oasis Infobytes / Remote / ..."), while visitors ask in
# everyday words ("where has she worked?"). These hints are added to the text that
# gets embedded - not to what is shown - so the two meet in vector space.
SECTION_HINTS = {
    "contact": "Contact details: how to get in touch, email, phone number, location, LinkedIn, GitHub.",
    "summary": "About: a short introduction to this person, their profile, overview and background.",
    "objective": "About: a short introduction to this person, their profile, overview and background.",
    "education": "Education: university, degree, where and what they studied, graduation year.",
    "skill": "Skills: programming languages, technologies, frameworks and tools they know.",
    "experience": "Work experience: a job or internship, the role, company and responsibilities.",
    "project": "Projects: a project they built, what it does and its tech stack.",
    "certif": "Certifications: certificates and courses completed.",
    "award": "Awards, honours and achievements.",
}


@dataclass
class Chunk:
    id: int
    text: str
    section: str
    source: str

    def to_dict(self) -> dict:
        return asdict(self)

    def embedding_text(self) -> str:
        section = self.section.lower()
        hint = next((hint for key, hint in SECTION_HINTS.items() if key in section), "")
        return f"{hint}\n{self.text}".strip()


def source_files() -> list[Path]:
    """The resume plus any supported file in the extra docs folder."""
    files = [config.RESUME_PATH] if config.RESUME_PATH.is_file() else []
    if config.EXTRA_DOCS_DIR.is_dir():
        files += sorted(
            p
            for p in config.EXTRA_DOCS_DIR.iterdir()
            if p.is_file() and p.suffix.lower() in config.SUPPORTED_EXTENSIONS
        )
    return files


def fingerprint(files: list[Path]) -> str:
    """Content hash of every source file - changes whenever the data changes.

    The chunking settings are hashed too, so a persisted index built with
    different settings is never reused.
    """
    settings = (SECTION_HINTS, config.MAX_CHUNK_WORDS, config.CHUNK_OVERLAP_WORDS)
    digest = hashlib.sha256(repr(settings).encode())
    for path in files:
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def extract_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        with pymupdf.open(path) as document:
            return "\n".join(page.get_text() for page in document)
    return path.read_text(encoding="utf-8", errors="ignore")


def _window(words: list[str]) -> list[str]:
    """Split an over-long passage into overlapping word windows."""
    if len(words) <= config.MAX_CHUNK_WORDS:
        return [" ".join(words)]
    step = config.MAX_CHUNK_WORDS - config.CHUNK_OVERLAP_WORDS
    return [
        " ".join(words[start : start + config.MAX_CHUNK_WORDS])
        for start in range(0, len(words), step)
        if start == 0 or start + config.CHUNK_OVERLAP_WORDS < len(words)
    ]


def _split_entries(lines: list[str]) -> list[list[str]]:
    """Split a section into entries (one job, one project...).

    A new entry starts at the first non-bullet line that follows a bullet line,
    which is how resumes lay out "title / bullets / title / bullets".
    """
    entries: list[list[str]] = [[]]
    previous_was_bullet = False
    for line in lines:
        is_bullet = bool(BULLET.match(line))
        if previous_was_bullet and not is_bullet:
            entries.append([])
        entries[-1].append(line)
        previous_was_bullet = is_bullet
    return [entry for entry in entries if entry]


def split_sections(text: str) -> list[tuple[str, list[str]]]:
    """Group lines under their ALL-CAPS section headings.

    Everything before the first heading becomes "Contact" on a resume (name and
    contact line) and "Overview" on any other document.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    # A resume opens with the person's name in capitals followed by their email;
    # that first line is a name, not a section heading.
    has_contact_header = any("@" in line for line in lines[1:4])
    sections: list[tuple[str, list[str]]] = [("Contact" if has_contact_header else "Overview", [])]
    for index, line in enumerate(lines):
        if HEADING.match(line) and not (index == 0 and has_contact_header):
            sections.append((line.title(), []))
        else:
            sections[-1][1].append(line)
    return [(title, body) for title, body in sections if body]


def chunk_document(text: str) -> list[tuple[str, str]]:
    """Return (section, chunk_text) pairs for one document."""
    chunks: list[tuple[str, str]] = []
    for section, lines in split_sections(text):
        for entry in _split_entries(lines):
            # Split on spaces only, so line breaks survive inside each window.
            for piece in _window(" \n".join(entry).split(" ")):
                piece = piece.replace(" \n", "\n")
                # Prefix each chunk with its section so it stays meaningful (and
                # retrievable) on its own.
                chunks.append((section, f"{section}\n{piece}"))
    return chunks


def acquire() -> tuple[list[Chunk], str, list[str]]:
    """Run acquisition end to end: (chunks, fingerprint, source names)."""
    files = source_files()
    if not files:
        raise FileNotFoundError(
            f"No source documents found. Expected the resume at {config.RESUME_PATH}"
        )
    chunks: list[Chunk] = []
    for path in files:
        for section, text in chunk_document(extract_text(path)):
            chunks.append(Chunk(id=len(chunks), text=text, section=section, source=path.name))
    if not chunks:
        raise ValueError("Source documents contained no extractable text.")
    return chunks, fingerprint(files), [path.name for path in files]


def replace_resume(data: bytes) -> Path | None:
    """Swap in a newly uploaded resume PDF. Returns where the old one was backed up.

    The upload is validated first, so a broken file never replaces a working resume.
    """
    try:
        with pymupdf.open(stream=data, filetype="pdf") as document:
            text = "\n".join(page.get_text() for page in document)
    except Exception as error:
        raise ValueError("That file is not a readable PDF.") from error
    if not text.strip():
        raise ValueError("No text found in that PDF. Scanned or image-only resumes can't be indexed.")

    backup = None
    if config.RESUME_PATH.is_file():
        config.RESUME_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = config.RESUME_BACKUP_DIR / f"{config.RESUME_PATH.stem}-{stamp}.pdf"
        shutil.copy2(config.RESUME_PATH, backup)
    # Write next to the target, then rename, so the watcher never sees a half-written file.
    temporary = config.RESUME_PATH.with_suffix(".uploading")
    temporary.write_bytes(data)
    os.replace(temporary, config.RESUME_PATH)
    return backup
