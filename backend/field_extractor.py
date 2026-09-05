import re
from datetime import datetime
from difflib import SequenceMatcher


# ============================================================
# OCR LABEL CORRECTIONS
# ============================================================

OCR_LABEL_CORRECTIONS = {
    "alrp": "mrp",
    "alrpr": "mrp",
    "mrp": "mrp",
    "mrprs": "mrp",
    "map": "mrp",              # common OCR error
    "morutectured": "manufactured",
    "wrratsctured": "manufactured",
    "manufactured": "manufactured",
    "mfd": "mfd",
    "mfg": "mfg",
    "sy": "by",
    "dy": "by",
}


# ============================================================
# CONFIDENCE
# ============================================================

def confidence_level(confidence):

    if confidence >= 0.80:
        return "HIGH"

    if confidence >= 0.50:
        return "MEDIUM"

    return "LOW"


# ============================================================
# TEXT HELPERS
# ============================================================

def normalize_text(text):

    text = str(text)

    replacements = {
        "₹": "Rs",
        "—": "-",
        "–": "-",
        "’": "'",
        "“": '"',
        "”": '"',
        "×": "x",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Normalize common label formats
    text = re.sub(
        r"\bM[\s.]*R[\s.]*P[\s.]*\b",
        "MRP",
        text,
        flags=re.I
    )

    text = re.sub(
        r"\bM[\s.]*F[\s.]*G[\s.]*\b",
        "MFG",
        text,
        flags=re.I
    )

    text = re.sub(
        r"\bM[\s.]*F[\s.]*D[\s.]*\b",
        "MFD",
        text,
        flags=re.I
    )

    return text


def clean_word(text):

    # For label matching we only care about letters and digits.
    # Keeping punctuation like ':' and '/' was causing labels such as
    # 'MFD:' and 'MRP:' to normalize to 'mfd:' and 'mrp:' instead of
    # the canonical label names used throughout the extractor.
    return "".join(
        ch.lower()
        for ch in str(text)
        if ch.isalnum()
    )


def normalized_label(text):

    value = clean_word(
        normalize_text(text)
    )

    return OCR_LABEL_CORRECTIONS.get(
        value,
        value
    )


def fuzzy_match(text, possibilities, threshold=0.70):

    text = str(text).lower().strip()

    best_match = None
    best_score = 0

    for possibility in possibilities:

        score = SequenceMatcher(
            None,
            text,
            possibility.lower()
        ).ratio()

        if score > best_score:
            best_score = score
            best_match = possibility

    if best_score >= threshold:
        return best_match, best_score

    return None, 0


def make_result(
    value=None,
    confidence=0.0,
    evidence=None,
    bbox=None,
    status="found"
):

    return {
        "value": value,
        "confidence": round(
            max(0.0, min(1.0, confidence)),
            2
        ),
        "status": status,
        "evidence": evidence,
        "bbox": bbox
    }


def word_text(words):

    return " ".join(
        str(w["text"])
        for w in words
    )


def safe_confidence(words):

    valid = [
        w["confidence"]
        for w in words
        if w.get("confidence", -1) >= 0
    ]

    if not valid:
        return 0.0

    return min(valid) / 100


# ============================================================
# MRP
# ============================================================

def extract_mrp(words):

    # Handles:
    #
    # MRP 120
    # M.R.P. Rs.120
    # MRP: ₹120
    # Rs 120
    # OCR mistakes such as MAP

    mrp_label_pattern = re.compile(
        r"\b(?:MRP|MAP|M[\s.]*R[\s.]*P)\b",
        re.I
    )

    price_pattern = re.compile(
        r"(?:Rs[\s.:]*)?"
        r"(?:₹[\s.]*)?"
        r"(\d+(?:\.\d{1,2})?)"
        r"\s*(?:/-)?",
        re.I
    )

    # --------------------------------------------------------
    # PASS 1: label + nearby price
    # --------------------------------------------------------

    for i, word in enumerate(words):

        text = normalize_text(word["text"])

        if not mrp_label_pattern.search(text):
            continue

        nearby = words[i:i + 7]

        local_text = word_text(nearby)

        match = price_pattern.search(
            local_text
        )

        if match:

            value = float(
                match.group(1)
            )

            confidence = safe_confidence(
                nearby
            )

            # Strong label context gets a small boost
            confidence = min(
                1.0,
                confidence + 0.05
            )

            return make_result(
                value=value,
                confidence=confidence,
                evidence=local_text,
                bbox=word["bbox"]
            )

    # --------------------------------------------------------
    # PASS 2: standalone Rs / ₹ price
    # --------------------------------------------------------

    for i, word in enumerate(words):

        text = normalize_text(
            word["text"]
        )

        if not re.search(
            r"(?:Rs\.?|₹)",
            text,
            re.I
        ):
            continue

        match = re.search(
            r"(?:Rs\.?|₹)\s*(\d+(?:\.\d{1,2})?)",
            text,
            re.I
        )

        if match:

            return make_result(
                value=float(match.group(1)),
                confidence=(
                    word["confidence"] / 100
                ),
                evidence=text,
                bbox=word["bbox"]
            )

    return None


# ============================================================
# NET QUANTITY
# ============================================================

UNIT_MAP = {

    "kg": "kg",
    "kgs": "kg",
    "kilo": "kg",
    "kilos": "kg",
    "kilogram": "kg",
    "kilograms": "kg",

    "g": "g",
    "gm": "g",
    "gms": "g",
    "gram": "g",
    "grams": "g",

    "mg": "mg",
    "mgs": "mg",
    "milligram": "mg",
    "milligrams": "mg",

    "l": "L",
    "lt": "L",
    "ltr": "L",
    "litre": "L",
    "litres": "L",
    "liter": "L",
    "liters": "L",

    "ml": "mL",
    "mls": "mL",
    "millilitre": "mL",
    "millilitres": "mL",
    "milliliter": "mL",
    "milliliters": "mL"
}


def parse_quantity(text):

    text = normalize_text(
        text
    ).strip()

    pattern = re.compile(
        r"(\d+(?:\.\d+)?)\s*"
        r"(kg|kgs|kilo|kilos|kilogram|kilograms|"
        r"g|gm|gms|gram|grams|"
        r"mg|mgs|milligram|milligrams|"
        r"ml|mls|millilitre|millilitres|"
        r"milliliter|milliliters|"
        r"l|lt|ltr|litre|litres|liter|liters)"
        r"\b",
        re.I
    )

    match = pattern.search(text)

    if not match:
        return None

    number = float(
        match.group(1)
    )

    unit = UNIT_MAP[
        match.group(2).lower()
    ]

    return number, unit


def extract_quantity(words):

    quantity_labels = {
        "net",
        "netweight",
        "netwt",
        "netquantity",
        "netqty",
        "netweightwhenpacked",
        "netwtwhenpacked"
    }

    # --------------------------------------------------------
    # PASS 1:
    #
    # NET WEIGHT: 246 g
    # NETWT: 100g
    # --------------------------------------------------------

    for i, word in enumerate(words):

        current = normalized_label(
            word["text"]
        )

        if current not in quantity_labels:
            continue

        nearby = words[
            i + 1:i + 10
        ]

        # Individual token
        for candidate in nearby:

            result = parse_quantity(
                candidate["text"]
            )

            if result:

                number, unit = result

                confidence = min(
                    word["confidence"],
                    candidate["confidence"]
                ) / 100

                confidence = min(
                    1.0,
                    confidence + 0.05
                )

                return make_result(
                    value=f"{number:g} {unit}",
                    confidence=confidence,
                    evidence=(
                        f"{word['text']} "
                        f"{candidate['text']}"
                    ),
                    bbox=candidate["bbox"]
                )

        # Two-token quantity:
        #
        # 246
        # g

        for j in range(
            len(nearby) - 1
        ):

            combined = (
                nearby[j]["text"]
                + " "
                + nearby[j + 1]["text"]
            )

            result = parse_quantity(
                combined
            )

            if result:

                number, unit = result

                confidence = min(
                    word["confidence"],
                    nearby[j]["confidence"],
                    nearby[j + 1]["confidence"]
                ) / 100

                return make_result(
                    value=f"{number:g} {unit}",
                    confidence=confidence,
                    evidence=(
                        f"{word['text']} "
                        f"{nearby[j]['text']} "
                        f"{nearby[j + 1]['text']}"
                    ),
                    bbox=nearby[j]["bbox"]
                )

    # --------------------------------------------------------
    # PASS 2:
    #
    # NET WEIGHT:
    # 2 Packs x 123 g
    #
    # Prefer the calculated total.
    # --------------------------------------------------------

    full_text = word_text(words)

    pack_pattern = re.compile(
        r"(\d+)\s*"
        r"(?:packs?|pieces?|pcs?)\s*"
        r"[xX×]\s*"
        r"(\d+(?:\.\d+)?)\s*"
        r"(kg|g|gm|gms|mg|ml|l)\b",
        re.I
    )

    match = pack_pattern.search(
        normalize_text(full_text)
    )

    if match:

        count = float(
            match.group(1)
        )

        amount = float(
            match.group(2)
        )

        unit = UNIT_MAP[
            match.group(3).lower()
        ]

        total = count * amount

        return make_result(
            value=f"{total:g} {unit}",
            confidence=0.80,
            evidence=match.group(0),
            bbox=None
        )

    return None


# ============================================================
# DATE PARSING
# ============================================================

DATE_PATTERNS = [

    r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",

    r"\b\d{1,2}-\d{1,2}-\d{2,4}\b",

    r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b",

    r"\b\d{1,2}/\d{2,4}\b",

    r"\b\d{1,2}-\d{2,4}\b",

    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
    r"\s+\d{4}\b",

    r"\b\d{1,2}\s+"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
    r"\s+\d{4}\b",

    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
    r"\s+\d{1,2}\s+\d{4}\b"
]


def parse_date(text):

    text = text.strip()

    formats = [

        "%d/%m/%Y",
        "%d/%m/%y",

        "%d-%m-%Y",
        "%d-%m-%y",

        "%d.%m.%Y",
        "%d.%m.%y",

        "%m/%Y",
        "%m-%Y",

        "%b %Y",
        "%B %Y",

        "%d %b %Y",
        "%d %B %Y",

        "%b %d %Y",
        "%B %d %Y"
    ]

    for fmt in formats:

        try:

            return datetime.strptime(
                text,
                fmt
            ).date()

        except ValueError:
            continue

    return None


def find_dates(words):

    dates = []

    for i in range(
        len(words)
    ):

        nearby = words[
            i:i + 5
        ]

        text = word_text(
            nearby
        )

        for pattern in DATE_PATTERNS:

            matches = re.findall(
                pattern,
                text,
                re.I
            )

            for match in matches:

                parsed = parse_date(
                    match
                )

                if parsed is None:
                    continue

                dates.append({

                    "value": match,

                    "date": parsed,

                    "confidence":
                        safe_confidence(
                            nearby
                        ),

                    "bbox":
                        words[i]["bbox"]
                })

    # Remove duplicates
    unique = {}

    for item in dates:

        unique[
            item["date"]
        ] = item

    return list(
        unique.values()
    )


# ============================================================
# MANUFACTURING DATE
# ============================================================

def extract_manufacturing_date(words):

    labels = {

        "mfg",
        "mfd",
        "manufacturing",
        "manufactured",
        "manufacturingdate",
        "dateofmanufacture",
        "mfgdate",
        "mfgdt",
        "mfddate",
        "mfgmonth",
        "packed",
        "packedon",
        "packingdate"
    }

    for i, word in enumerate(words):

        current = normalized_label(
            word["text"]
        )

        if current not in labels:
            continue

        nearby = words[
            i:i + 10
        ]

        dates = find_dates(
            nearby
        )

        if dates:

            item = dates[0]

            return make_result(

                value=item["value"],

                confidence=min(
                    1.0,
                    item["confidence"] + 0.05
                ),

                evidence=word_text(
                    nearby
                ),

                bbox=item["bbox"]
            )

    # --------------------------------------------------------
    # Fallback:
    #
    # Look for "Made in India by..." etc.
    # without requiring exact MFG label.
    # --------------------------------------------------------

    for i, word in enumerate(words):

        text = normalize_text(
            word["text"]
        ).lower()

        if text in {
            "mfg.",
            "mfd.",
            "mfg",
            "mfd"
        }:

            nearby = words[
                i:i + 10
            ]

            dates = find_dates(
                nearby
            )

            if dates:

                item = dates[0]

                return make_result(
                    value=item["value"],
                    confidence=item["confidence"],
                    evidence=word_text(
                        nearby
                    ),
                    bbox=item["bbox"]
                )

    return None


# ============================================================
# BEST BEFORE
# ============================================================

def extract_best_before(words):

    duration_pattern = re.compile(

        r"(\d+(?:\.\d+)?)\s*"
        r"(day|days|month|months|year|years)",

        re.I
    )

    expiry_pattern = re.compile(

        r"(?:best\s*before|bestbefore|use\s*by|expiry|expires?|exp|bbe)\s*:?\s*"
        r"("
        r"\d{1,2}/\d{1,2}/\d{2,4}"
        r"|"
        r"\d{1,2}-\d{1,2}-\d{2,4}"
        r"|"
        r"\d{1,2}/\d{2,4}"
        r"|"
        r"\d{1,2}-\d{2,4}"
        r"|"
        r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}"
        r"|"
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}"
        r")",

        re.I
    )

    labels = {

        "best",
        "before",
        "use",
        "expiry",
        "expires",
        "exp",
        "shelf",
        "useby",
        "bestbefore"
    }

    for i, word in enumerate(words):

        current = normalized_label(
            word["text"]
        )

        if current not in labels:
            continue

        nearby = words[
            i:i + 12
        ]

        local_text = normalize_text(
            word_text(nearby)
        )

        # Duration
        match = duration_pattern.search(
            local_text
        )

        if match:

            value = (
                f"{match.group(1)} "
                f"{match.group(2).lower()}"
            )

            return make_result(

                value=value,

                confidence=min(
                    1.0,
                    safe_confidence(nearby)
                    + 0.05
                ),

                evidence=local_text,

                bbox=nearby[0]["bbox"]
            )

        # Expiry date
        match = expiry_pattern.search(
            local_text
        )

        if match:

            return make_result(

                value=match.group(1),

                confidence=min(
                    1.0,
                    safe_confidence(nearby)
                    + 0.05
                ),

                evidence=local_text,

                bbox=nearby[0]["bbox"]
            )

        dates = find_dates(nearby)

        if dates:

            item = dates[0]

            return make_result(

                value=item["value"],

                confidence=min(
                    1.0,
                    item["confidence"] + 0.05
                ),

                evidence=local_text,

                bbox=item["bbox"]
            )

    return None


# ============================================================
# PRODUCT NAME
# ============================================================

def extract_product_name(words):

    stop_labels = {

        "net",
        "netweight",
        "mrp",
        "mfg",
        "mfd",
        "manufacturing",
        "manufactured",
        "packed",
        "packer",
        "importer",
        "country",
        "consumer",
        "unit",
        "best",
        "before",
        "date",
        "batch",
        "ingredients",
        "composition",
        "quantity",
        "qty",
        "price",
        "contact",
        "care",
        "expiry",
        "use",
        "by",
        "made",
        "in"
    }

    # --------------------------------------------------------
    # PASS 1:
    #
    # Product Name: XXXXX
    # --------------------------------------------------------

    for i in range(
        len(words) - 1
    ):

        first = normalized_label(
            words[i]["text"]
        )

        second = normalized_label(
            words[i + 1]["text"]
        )

        if first != "product":
            continue

        if second != "name":
            continue

        candidates = words[
            i + 2:i + 9
        ]

        collected = []

        for candidate in candidates:

            value = candidate["text"].strip()

            if not value:
                continue

            cleaned = normalized_label(
                value
            )

            if cleaned in stop_labels:
                break

            if re.fullmatch(
                r"[^a-zA-Z0-9]+",
                value
            ):
                continue

            if candidate["confidence"] < 40:
                continue

            collected.append(
                candidate
            )

        if collected:

            value = " ".join(
                item["text"]
                for item in collected
            )

            return make_result(

                value=value.strip(),

                confidence=safe_confidence(
                    collected
                ),

                evidence=(
                    f"Product Name "
                    f"{value}"
                ),

                bbox=collected[0]["bbox"]
            )

    # --------------------------------------------------------
    # PASS 2:
    #
    # Product names are often the first meaningful phrase near
    # the top of the label, before price, quantity, and dates.
    # --------------------------------------------------------

    top_words = words[:80]
    metadata_tokens = {"mrp", "net", "mfg", "mfd", "manufactured", "manufacturing",
                       "best", "before", "expiry", "use", "quantity", "qty", "price",
                       "country", "origin", "importer", "packer", "packed", "consumer",
                       "care", "batch", "date"}

    candidate_words = []
    for word in top_words:
        token = normalized_label(word["text"])
        if token in metadata_tokens:
            break

        value = word["text"].strip()
        if not value:
            continue
        if re.fullmatch(r"[^a-zA-Z0-9]+", value):
            continue
        if value.lower() in {"and", "for", "of", "with", "by", "the"}:
            continue
        if word.get("confidence", 0) < 35:
            continue
        candidate_words.append(word)

    if len(candidate_words) >= 2:
        value = " ".join(item["text"] for item in candidate_words[:8]).strip()
        if value:
            return make_result(
                value=value,
                confidence=safe_confidence(candidate_words[:8]),
                evidence=value,
                bbox=candidate_words[0]["bbox"]
            )

    # --------------------------------------------------------
    # PASS 3:
    #
    # Common/generic descriptors.
    #
    # Example:
    # AYURVEDIC SOAP
    # TOILET SOAP
    # --------------------------------------------------------

    generic_patterns = [

        r"\b(?:ayurvedic|herbal|natural|"
        r"toilet|bath|beauty|medicated|"
        r"liquid|hand|body|face)\s+"
        r"(?:soap|wash|cream|lotion|"
        r"shampoo|oil|powder|gel|"
        r"tablet|capsule|syrup)\b"

    ]

    # Search first ~40 words because product names
    # are commonly near the top of the label.

    top_words = words[:40]

    for i, word in enumerate(top_words):

        local = word_text(
            top_words[i:i + 5]
        )

        for pattern in generic_patterns:

            match = re.search(
                pattern,
                local,
                re.I
            )

            if not match:
                continue

            value = match.group(0).strip()

            return make_result(

                value=value,

                confidence=min(
                    1.0,
                    safe_confidence(
                        top_words[i:i + 5]
                    ) + 0.10
                ),

                evidence=local,

                bbox=word["bbox"]
            )

    return None


# ============================================================
# COUNTRY OF ORIGIN
# ============================================================

COUNTRY_NAMES = {
    "india", "indian",
    "usa", "united states", "united states of america", "america",
    "uk", "united kingdom", "england", "wales", "scotland",
    "china", "japan", "korea", "germany", "france", "italy",
    "spain", "netherlands", "switzerland", "canada", "australia",
    "new zealand", "singapore", "thailand", "vietnam", "malaysia",
    "indonesia", "brazil", "mexico", "argentina", "egypt", "uae",
    "oman", "saudi arabia", "qatar", "iran", "pakistan", "nepal",
    "bangladesh", "sri lanka"
}


def extract_country_of_origin(words):

    # --------------------------------------------------------
    # "Made in India"
    # --------------------------------------------------------

    for i in range(
        len(words) - 2
    ):

        first = normalized_label(
            words[i]["text"]
        )

        second = normalized_label(
            words[i + 1]["text"]
        )

        if first != "made":
            continue

        if second != "in":
            continue

        candidate = words[
            i + 2
        ]

        country = candidate[
            "text"
        ].strip()

        if country:

            return make_result(

                value=country,

                confidence=min(
                    1.0,
                    safe_confidence(
                        words[i:i + 3]
                    ) + 0.05
                ),

                evidence=word_text(
                    words[i:i + 3]
                ),

                bbox=candidate["bbox"]
            )

    # --------------------------------------------------------
    # "Origin: India" / "Country: India" / "Product of India"
    # --------------------------------------------------------

    for i, word in enumerate(words):

        text = normalized_label(word["text"])

        if text not in {"origin", "country", "made", "product", "of"}:
            continue

        nearby = words[i:i + 8]
        local = word_text(nearby)

        match = re.search(
            r"(?:country\s+of\s+origin|origin|made\s+in|product\s+of)\s*[:\-]?\s*"
            r"([A-Za-z][A-Za-z\s.-]{2,40})",
            local,
            re.I,
        )

        if not match:
            continue

        candidate = match.group(1).strip()
        cleaned = clean_word(candidate)

        if not candidate or len(cleaned) < 3:
            continue

        if clean_word(candidate).lower() not in COUNTRY_NAMES and not candidate.lower().startswith(tuple(COUNTRY_NAMES)):
            continue

        return make_result(
            value=candidate,
            confidence=min(1.0, safe_confidence(nearby) + 0.05),
            evidence=local,
            bbox=nearby[0]["bbox"] if nearby else word["bbox"],
        )

    # --------------------------------------------------------
    # "Country of Origin: India"
    # --------------------------------------------------------

    for i, word in enumerate(words):

        current = normalized_label(
            word["text"]
        )

        if current != "country":
            continue

        nearby = words[
            i:i + 8
        ]

        normalized = [
            normalized_label(
                w["text"]
            )
            for w in nearby
        ]

        if "origin" not in normalized:
            continue

        origin_index = normalized.index(
            "origin"
        )

        for candidate in nearby[
            origin_index + 1:
        ]:

            value = candidate[
                "text"
            ].strip()

            cleaned = clean_word(
                value
            )

            if cleaned in {
                "",
                "of",
                ":",
                "-",
                "/"
            }:
                continue

            if not cleaned.isalpha():
                continue

            if len(cleaned) < 3:
                continue

            return make_result(

                value=value,

                confidence=(
                    candidate["confidence"]
                    / 100
                ),

                evidence=word_text(
                    nearby
                ),

                bbox=candidate["bbox"]
            )

        return make_result(

            value=None,

            confidence=(
                word["confidence"]
                / 100
            ),

            evidence=word_text(
                nearby
            ),

            bbox=word["bbox"],

            status="label_found_value_missing"
        )

    return make_result(
        status="label_not_found"
    )


# ============================================================
# MANUFACTURER
# ============================================================

def extract_manufacturer(words):

    labels = {

        "manufactured",
        "manufacturer",
        "manufacturedby",

        "manufacturedby",
        "mfgby",
        "mfdby",

        "packer",
        "packedby",
        "packed",

        "importer",
        "importedby",

        "marketedby",
        "mktdby",

        "made"
    }

    stop_labels = {

        "mrp",
        "net",
        "netweight",
        "mfg",
        "mfd",
        "date",
        "best",
        "before",
        "country",
        "origin",
        "consumer",
        "unit",
        "batch",
        "ingredients",
        "composition",
        "quality",
        "license"
    }

    for i, word in enumerate(words):

        current = normalized_label(
            word["text"]
        )

        # Handle:
        #
        # Mfg By
        # Mfd By
        # Manufactured By
        #

        next_label = ""

        if i + 1 < len(words):

            next_label = normalized_label(
                words[i + 1]["text"]
            )

        combined = (
            current +
            next_label
        )

        if current not in labels and \
           combined not in labels:

            continue

        start = i + 1

        # Skip "by", if present
        if start < len(words):

            if normalized_label(
                words[start]["text"]
            ) == "by":

                start += 1

        candidates = words[
            start:start + 12
        ]

        collected = []

        for candidate in candidates:

            value = candidate[
                "text"
            ].strip()

            if not value:
                continue

            cleaned = normalized_label(
                value
            )

            if cleaned in stop_labels:
                break

            if cleaned in {
                "by",
                "sy",
                "dy",
                ":",
                "-"
            }:
                continue

            if re.fullmatch(
                r"[^a-zA-Z0-9]+",
                value
            ):
                continue

            if candidate["confidence"] < 30:
                continue

            collected.append(
                candidate
            )

        if not collected:
            continue

        value = " ".join(
            item["text"]
            for item in collected
        ).strip()

        if not value:
            continue

        confidence = safe_confidence(
            collected
        )

        confidence = min(
            1.0,
            confidence + 0.05
        )

        return make_result(

            value=value,

            confidence=confidence,

            evidence=(
                f"{word['text']} "
                f"{value}"
            ),

            bbox=collected[0]["bbox"]
        )

    return None


# ============================================================
# CONSUMER CARE
# ============================================================

def extract_consumer_care(words):

    phone_pattern = re.compile(

        r"(?:\+91[\s-]?)?"
        r"\d[\d\s-]{8,12}\d"

    )

    email_pattern = re.compile(

        r"[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\."
        r"[A-Za-z]{2,}"

    )

    labels = {

        "consumer",
        "care",
        "helpline",
        "customer",
        "contact",
        "tollfree",
        "email",
        "feedback",
        "queries",
        "complaint"
    }

    for i, word in enumerate(words):

        current = normalized_label(
            word["text"]
        )

        if current not in labels:
            continue

        nearby = words[
            i + 1:i + 15
        ]

        for candidate in nearby:

            value = candidate[
                "text"
            ].strip()

            phone = phone_pattern.search(
                value
            )

            email = email_pattern.search(
                value
            )

            if phone:

                return make_result(

                    value=phone.group(),

                    confidence=(
                        candidate["confidence"]
                        / 100
                    ),

                    evidence=(
                        f"{word['text']} "
                        f"{value}"
                    ),

                    bbox=candidate["bbox"]
                )

            if email:

                return make_result(

                    value=email.group(),

                    confidence=(
                        candidate["confidence"]
                        / 100
                    ),

                    evidence=(
                        f"{word['text']} "
                        f"{value}"
                    ),

                    bbox=candidate["bbox"]
                )

    return None


# ============================================================
# UNIT SALE PRICE
# ============================================================

def extract_unit_sale_price(words):

    labels = {

        "unit",
        "unitprice",
        "saleprice",
        "unitsaleprice",
        "sellingprice",
        "perunit",
        "priceperunit"
    }

    for i, word in enumerate(words):

        current = normalized_label(
            word["text"]
        )

        if current not in labels:
            continue

        nearby = words[
            i + 1:i + 8
        ]

        local_text = word_text(
            nearby
        )

        match = re.search(

            r"(?:Rs\.?|₹)?\s*"
            r"(\d+(?:\.\d{1,2})?)",

            normalize_text(
                local_text
            ),

            re.I
        )

        if not match:
            match = re.search(
                r"(\d+(?:\.\d{1,2})?)\s*(?:/|per)\s*(?:\d+\s*)?(?:g|kg|ml|l|pc|piece|unit)",
                normalize_text(local_text),
                re.I,
            )

        if not match:
            continue

        return make_result(

            value=float(
                match.group(1)
            ),

            confidence=safe_confidence(
                nearby
            ),

            evidence=(
                f"{word['text']} "
                f"{local_text}"
            ),

            bbox=nearby[0]["bbox"]
            if nearby
            else word["bbox"]
        )

    # ------------------------------------------------------------------
    # Fallback: look for patterns like "Rs. 45 / 100g" or "₹45 / pc"
    # ------------------------------------------------------------------

    full_text = normalize_text(word_text(words))
    match = re.search(
        r"(?:Rs\.?|₹)?\s*(\d+(?:\.\d{1,2})?)\s*(?:/|per)\s*(?:\d+\s*)?(?:g|kg|ml|l|pc|piece|unit)",
        full_text,
        re.I,
    )

    if match:
        return make_result(
            value=float(match.group(1)),
            confidence=0.75,
            evidence=match.group(0),
            bbox=None,
        )

    return None


# ============================================================
# MAIN EXTRACTION
# ============================================================

def extract_fields(ocr_result):

    if not isinstance(ocr_result, dict):
        ocr_result = {}

    words = ocr_result.get(
        "words",
        []
    )

    if not isinstance(words, list):
        words = []

    fields = {

        "mrp":
            extract_mrp(words),

        "net_quantity":
            extract_quantity(words),

        "manufacturing_date":
            extract_manufacturing_date(
                words
            ),

        "best_before":
            extract_best_before(
                words
            ),

        "product_name":
            extract_product_name(
                words
            ),

        "country_of_origin":
            extract_country_of_origin(
                words
            ),

        "manufacturer":
            extract_manufacturer(
                words
            ),

        "consumer_care":
            extract_consumer_care(
                words
            ),

        "unit_sale_price":
            extract_unit_sale_price(
                words
            )
    }

    return fields