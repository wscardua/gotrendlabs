from io import BytesIO
from pathlib import Path
from textwrap import wrap
from urllib.parse import urlparse, urlencode

from django.conf import settings
from django.utils.crypto import salted_hmac
from django.urls import reverse

from PIL import Image, ImageDraw, ImageFont


CARD_SIZE = (1200, 630)
CARD_BG = (250, 252, 246)
CARD_PANEL = (255, 253, 247)
INK = (15, 20, 24)
MUTED = (84, 95, 95)
GREEN = (19, 111, 74)
LINE = (205, 225, 211)
ORYNTH_CONTEXT = "Rede social de previsões educativas com consenso público, reputação e resolução auditável."
MARKET_CTA = "Registre previsões, compare com a comunidade e construa reputação."


def currency_label(value):
    label = str(value or "0 O₵").replace(" OC", " O₵")
    return label if "O₵" in label else f"{label} O₵"


def absolute_url(request, view_name, *args, query=None):
    path = reverse(view_name, args=args)
    public_base_url = getattr(settings, "PUBLIC_SHARE_BASE_URL", "")
    url = f"{public_base_url}{path}" if public_base_url else request.build_absolute_uri(path)
    if query:
        url = f"{url}?{urlencode(query)}"
    return url


def build_share_context(request, *, kind, title, description, text, image_view_name, image_args, query=None):
    canonical_url = absolute_url(request, f"share-{kind}", *image_args, query=query)
    image_url = absolute_url(request, image_view_name, *image_args, query=query)
    share_text = f"{text} {canonical_url}".strip()
    return {
        "kind": kind,
        "title": title,
        "description": description,
        "text": text,
        "copy_text": share_text,
        "url": canonical_url,
        "display_url": _display_url(canonical_url),
        "image_url": image_url,
        "is_publicly_crawlable": _is_publicly_crawlable(canonical_url),
        "links": _platform_links(canonical_url, text),
    }


def market_share_context(request, market):
    title = str(market.get("title", "Mercado Orynth Trends"))
    volume_label = currency_label(market.get("volume_oc", 0))
    description = (
        f"Consenso atual: {market.get('primary_probability', 0)}% {market.get('primary_outcome', '')} · "
        f"{volume_label} reservados pela comunidade. {MARKET_CTA} {ORYNTH_CONTEXT}"
    )
    text = f"No Orynth Trends: {title}. {MARKET_CTA}"
    return build_share_context(
        request,
        kind="market",
        title=title,
        description=description,
        text=text,
        image_view_name="share-market-image",
        image_args=[market.get("slug")],
    )


def result_share_context(request, market, viewer):
    if viewer.get("is_authenticated"):
        title = f"{viewer.get('name', 'Usuario')} compartilhou um resultado no Orynth Trends."
        description = (
            f"Resultado: {market.get('primary_outcome', '')}. Mercado: {market.get('title', 'mercado')}. "
            f"Reputacao atual {viewer.get('reputation', 0)}. {ORYNTH_CONTEXT}"
        )
        text = f"{viewer.get('name', 'Usuario')} compartilhou um resultado no Orynth Trends: {market.get('title', '')}"
    else:
        title = f"Resultado: {market.get('primary_outcome', '')} · Orynth Trends"
        description = f"Mercado: {market.get('title', 'mercado')}. {ORYNTH_CONTEXT}"
        text = f"Resultado no Orynth Trends: {market.get('title', '')}"
    return build_share_context(
        request,
        kind="result",
        title=title,
        description=description,
        text=text,
        image_view_name="share-result-image",
        image_args=[market.get("slug")],
    )


def public_badge_share_token(user_id, badge_code):
    return salted_hmac("orynth.badge.share", f"{user_id}:{badge_code}").hexdigest()[:32]


def badge_share_context(request, badge, viewer):
    title = f"{viewer.get('name', 'Usuario')} conquistou {badge.get('name', 'uma badge')}."
    description = f"{badge.get('description') or 'Conquista registrada no Orynth Trends.'} {ORYNTH_CONTEXT}"
    text = f"{viewer.get('name', 'Usuario')} conquistou a badge {badge.get('name', 'Orynth Trends')} no Orynth Trends."
    query = {"t": viewer["share_token"]} if viewer.get("share_token") else None
    return build_share_context(
        request,
        kind="badge",
        title=title,
        description=description,
        text=text,
        image_view_name="share-badge-image",
        image_args=[badge.get("code")],
        query=query,
    )


def render_market_card(market, share):
    option_summary = _market_option_summary(market)
    return _render_card(
        eyebrow=f"Orynth Trends · {market.get('category', 'Mercado')} · {market.get('event') or market.get('subcategory', 'Evento')}",
        title=str(market.get("title", "Mercado Orynth Trends")),
        lead=f"{market.get('primary_probability', 0)}% {market.get('primary_outcome', '')} · {currency_label(market.get('volume_oc', 0))} reservados",
        body=option_summary or f"{MARKET_CTA} Fonte: {market.get('source', 'verificavel')}",
        url=share["display_url"],
        image_url=market.get("image_url"),
        fallback_mark=market.get("thumb") or "OR",
    )


def render_result_card(market, viewer, share):
    if viewer.get("is_authenticated"):
        title = str(market.get("title", "Mercado Orynth Trends"))
        body = f"Reputacao atual {viewer.get('reputation', 0)} · {ORYNTH_CONTEXT}"
    else:
        title = str(market.get("title", "Mercado Orynth Trends"))
        body = ORYNTH_CONTEXT
    return _render_card(
        eyebrow=f"Orynth Trends · Resultado: {market.get('primary_outcome', '')}",
        title=title,
        lead=f"Resultado: {market.get('primary_outcome', '')}",
        body=body,
        url=share["display_url"],
        image_url=market.get("image_url"),
        fallback_mark=market.get("thumb") or "OR",
    )


def render_badge_card(badge, viewer, share):
    return _render_card(
        eyebrow="Orynth Trends · Badge conquistada",
        title=f"{viewer.get('name', 'Usuario')} conquistou {badge.get('name', 'uma badge')}.",
        lead=str(badge.get("description") or "Conquista registrada no Orynth Trends."),
        body=f"{badge.get('rule_description') or 'Conquista validada pela plataforma.'} {ORYNTH_CONTEXT}",
        url=share["display_url"],
        image_url=badge.get("image_url"),
    )


def png_response_bytes(image):
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def _platform_links(url, text):
    copy_text = f"{text} {url}".strip()
    return {
        "whatsapp": f"https://wa.me/?{urlencode({'text': copy_text})}",
        "telegram": f"https://t.me/share/url?{urlencode({'url': url, 'text': text})}",
        "x": f"https://x.com/intent/tweet?{urlencode({'text': text, 'url': url})}",
        "facebook": f"https://www.facebook.com/sharer/sharer.php?{urlencode({'u': url})}",
        "linkedin": f"https://www.linkedin.com/sharing/share-offsite/?{urlencode({'url': url})}",
    }


def _display_url(url):
    return url.replace("https://", "").replace("http://", "").rstrip("/")


def _market_option_summary(market):
    options = market.get("options") or []
    labels = []
    for option in options[:4]:
        label = "NÃO" if option.get("label") == "NAO" else str(option.get("label") or "")
        probability = option.get("probability", 0)
        if label:
            labels.append(f"{label} {probability}%")
    return "Opções: " + " · ".join(labels) if labels else ""


def _is_publicly_crawlable(url):
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if parsed.scheme != "https":
        return False
    return host not in {"localhost", "127.0.0.1", "0.0.0.0", "testserver"} and not host.startswith("192.168.") and not host.startswith("10.")


def _font(size, *, bold=False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Black.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def _render_card(*, eyebrow, title, lead, body, url, image_url=None, fallback_mark="O"):
    image = Image.new("RGB", CARD_SIZE, CARD_BG)
    draw = ImageDraw.Draw(image)
    _soft_background(draw)

    draw.rounded_rectangle((36, 36, 1164, 594), radius=34, fill=CARD_PANEL, outline=LINE, width=2)
    draw.text((74, 74), "Orynth Trends", fill=GREEN, font=_font(34, bold=True))
    draw.text((74, 546), url, fill=GREEN, font=_font(24, bold=True))
    draw.text((930, 78), eyebrow, fill=MUTED, font=_font(24), anchor="ra")

    art = _load_art(image_url)
    if art:
        art = art.convert("RGBA")
        art.thumbnail((215, 215), Image.LANCZOS)
        draw.rounded_rectangle((82, 150, 300, 368), radius=28, fill=(249, 249, 242), outline=LINE, width=2)
        x = 82 + ((218 - art.width) // 2)
        y = 150 + ((218 - art.height) // 2)
        image.paste(art, (x, y), art)
    else:
        draw.rounded_rectangle((82, 150, 300, 368), radius=28, fill=(235, 248, 239), outline=LINE, width=2)
        draw.text((191, 259), str(fallback_mark or "O")[:4].upper(), fill=GREEN, font=_font(82, bold=True), anchor="mm")

    text_x = 340
    _draw_wrapped(draw, title, (text_x, 142), _font(70, bold=True), INK, max_width=790, line_gap=4, max_lines=3)
    title_height = _wrapped_height(draw, title, _font(70, bold=True), 790, 4, 3)
    lead_y = min(390, 152 + title_height + 24)
    _draw_wrapped(draw, lead, (text_x, lead_y), _font(34), MUTED, max_width=815, line_gap=10, max_lines=2)
    body_y = min(500, lead_y + _wrapped_height(draw, lead, _font(34), 815, 10, 2) + 24)
    _draw_wrapped(draw, body, (text_x, body_y), _font(30), INK, max_width=815, line_gap=8, max_lines=2)
    return image


def _soft_background(draw):
    for index in range(0, 1200, 16):
        color = (
            min(255, CARD_BG[0] - 4 + index // 180),
            min(255, CARD_BG[1]),
            min(255, CARD_BG[2] + index // 240),
        )
        draw.line((index, 0, index + 430, 630), fill=color, width=18)


def _load_art(image_url):
    if not image_url:
        return None
    if image_url.startswith(settings.MEDIA_URL):
        relative = image_url[len(settings.MEDIA_URL) :].lstrip("/")
        path = Path(settings.MEDIA_ROOT) / relative
    elif image_url.startswith("/media/"):
        path = Path(settings.MEDIA_ROOT) / image_url.removeprefix("/media/")
    else:
        return None
    if not path.exists():
        return None
    try:
        return Image.open(path)
    except Exception:
        return None


def _draw_wrapped(draw, text, xy, font, fill, *, max_width, line_gap=0, max_lines=3):
    x, y = xy
    for line in _wrap_lines(draw, text, font, max_width, max_lines):
        draw.text((x, y), line, fill=fill, font=font)
        y += _line_height(draw, font) + line_gap


def _wrapped_height(draw, text, font, max_width, line_gap, max_lines):
    lines = _wrap_lines(draw, text, font, max_width, max_lines)
    if not lines:
        return 0
    return (len(lines) * _line_height(draw, font)) + ((len(lines) - 1) * line_gap)


def _wrap_lines(draw, text, font, max_width, max_lines):
    words = []
    for chunk in str(text).split():
        words.extend(wrap(chunk, 22) or [chunk])
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if _text_width(draw, candidate, font) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) == max_lines and len(" ".join(words)) > len(" ".join(lines)):
        lines[-1] = lines[-1].rstrip(". ") + "..."
    return lines


def _text_width(draw, text, font):
    return draw.textbbox((0, 0), text, font=font)[2]


def _line_height(draw, font):
    bbox = draw.textbbox((0, 0), "Ag", font=font)
    return bbox[3] - bbox[1]
