"""Cell notes in the master Google Sheet, shared by the people and scripts that write them.

One cell has one note, and several writers share it: people, validate_data.py's quality hints
("[Auto-check]") and sheet_corrections.py's record of what it changed ("[Source check]"). Each
script replaces only its own paragraph and keeps every other one. A paragraph runs until the next
blank line, so a person's text belongs in its own paragraph; typed directly under an automatic one,
only a [Keep] line, and anything under a one-line [Source check] record, is kept.
"""

PIN = '[keep]'


def is_pinned(note):
    """A cell whose note says [Keep] (any case) is never changed automatically."""
    return PIN in (note or '').lower()


def merge_note(existing, prefix, paragraph, own_lines=None):
    """existing, with every paragraph that starts with prefix replaced by paragraph (or dropped when
    paragraph is empty). Other paragraphs keep their text and order. From a replaced paragraph, a
    [Keep] line is kept, and so is every line past own_lines, the number of lines its writer puts
    there (all of them when None), because a person typed it."""
    kept = []
    for part in (existing or '').split('\n\n'):
        if not part.strip():
            continue
        if not part.lstrip().startswith(prefix):
            kept.append(part)
            continue
        lines = part.split('\n')
        own, extra = (lines[:own_lines], lines[own_lines:]) if own_lines else (lines, [])
        carried = [line for line in own if PIN in line.lower()] + [line for line in extra if line.strip()]
        if carried:
            kept.append('\n'.join(carried))
    if paragraph:
        kept.append(paragraph)
    return '\n\n'.join(kept)
