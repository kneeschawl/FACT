import re
import json
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import spacy
from spacy.matcher import Matcher

# ─── Setup ────────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

try:
    nlp = spacy.load("en_core_web_md")
    log.info("Loaded spaCy model: en_core_web_md")
except OSError:
    try:
        nlp = spacy.load("en_core_web_sm")
        log.info("Loaded spaCy model: en_core_web_sm")
    except OSError:
        log.error("No spaCy model found. Run: python -m spacy download en_core_web_sm")
        raise


# ─── spaCy Matchers ───────────────────────────────────────────────────────────

matcher = Matcher(nlp.vocab)

# Price token patterns
PRICE_PATTERNS = [
    [{"TEXT": {"REGEX": r"^[\$£€₹¥₩]"}, "OP": "?"}, {"TEXT": {"REGEX": r"^\d{1,6}([,\.]\d+)*$"}}],
    [{"TEXT": {"REGEX": r"^\d{1,6}([,\.]\d+)*$"}}, {"TEXT": {"REGEX": r"^(USD|GBP|EUR|INR|NPR|AUD|CAD)$"}}],
    [{"LOWER": {"IN": ["usd", "gbp", "eur", "inr", "npr", "rs", "rs."]}}, {"TEXT": {"REGEX": r"^\d{1,6}([,\.]\d+)*$"}}],
]
matcher.add("PRICE", PRICE_PATTERNS)

# Discount token patterns — case-insensitive via LOWER
DISCOUNT_PATTERNS = [
    # Captures "-80%" specifically
    [
        {"TEXT": {"REGEX": r"^-\d{1,3}$"}}, # Must start with '-' followed by 1-3 digits
        {"TEXT": "%"},
        {"LOWER": {"IN": ["off", "discount"]}, "OP": "?"} # Optional context
    ],
    # Captures "-80% OFF" as a single token if the site joins them
    [
        {"TEXT": {"REGEX": r"^-\d{1,3}%$"}}, 
        {"LOWER": {"IN": ["off", "discount"]}, "OP": "?"}
    ]
]
matcher.add("DISCOUNT", DISCOUNT_PATTERNS)

# Urgency token patterns
URGENCY_PATTERNS = [
    [{"LOWER": {"IN": ["hurry", "hurry!"]}}, {"LOWER": {"IN": ["up", "!", "now"]}, "OP": "?"}],
    [{"LOWER": "limited"}, {"LOWER": {"IN": ["time", "stock", "offer", "edition", "availability"]}}],
    [{"LOWER": "only"}, {"TEXT": {"REGEX": r"^\d+$"}}, {"LOWER": {"IN": ["left", "remaining", "available"]}}],
    [{"LOWER": "last"}, {"TEXT": {"REGEX": r"^\d+$"}}, {"LOWER": {"IN": ["left", "remaining", "items", "pieces"]}}],
    [{"LOWER": "ends"}, {"LOWER": {"IN": ["today", "soon", "tonight", "tomorrow"]}}],
    [{"LOWER": "don't"}, {"LOWER": "miss"}],
    [{"LOWER": "selling"}, {"LOWER": "fast"}],
    [{"LOWER": "almost"}, {"LOWER": "gone"}],
    [{"LOWER": "act"}, {"LOWER": "now"}],
    [{"LOWER": "order"}, {"LOWER": "now"}],
    [{"LOWER": "buy"}, {"LOWER": "now"}],
    [{"LOWER": "flash"}, {"LOWER": "sale"}],
    [{"LOWER": {"IN": ["deal", "deals"]}}, {"LOWER": "of"}, {"LOWER": "the"}, {"LOWER": "day"}],
    [{"LOWER": "today"}, {"LOWER": "only"}],
    [{"LOWER": "expires"}, {"LOWER": {"IN": ["soon", "today", "tonight"]}, "OP": "?"}],
    [{"LOWER": "get"}, {"LOWER": "it"}, {"LOWER": "now"}],
    [{"LOWER": "while"}, {"LOWER": "stocks"}, {"LOWER": "last"}],
    [{"LOWER": "out"}, {"LOWER": "of"}, {"LOWER": "stock", "OP": "?"}],
]
matcher.add("URGENCY", URGENCY_PATTERNS)


# ─── Regex Extractors ─────────────────────────────────────────────────────────

PRICE_REGEX = re.compile(
    r"""
    (?:
        [\$£€₹¥₩]\s?\d{1,6}(?:[,\.]\d{2,3})*(?:\.\d{2})?   |
        \d{1,6}(?:[,\.]\d{2,3})*(?:\.\d{2})?\s?(?:USD|GBP|EUR|INR|NPR|AUD|CAD|Rs\.?)  |
        (?:Rs\.?|INR|NPR)\s?\d{1,6}(?:[,\.]\d{2,3})*
    )
    """,
    re.VERBOSE | re.IGNORECASE
)

# Much broader discount regex — catches all common formats
DISCOUNT_REGEX = re.compile(
    r"""
    (?:
        # "-20% off" / "-20 % OFF" (Mandatory minus for actual discount badges)
        -\d{1,3}\s?%\s*(?:off|discount|sale|savings?)?  |

        # "off 20%" / "off $10" (Keep as is, usually specific to price area)
        off\s+(?:\d{1,3}\s?%|[\$£€₹]\s?\d+(?:\.\d+)?)  |

        # "save $10" / "save 30%"
        (?:save|saving|savings)\s+(?:[\$£€₹¥]?\s?\d+(?:[,.]\d+)?|\d{1,3}\s?%)  |

        # "was $50 now $30" (The gold standard for your Fiscal Table)
        was\s+[\$£€₹¥]?\s?\d+(?:[,.]\d+)?\s*(?:,\s*)?now\s+[\$£€₹¥]?\s?\d+(?:[,.]\d+)?  |

        # standalone "-X% OFF" (Common on Daraz/Amazon badges)
        -\d{1,3}%\s*OFF
    )
    """,
    re.VERBOSE | re.IGNORECASE
)

URGENCY_REGEX = re.compile(
    r"""
    (?:
        hurry\s*up? | limited\s+(?:time|stock|offer|edition) |
        only\s+\d+\s+(?:left|remaining|available) |
        last\s+\d+\s+(?:left|remaining|items?|pieces?) |
        ends?\s+(?:today|soon|tonight|tomorrow) |
        don.?t\s+miss | selling\s+fast | almost\s+gone |
        act\s+now | order\s+now | buy\s+now | flash\s+sale |
        deal\s+of\s+the\s+day | today\s+only | expires?\s+soon |
        get\s+it\s+now | while\s+stocks?\s+last |
        out\s+of\s+stock | back\s+in\s+stock |
        selling\s+out | last\s+chance | one\s+day\s+(?:only|deal|sale) |
        \d+\s*(?:items?|units?|pieces?)\s*(?:left|remaining) |
        \d+\s*(?:hours?|hrs?|mins?|minutes?)\s*(?:left|remaining|only) |
        grab\s+(?:it|yours?)\s+(?:now|fast|quick) | don.?t\s+wait |
        offer\s+ends | sale\s+ends | exclusive\s+(?:deal|offer) |
        countdown | stock\s+running\s+(?:low|out)
    )
    """,
    re.VERBOSE | re.IGNORECASE
)


# ─── Core Extraction Helpers ──────────────────────────────────────────────────

def run_spacy_matchers(text: str):
    """Run spaCy NER + token matchers on text."""
    doc = nlp(text[:5000])

    ner_brands, ner_prices, ner_other = [], [], []
    seen = set()

    for ent in doc.ents:
        val = ent.text.strip()
        k = val.lower()
        if k in seen or len(val) < 2:
            continue
        seen.add(k)
        if ent.label_ in ("ORG", "PRODUCT", "GPE", "BRAND"):
            ner_brands.append({"text": val, "label": ent.label_})
        elif ent.label_ in ("MONEY", "QUANTITY"):
            ner_prices.append({"text": val, "label": ent.label_})
        elif ent.label_ not in ("DATE", "TIME", "CARDINAL", "ORDINAL"):
            ner_other.append({"text": val, "label": ent.label_})

    matcher_hits = {"PRICE": [], "DISCOUNT": [], "URGENCY": []}
    seen_spans = set()
    for match_id, start, end in matcher(doc):
        label = nlp.vocab.strings[match_id]
        span = doc[start:end].text.strip()
        if span.lower() not in seen_spans and len(span) > 1:
            seen_spans.add(span.lower())
            matcher_hits[label].append(span)

    return ner_brands, ner_prices, ner_other, matcher_hits


def regex_prices(hints: list, full_text: str) -> set:
    results = set()
    for t in hints:
        for m in PRICE_REGEX.finditer(t):
            results.add(m.group().strip())
    for m in PRICE_REGEX.finditer(full_text[:6000]):
        v = m.group().strip()
        if len(v) >= 2:
            results.add(v)
    return results


def regex_discounts(hints: list, full_text: str) -> set:
    """
    Pull discounts from:
      1. Dedicated discount hint elements (badges, banners)
      2. Price hint elements (often contain 'was/now', strikethrough prices)
      3. Full page text via broad regex
    """
    results = set()
    # Scan all hint buckets — discount info often lives in price elements
    all_hint_text = " | ".join(hints)
    for m in DISCOUNT_REGEX.finditer(all_hint_text):
        v = m.group().strip()
        if len(v) >= 2:
            results.add(v)

    # Full text scan
    for m in DISCOUNT_REGEX.finditer(full_text[:8000]):
        v = m.group().strip()
        if len(v) >= 2:
            results.add(v)

    # Also look for raw percentage strings in hint elements (e.g. badge says just "30%")
    pct_only = re.compile(r'\b(\d{1,3})\s*%')
    for t in hints:
        for m in pct_only.finditer(t):
            pct = int(m.group(1))
            if 1 <= pct <= 90:           # realistic discount range
                results.add(f"{pct}% off")

    return results


def regex_urgency(hints: list, full_text: str) -> set:
    results = set()
    combined = " ".join(hints) + " " + full_text[:6000]
    for m in URGENCY_REGEX.finditer(combined):
        v = m.group().strip()
        if len(v) >= 4:
            results.add(v.lower().capitalize())
    return results


def build_brands(brand_hints, image_alts, ner_brands, title) -> list:
    seen = set()
    results = []
    for t in (brand_hints + image_alts)[:8]:
        t = t.strip()
        if t and 1 < len(t) < 100 and t.lower() not in seen:
            seen.add(t.lower())
            results.append({"text": t, "source": "page_element"})
    for ent in ner_brands:
        if ent["text"].lower() not in seen:
            seen.add(ent["text"].lower())
            results.append({"text": ent["text"], "source": f"NER:{ent['label']}"})
    if title and title.lower() not in seen:
        results.append({"text": title[:80], "source": "page_title"})
    return results[:15]


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model": nlp.meta.get("name", "unknown")})


@app.route("/extract", methods=["POST"])
def extract():
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400

    full_text      = data.get("full_text", "")
    title          = data.get("title", "")
    price_hints    = data.get("price_hints", [])
    discount_hints = data.get("discount_hints", [])
    brand_hints    = data.get("brand_hints", [])
    urgency_hints  = data.get("urgency_hints", [])
    image_alts     = data.get("image_alts", [])
    url            = data.get("url", "")

    log.info(f"Processing: {url[:80]} | text_len={len(full_text)}")

    # Run spaCy
    ner_brands, ner_prices, ner_other, matcher_hits = run_spacy_matchers(full_text)

    # Prices — merge all sources
    all_prices = regex_prices(price_hints, full_text)
    all_prices.update(matcher_hits["PRICE"])
    all_prices.update(e["text"] for e in ner_prices)

    # Discounts — pass ALL hint types, not just discount_hints
    # Price elements frequently contain discount info ("was/now", strikethrough)
    all_discounts = regex_discounts(
        discount_hints + price_hints + urgency_hints,
        full_text
    )
    all_discounts.update(matcher_hits["DISCOUNT"])

    # Urgency
    all_urgency = regex_urgency(urgency_hints, full_text)
    all_urgency.update(matcher_hits["URGENCY"])

    # Brands
    brands = build_brands(brand_hints, image_alts, ner_brands, title)

    result = {
        "url": url,
        "brands":        brands,
        "prices":        sorted([{"text": p} for p in all_prices],    key=lambda x: x["text"]),
        "discounts":     sorted([{"text": d} for d in all_discounts], key=lambda x: x["text"]),
        "urgency_texts": sorted([{"text": u} for u in all_urgency],   key=lambda x: x["text"]),
        "other_entities": ner_other[:20],
        "meta": {
            "title":       title,
            "spacy_model": nlp.meta.get("name", "unknown"),
            "text_length": len(full_text)
        }
    }

    log.info(
        f"→ brands:{len(brands)} prices:{len(all_prices)} "
        f"discounts:{len(all_discounts)} urgency:{len(all_urgency)}"
    )
    return jsonify(result)


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*55)
    print("  🛒  E-Commerce NER Backend")
    print("  Running at http://localhost:5000")
    print("  Keep this terminal open while using the extension")
    print("="*55 + "\n")
    app.run(host="127.0.0.1", port=5000, debug=False)