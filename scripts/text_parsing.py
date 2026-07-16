"""Shared parsing for catalog text fields.

Ported from src/utils/parsing.js so that catalog.json ships real link labels
instead of the "Link" placeholder the browser repairs at render time, and so the
public API can express license and organization cells as structured values.
Anything published to the API must be usable without reimplementing these rules.

label_from_url must stay equivalent to its JavaScript twin, which survives in
src/utils/parsing.js for the markdown renderer: the site's link labels now come
from this module, so a divergence would change what readers see.
scripts/check_parity.py diffs the two over every URL in the catalog.
"""

import re
from urllib.parse import urlparse, unquote

URL_RE = re.compile(r'https?://[^\s)]+', re.I)

# Friendly display names for well-known hosts so a bare link reads as a real
# destination instead of an anonymous "Access Dataset 2".
KNOWN_HOSTS = [
    (re.compile(r'(^|\.)huggingface\.co$', re.I), 'Hugging Face'),
    (re.compile(r'(^|\.)github\.com$', re.I), 'GitHub'),
    (re.compile(r'(^|\.)gitlab\.com$', re.I), 'GitLab'),
    (re.compile(r'(^|\.)kaggle\.com$', re.I), 'Kaggle'),
    (re.compile(r'(^|\.)zenodo\.org$', re.I), 'Zenodo'),
    (re.compile(r'(^|\.)figshare\.com$', re.I), 'figshare'),
    (re.compile(r'(^|\.)data\.world$', re.I), 'data.world'),
    (re.compile(r'(^|\.)drive\.google\.com$', re.I), 'Google Drive'),
    (re.compile(r'(^|\.)docs\.google\.com$', re.I), 'Google Docs'),
    (re.compile(r'(^|\.)doi\.org$', re.I), 'DOI'),
]

# Path segments that don't identify a resource; skipped when picking the tail.
NOISE_SEGMENT = re.compile(
    r'^(tree|blob|main|master|resolve|datasets?|models?|record|records|en|view|file|files|download|raw|-)$',
    re.I,
)

_TAIL_EXT = re.compile(r'\.(git|zip|csv|json|pdf|html?)$', re.I)
_TAIL_BRACKETS = re.compile(r'[\[\]()]')


def first_url(text):
    """Return the first http(s) URL in text, or None."""
    if not text or not isinstance(text, str):
        return None
    match = URL_RE.search(text)
    return match.group(0) if match else None


def clean_label(label=''):
    """Drop parenthesised asides and collapse whitespace."""
    if not isinstance(label, str):
        return ''
    result = re.sub(r'\([^)]*\)', ' ', label)
    result = re.sub(r'\s{2,}', ' ', result)
    return result.strip()


_BAD_ESCAPE_RE = re.compile(r'%(?![0-9a-fA-F]{2})')
# new URL() rejects a host containing any of these; urlparse happily accepts them.
_BAD_HOST_RE = re.compile(r'[\s%<>\\^`{|}]')


def _safe_decode(segment):
    """Percent-decode a path segment, leaving malformed escapes intact.

    Mirrors labelFromUrl's safeDecode, which catches decodeURIComponent's throw and
    returns the raw segment.
    """
    if _BAD_ESCAPE_RE.search(segment):
        return segment
    return unquote(segment)


def _strict_decode(segment):
    """Percent-decode, raising on a malformed escape like decodeURIComponent does.

    licenseLabel calls decodeURIComponent bare, so a malformed escape throws there
    and unwinds to the hostname fallback. Swallowing it instead made Python publish
    a different license name than the site rendered for the same cell.
    """
    if _BAD_ESCAPE_RE.search(segment):
        raise ValueError('malformed percent-escape')
    return unquote(segment)


def _js_url(raw):
    """Parse a URL, returning None for anything new URL() would reject.

    urlparse is far more permissive than the WHATWG parser the frontend uses: it
    accepts spaces and stray '%' in the host and out-of-range ports, where new URL()
    throws. label_from_url has to agree with its JavaScript twin, so the stricter
    parser's rejections are reproduced here.
    """
    try:
        parsed = urlparse(raw.strip())
    except ValueError:
        return None
    if parsed.scheme.lower() not in ('http', 'https'):
        return None
    try:
        parsed.port  # raises when the port is non-numeric or out of range
    except ValueError:
        return None
    if parsed.netloc == '' and parsed.path.startswith('/'):
        # new URL('https:///path') slides the first path segment into the host.
        rest = parsed.path.lstrip('/')
        if not rest:
            return None
        host, _, tail = rest.partition('/')
        parsed = parsed._replace(netloc=host, path='/' + tail)
    try:
        hostname = parsed.hostname
    except ValueError:
        return None
    if not hostname or _BAD_HOST_RE.search(hostname):
        return None
    return parsed


def label_from_url(raw_url=''):
    """Derive a human-readable label for a raw link URL.

    https://huggingface.co/somyalab/Spark_somya_TTS  -> "Hugging Face: Spark_somya_TTS"
    https://huggingface.co/roymukund/X/tree/main     -> "Hugging Face: X"
    https://spiredatasets.ee.iisc.ac.in/syspincorpus -> "spiredatasets.ee.iisc.ac.in"

    Returns None for non-http/unparseable URLs so callers can fall back.
    """
    if not raw_url or not isinstance(raw_url, str):
        return None
    parsed = _js_url(raw_url)
    if parsed is None:
        return None
    host = re.sub(r'^www\.', '', parsed.hostname)
    host_label = host
    for pattern, name in KNOWN_HOSTS:
        if pattern.search(host):
            host_label = name
            break

    segments = [s for s in parsed.path.split('/') if s]
    # Walk back from the end to the first segment that names something.
    tail = ''
    for segment in reversed(segments):
        decoded = _safe_decode(segment)
        if not NOISE_SEGMENT.match(decoded):
            tail = decoded
            break

    if tail:
        tail = _TAIL_EXT.sub('', tail)
        tail = _TAIL_BRACKETS.sub('', tail)  # chars that would break a markdown label
        tail = tail.strip()
        if len(tail) > 34:
            tail = tail[:33].rstrip() + '…'

    # The tail is the distinguishing resource name (repo / corpus id) and hosts often
    # repeat across a project's links, so keep it whenever there is one.
    return f'{host_label}: {tail}' if tail else host_label


def label_from_resource_url(url):
    """Label a paper / article / publication link.

    Differs from label_from_url deliberately: additional resources are mostly
    articles, whose slug title-cases into a readable headline ("Africa Biomass
    Challenge (zindi.africa)"), whereas dataset links are repositories whose exact
    identifier must survive verbatim. Returns None when nothing useful can be
    derived, leaving the caller's placeholder in place.
    """
    if not url or not isinstance(url, str):
        return None
    try:
        parsed = urlparse(url)
    except ValueError:
        return None

    def tail_words(path):
        segments = path.strip('/').split('/')
        slug = segments[-1] if segments and segments[-1] else ''
        return slug.replace('-', ' ').replace('_', ' ')

    if parsed.scheme in ('http', 'https'):
        domain = parsed.netloc.replace('www.', '')
        slug = tail_words(parsed.path)
        if slug and len(slug) > 3:
            return f'{slug.title()} ({domain})'
        return domain or None
    if url.startswith('/'):
        slug = tail_words(url)
        return slug.title() if slug else None
    return None


# SPDX identifiers we recognise, so a harvester can act on the license instead of
# string-matching our prose. Anything not listed reports spdx: null rather than a
# guess -- claiming the wrong license for a partner's asset is worse than silence.
SPDX_IDS = frozenset({
    'CC-BY-4.0', 'CC0-1.0', 'CC-BY-SA-4.0', 'Apache-2.0', 'MIT', 'AGPL-3.0', 'ODbL-1.0',
})


def spdx_for(name):
    """Map a display name to an SPDX id, or None when we do not recognise it.

    Separators are normalised because the same license reaches here spelled two
    ways: LICENSE_NORMALIZATION emits "CC-BY 4.0" from the sheet's usual wording,
    while license_label's bare-version shorthand emits "CC-BY-4.0". Matching only
    one of them silently dropped the id for the other.
    """
    if not name or not isinstance(name, str):
        return None
    key = re.sub(r'\s+', '-', name.strip())
    return key if key in SPDX_IDS else None


def license_parts(raw):
    """Split a license cell into {name, spdx, url}, or None when unrecorded.

    None means no license was recorded for the asset -- not that the asset is
    unlicensed, and not that it is freely reusable.
    """
    if not raw or not isinstance(raw, str) or not raw.strip():
        return None
    name = license_label(raw)
    url = first_url(raw)
    if not name and not url:
        return None
    return {
        'name': name or None,
        'spdx': spdx_for(name),
        'url': url,
    }


def license_label(license_text=''):
    """Reduce a license cell to a display name.

    A bare version number is the shorthand the source sheet uses for Creative
    Commons attribution, and a value that is only a URL falls back to the last
    path segment, then the host.
    """
    if not license_text or not isinstance(license_text, str):
        return ''
    trimmed = license_text.strip()
    if re.fullmatch(r'\d+(\.\d+)?', trimmed):
        return f'CC-BY-{trimmed}'

    url = first_url(license_text)
    if not url:
        return trimmed

    label = license_text.replace(url, '').strip()
    if label:
        return label

    # Mirrors licenseLabel's two try blocks. Both construct new URL(), so a URL that
    # parser rejects throws twice over there and yields the literal 'License'.
    parsed = _js_url(url)
    if parsed is None:
        return 'License'
    try:
        segments = [s for s in parsed.path.split('/') if s]
        if segments:
            last = _strict_decode(segments[-1])
            if last:
                return last
    except ValueError:
        # A malformed escape throws in the first block; the second re-parses and
        # returns the host.
        pass
    return re.sub(r'^www\.', '', parsed.hostname)


# Organization cells encode three roles as prose, e.g.
#   "Powered by / Provided by: X\nCatalyzed by: Y\nFinanced by: Z"
_ORG_ROLE_PATTERNS = {
    'provided_by': r'Powered by\s*(?:/\s*Provided by)?',
    'catalyzed_by': r'Catalyzed by',
    'financed_by': r'Financed by',
}

_NEXT_ROLE_RES = [
    re.compile(r'Catalyzed by:', re.I),
    re.compile(r'Financed by:', re.I),
    re.compile(r'Powered by\s*(?:/\s*Provided by)?:', re.I),
]

_LOGO_PAREN_RE = re.compile(r'\(logo\s+https?://[^\s)]+\)', re.I)
_IMAGE_PAREN_RE = re.compile(
    r'\(\s*https?://[^\s)]+\.(?:jpg|jpeg|png|gif|svg)\s*\)', re.I
)
_NAME_PAREN_URL_RE = re.compile(r'([^(\n]*?)\s*\(\s*(https?://[^\s)]+)\s*\)')
_NAME_BARE_URL_RE = re.compile(
    r'([^,&;\n\[\]()]+?)\s+(https?://[^\s,&;)]+)(?=[,&;\n]|$)'
)


def linkify_org_text(text):
    """Convert org text with inline URLs into markdown links.

    "Org Name (https://url.com/)" -> "[Org Name](https://url.com/)"
    "(logo https://...)"          -> stripped
    "OrgA, OrgB (url)"            -> "OrgA, [OrgB](url)" (links only the closest org)
    """
    if not text:
        return text
    result = _LOGO_PAREN_RE.sub('', text)
    result = _IMAGE_PAREN_RE.sub('', result)

    def _paren_repl(match):
        name, url = match.group(1), match.group(2)
        trimmed = name.lstrip()
        # Link only the organization closest to the URL, after the last separator.
        split_after = -1
        for sep, offset in ((',', 1), ('&', 1), (';', 1), (' and ', 5)):
            idx = trimmed.rfind(sep)
            if idx >= 0:
                split_after = max(split_after, idx + offset)
        if split_after >= 0:
            prefix = trimmed[:split_after]
            org_name = trimmed[split_after:].strip()
            return f'{prefix} [{org_name}]({url})'
        final = trimmed.strip()
        connector = re.match(r'^(and\s+)(.+)', final, re.I)
        if connector:
            return f'{connector.group(1)}[{connector.group(2).strip()}]({url})'
        return f'[{final}]({url})'

    result = _NAME_PAREN_URL_RE.sub(_paren_repl, result)
    result = _NAME_BARE_URL_RE.sub(
        lambda m: f'[{m.group(1).strip()}]({m.group(2)})', result
    )
    return result.strip()


_MD_LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')


def org_section_parts(section):
    """Split one organization role into plain text and the links it embeds.

    linkify_org_text already knows how to tell an organization's name from a URL
    glued to it, so it is reused as an intermediate representation and then
    unwrapped: markdown is a rendering artifact, and a consumer of the API should
    receive the name and the URL as separate values rather than have to strip
    syntax back out. Returns None when the role carries nothing.
    """
    if not section or not section.strip():
        return None
    markdown = linkify_org_text(section) or ''
    links = [{'name': m.group(1).strip(), 'url': m.group(2).strip()}
             for m in _MD_LINK_RE.finditer(markdown)]
    text = _MD_LINK_RE.sub(r'\1', markdown)
    text = re.sub(r'\s{2,}', ' ', text).strip().strip(',').strip()
    if not text and not links:
        return None
    return {'text': text or None, 'links': links}


def parse_organizations(org_text=''):
    """Split an organization cell into provided_by / catalyzed_by / financed_by.

    Returns each role's text verbatim, or {'raw': ...} when the cell carries no
    role labels at all, or None for empty input. Sections are deliberately left
    unlinkified: linkify_org_text is not idempotent (it would re-wrap an existing
    markdown link into [[Name]](url)), so callers apply it at most once.
    """
    if not org_text or not isinstance(org_text, str):
        return None

    def extract_section(label_pattern):
        match = re.search(label_pattern + r':\s*', org_text, re.I)
        if not match:
            return None
        start = org_text.index(':', match.start()) + 1
        remaining = org_text[start:]
        ends = [m.start() for m in
                (pattern.search(remaining) for pattern in _NEXT_ROLE_RES) if m]
        end = min(ends) if ends else len(remaining)
        section = remaining[:end].strip()
        return section or None

    roles = {key: extract_section(pattern)
             for key, pattern in _ORG_ROLE_PATTERNS.items()}

    if not any(roles.values()):
        return {'raw': org_text.strip()}
    return roles
