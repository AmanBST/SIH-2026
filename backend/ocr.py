import cv2
import pytesseract
from pytesseract import Output


# ============================================================
# IMAGE UPSCALING
# ============================================================

def upscale_image(image, scale=3):

    return cv2.resize(
        image,
        None,
        fx=scale,
        fy=scale,
        interpolation=cv2.INTER_CUBIC
    )


# ============================================================
# CONTRAST ENHANCEMENT
# ============================================================

def enhance_contrast(image):

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    return clahe.apply(gray)


# ============================================================
# CREATE OCR VARIANTS
# ============================================================

def create_variants(image):

    # Upscale once
    enlarged = upscale_image(
        image,
        scale=3
    )

    # Grayscale
    gray = cv2.cvtColor(
        enlarged,
        cv2.COLOR_BGR2GRAY
    )

    # Contrast enhanced
    contrast = enhance_contrast(
        enlarged
    )

    # OTSU
    _, otsu = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    # Adaptive threshold
    adaptive = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11
    )

    return {
        "original": enlarged,
        "gray": gray,
        "contrast": contrast,
        "otsu": otsu,
        "adaptive": adaptive
    }


# ============================================================
# RUN TESSERACT
# ============================================================

def run_tesseract(image):

    data = pytesseract.image_to_data(
        image,
        config="--psm 3",
        output_type=Output.DICT
    )

    words = []

    for i in range(len(data["text"])):

        text = data["text"][i].strip()

        try:
            confidence = float(
                data["conf"][i]
            )
        except (ValueError, TypeError):
            confidence = -1

        if not text:
            continue

        if confidence < 0:
            continue

        words.append({
            "text": text,
            "confidence": confidence,
            "bbox": {
                "x": data["left"][i],
                "y": data["top"][i],
                "width": data["width"][i],
                "height": data["height"][i]
            }
        })

    return words


# ============================================================
# OCR QUALITY SCORE
# ============================================================

def calculate_score(words):

    if not words:
        return 0

    # --------------------------------------------------------
    # Average OCR confidence
    # --------------------------------------------------------

    average_confidence = sum(
        word["confidence"]
        for word in words
    ) / len(words)

    # --------------------------------------------------------
    # Important Legal Metrology keywords
    # --------------------------------------------------------

    legal_keywords = [
        "mrp",
        "quantity",
        "qty",
        "net",
        "manufactured",
        "manufacturing",
        "mfg",
        "mfd",
        "packed",
        "packer",
        "manufacturer",
        "importer",
        "country",
        "origin",
        "best",
        "before",
        "use",
        "consumer",
        "care",
        "price"
    ]

    keyword_score = 0

    for word in words:

        text = word["text"].lower()

        for keyword in legal_keywords:

            if keyword in text:
                keyword_score += 1
                break

    # Prevent keyword score from dominating
    keyword_score = min(
        keyword_score,
        20
    )

    keyword_score = (
        keyword_score / 20
    ) * 100

    # --------------------------------------------------------
    # Final score
    # --------------------------------------------------------

    score = (
        average_confidence * 0.85
        + keyword_score * 0.15
    )

    return score


# ============================================================
# BUILD OCR RESULT
# ============================================================

def build_result(
    method,
    words
):

    text = " ".join(
        word["text"]
        for word in words
    )

    score = calculate_score(
        words
    )

    return {
        "method": method,
        "score": score,
        "text": text,
        "words": words
    }


# ============================================================
# MAIN OCR FUNCTION
# ============================================================

def extract_text(image_path):

    image = cv2.imread(
        image_path
    )

    if image is None:

        raise ValueError(
            f"Could not read image: "
            f"{image_path}"
        )

    # --------------------------------------------------------
    # Create preprocessing variants
    # --------------------------------------------------------

    variants = create_variants(
        image
    )

    results = []

    # --------------------------------------------------------
    # Run OCR on every variant
    # --------------------------------------------------------

    for method, processed_image in variants.items():

        words = run_tesseract(
            processed_image
        )

        result = build_result(
            method,
            words
        )

        results.append(
            result
        )

    # --------------------------------------------------------
    # Select best OCR result
    # --------------------------------------------------------

    best = max(
        results,
        key=lambda result: result["score"]
    )

    return best