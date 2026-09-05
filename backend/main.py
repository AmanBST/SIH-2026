import os

from ocr import extract_text
from field_extractor import extract_fields
from compliance_engine import check_compliance


def run_compliance_check(image_path):
    """
    Run the complete compliance pipeline for one image.

    Pipeline:
        Image -> OCR -> Field Extraction -> Compliance Check
    """

    print("\n")
    print("==========================================")
    print(f"PROCESSING: {image_path}")
    print("==========================================")

    # ============================================
    # STEP 1 — OCR
    # ============================================

    print("\n")
    print("==========================================")
    print("[1/3] EXTRACTING TEXT")
    print("==========================================")

    ocr_result = extract_text(image_path)

    print("\n---------- OCR SUMMARY ----------")

    print(
        f"OCR Method      : "
        f"{ocr_result['method']}"
    )

    print(
        f"OCR Score       : "
        f"{ocr_result['score']:.2f}"
    )

    print(
        f"Words Detected  : "
        f"{len(ocr_result['words'])}"
    )

    print("\n---------- RAW OCR TEXT ----------")

    print(ocr_result["text"])

    # ============================================
    # STEP 2 — FIELD EXTRACTION
    # ============================================

    print("\n")
    print("==========================================")
    print("[2/3] EXTRACTING PRODUCT INFORMATION")
    print("==========================================")

    fields = extract_fields(ocr_result)

    print("\n---------- EXTRACTED FIELDS ----------")

    for field, data in fields.items():

        print(f"\n{field}:")

        if data is None:

            print("  ❌ Not detected")

        else:

            print(
                f"  Value      : "
                f"{data['value']}"
            )

            print(
                f"  Confidence : "
                f"{data['confidence']:.2f}"
            )

            print(
                f"  Evidence   : "
                f"{data['evidence']}"
            )

            print(
                f"  BBox       : "
                f"{data['bbox']}"
            )

    # ============================================
    # STEP 3 — COMPLIANCE
    # ============================================

    print("\n")
    print("==========================================")
    print("[3/3] CHECKING COMPLIANCE")
    print("==========================================")

    # Compliance engine currently expects
    # simple field values rather than the
    # complete extraction objects.

    compliance_fields = {}

    for field, data in fields.items():

        if data is None:
            compliance_fields[field] = None
        else:
            compliance_fields[field] = data["value"]

    # --------------------------------------------
    # Import status
    # --------------------------------------------

    # Currently we do not automatically determine
    # whether a product is imported.
    #
    # Therefore this remains False until that
    # functionality is implemented.

    compliance_fields["is_imported"] = False

    result = check_compliance(
        compliance_fields
    )

    # ============================================
    # FINAL REPORT
    # ============================================

    print("\n")
    print("==========================================")
    print("FINAL COMPLIANCE REPORT")
    print("==========================================")

    print(
        "\nSTATUS:",
        result["status"]
    )

    # --------------------------------------------
    # PASSED
    # --------------------------------------------

    print("\n---------- PASSED ----------")

    if result["passed"]:

        for item in result["passed"]:

            print(
                "✅",
                item["field"]
            )

    else:

        print("None")

    # --------------------------------------------
    # NEEDS VERIFICATION
    # --------------------------------------------

    print("\n---------- NEEDS VERIFICATION ----------")

    if result["verification"]:

        for item in result["verification"]:

            print(
                f"⚠️ [{item['rule_id']}] "
                f"{item['field']}: "
                f"{item['message']}"
            )

    else:

        print("None")

    # --------------------------------------------
    # CONFIRMED VIOLATIONS
    # --------------------------------------------

    print("\n---------- CONFIRMED VIOLATIONS ----------")

    if result["violations"]:

        for item in result["violations"]:

            print(
                f"❌ [{item['rule_id']}] "
                f"{item['field']}: "
                f"{item['message']}"
            )

    else:

        print("None")

    return {
        "image_path": image_path,
        "ocr": ocr_result,
        "fields": fields,
        "compliance": result
    }


# =================================================
# DATASET TESTING
# =================================================

def run_dataset(dataset_path="uploads/labels"):
    """
    Run the complete pipeline on every image
    inside the dataset.

    Expected structure:

        uploads/
            labels/
                cosmetics/
                medicine/
                food/
    """

    supported_extensions = (
        ".jpg",
        ".jpeg",
        ".png",
        ".webp"
    )

    results = []

    print("\n")
    print("==========================================")
    print("DATASET TESTING")
    print("==========================================")

    print(
        f"\nDataset: {dataset_path}"
    )

    # --------------------------------------------
    # Check dataset directory
    # --------------------------------------------

    if not os.path.exists(dataset_path):

        print(
            f"\n❌ Dataset not found: "
            f"{dataset_path}"
        )

        return results

    # --------------------------------------------
    # Walk through all categories
    # --------------------------------------------

    for root, directories, files in os.walk(
        dataset_path
    ):

        for filename in sorted(files):

            if not filename.lower().endswith(
                supported_extensions
            ):
                continue

            image_path = os.path.join(
                root,
                filename
            )

            # Category = folder containing image
            category = os.path.basename(root)

            print("\n\n")
            print("##########################################")
            print(f"CATEGORY : {category}")
            print(f"IMAGE    : {filename}")
            print("##########################################")

            try:

                result = run_compliance_check(
                    image_path
                )

                results.append({
                    "image": image_path,
                    "category": category,
                    "status": result["compliance"]["status"]
                })

            except Exception as e:

                print("\n❌ ERROR PROCESSING IMAGE")
                print(e)

                results.append({
                    "image": image_path,
                    "category": category,
                    "status": "ERROR",
                    "error": str(e)
                })

    # ============================================
    # DATASET SUMMARY
    # ============================================

    print("\n\n")
    print("==========================================")
    print("DATASET TEST SUMMARY")
    print("==========================================")

    if not results:

        print("\nNo images found.")

        return results

    total = len(results)

    compliant = sum(
        1
        for result in results
        if result["status"] == "COMPLIANT"
    )

    needs_verification = sum(
        1
        for result in results
        if result["status"] == "NEEDS_VERIFICATION"
    )

    non_compliant = sum(
        1
        for result in results
        if result["status"] == "NON_COMPLIANT"
    )

    errors = sum(
        1
        for result in results
        if result["status"] == "ERROR"
    )

    print(f"\nTotal Images        : {total}")
    print(f"✅ Compliant        : {compliant}")
    print(f"⚠️ Needs Verification: {needs_verification}")
    print(f"❌ Non-Compliant    : {non_compliant}")
    print(f"💥 Errors           : {errors}")

    print("\n---------- IMAGE RESULTS ----------")

    for result in results:

        print(
            f"\n{result['category']:12} | "
            f"{result['status']:20} | "
            f"{result['image']}"
        )

    return results


# =================================================
# PROGRAM ENTRY
# =================================================

if __name__ == "__main__":

    # ============================================
    # DATASET TESTING
    # ============================================
    #
    # Your current dataset:
    #
    # uploads/
    # └── labels/
    #     ├── cosmetics/
    #     ├── medicine/
    #     └── food/
    #
    # Running this will automatically process
    # all images inside these folders.

    run_dataset(
        "uploads/labels"
    )