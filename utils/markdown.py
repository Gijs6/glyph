import bleach
import markdown as _markdown
from markupsafe import Markup

ALLOWED_TAGS = [
    "p",
    "br",
    "hr",
    "strong",
    "b",
    "em",
    "i",
    "u",
    "s",
    "strike",
    "a",
    "ul",
    "ol",
    "li",
    "blockquote",
    "code",
    "pre",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "img",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
]
ALLOWED_ATTRIBUTES = {
    "a": ["href", "rel", "target"],
    "img": ["src", "alt", "title"],
}


def render_markdown(text):
    html = _markdown.markdown(text or "", extensions=["extra", "sane_lists"])
    cleaned = bleach.clean(
        html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True
    )
    return Markup(bleach.linkify(cleaned, parse_email=False))
