from rules import RULES


def is_applicable(rule, fields):
    """
    Determine whether a rule applies to this product.
    """

    condition = rule.get("condition")

    if condition is None:
        return True

    if condition == "imported":
        return fields.get("is_imported", False)

    if condition == "where_applicable":
        return True

    return True


from rules import RULES


def is_applicable(rule, fields):
    """
    Determine whether a rule applies to this product.
    """

    condition = rule.get("condition")

    if condition is None:
        return True

    if condition == "imported":
        return fields.get("is_imported", False)

    if condition == "where_applicable":
        return True

    return True


def check_compliance(fields):
    """
    Check extracted fields against Legal Metrology rules.

    Missing information is treated as NEEDS_VERIFICATION,
    not automatically as a confirmed legal violation.
    """

    passed = []
    verification = []
    violations = []

    for rule_id, rule in RULES.items():

        # -----------------------------------------
        # Check applicability
        # -----------------------------------------

        if not is_applicable(rule, fields):
            continue

        field_name = rule["field"]

        result = fields.get(field_name)

        # -----------------------------------------
        # Determine actual extracted value
        # -----------------------------------------

        extracted_value = None

        if isinstance(result, dict):
            extracted_value = result.get("value")
        else:
            extracted_value = result

        # -----------------------------------------
        # Field exists
        # -----------------------------------------

        if extracted_value is not None and extracted_value != "":

            passed.append({
                "rule_id": rule_id,
                "field": field_name,
                "name": rule["name"],
                "message": "Required information detected.",
                "source": rule.get("source")
            })

        # -----------------------------------------
        # Field missing
        # -----------------------------------------

        else:

            verification.append({
                "rule_id": rule_id,
                "field": field_name,
                "name": rule["name"],
                "message": rule["message"],
                "source": rule.get("source")
            })

    # =============================================
    # Determine overall status
    # =============================================

    if violations:
        status = "NON_COMPLIANT"

    elif verification:
        status = "NEEDS_VERIFICATION"

    else:
        status = "COMPLIANT"

    # =============================================
    # Final result
    # =============================================

    return {
        "status": status,
        "passed": passed,
        "verification": verification,
        "violations": violations
    }