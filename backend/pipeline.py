from ocr import extract_text
from field_extractor import extract_fields
from rules import validate_fields


def process_image(image_path):

    ocr_result = extract_text(image_path)

    fields = extract_fields(
        ocr_result
    )

    violations = validate_fields(
        fields
    )

    if not violations:
        compliance_status = "COMPLIANT"
    else:
        missing_only = all(
            fields.get(violation["field"]) is None
            or fields[violation["field"]].get("value") is None
            for violation in violations
        )

        high_severity = any(
            violation["severity"] == "HIGH"
            for violation in violations
        )

        if missing_only:
            compliance_status = "REVIEW_REQUIRED"
        elif high_severity:
            compliance_status = "NON_COMPLIANT"
        else:
            compliance_status = "REVIEW_REQUIRED"

    return {
        "ocr": {
            "method": ocr_result["method"],
            "score": ocr_result["score"],
            "text": ocr_result["text"]
        },

        "fields": fields,

        "violations": violations,

        "compliance": {
            "status": compliance_status,
            "violation_count": len(violations)
        }
    }