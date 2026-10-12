"""Cell notes in the master Google Sheet, shared by the people and scripts that write them.

One cell has one note, and several writers share it: people, validate_data.py's quality hints
("[Auto-check]") and sheet_corrections.py's record of what it changed ("[Source check]"). Each
script replaces only its own paragraph and keeps every other one, so what a person wrote, including
a [Keep] pin, survives every automated run.
"""

PIN = '[keep]'


def is_pinned(note):
    """A cell whose note says [Keep] (any case) is never changed automatically."""
    return PIN in (note or '').lower()


def merge_note(existing, prefix, paragraph):
    """existing, with every paragraph that starts with prefix replaced by paragraph (or dropped when
    paragraph is empty). Other paragraphs keep their text and order."""
    kept = [p for p in (existing or '').split('\n\n') if p.strip() and not p.lstrip().startswith(prefix)]
    if paragraph:
        kept.append(paragraph)
    return '\n\n'.join(kept)
