"""Read the approved editorial files for the staff reference page."""

import hashlib
import html
import json
import re
from pathlib import Path

import markdown
from django.conf import settings
from django.urls import reverse


EDITORIAL_DIR = Path(settings.BASE_DIR) / "docs" / "editorial"
DOCUMENTS = {
    "manual": ("Manual editorial", "manual-editorial.md"),
    "checklist": ("Checklist de publicação", "checklist-de-publicacao.md"),
    "ficha": ("Ficha de mercado", "ficha-de-mercado.md"),
}
DOCUMENT_BY_FILENAME = {filename: key for key, (_, filename) in DOCUMENTS.items()}
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _render_document(text):
    """Render trusted, versioned Markdown while escaping raw HTML."""

    def replace_link(match):
        label, target = match.groups()
        key = DOCUMENT_BY_FILENAME.get(target)
        if key:
            return f"[{label}]({reverse('admin-ops-editorial')}?view={key})"
        if target.startswith("http://") or target.startswith("https://"):
            return match.group(0)
        # Specs are useful to maintainers, but have no staff-facing route.
        return label

    safe_markdown = html.escape(LINK_PATTERN.sub(replace_link, text))
    return markdown.markdown(safe_markdown, extensions=["tables", "toc"])


def load_editorial_reference(view="manual"):
    """Return one approved document and its machine-readable criteria."""

    view = view if view in DOCUMENTS else "manual"
    title, filename = DOCUMENTS[view]
    document = (EDITORIAL_DIR / filename).read_text(encoding="utf-8")
    raw_criteria = (EDITORIAL_DIR / "criteria-v1.2.json").read_bytes()
    rules = json.loads(raw_criteria)
    if rules["version"] != "1.2" or rules["status"] != "approved":
        raise ValueError("Versão editorial inválida")
    return {
        "active_view": view,
        "document_title": title,
        "document_html": _render_document(document),
        "criteria": rules["criteria"],
        "editorial_version": rules["version"],
        "approved_on": rules["approved_on"],
        "criteria_sha256": hashlib.sha256(raw_criteria).hexdigest(),
    }
