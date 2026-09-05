from pipeline import process_image


image_path = "test_images/product.jpg"

result = process_image(
    image_path
)

print("\n==============================")
print("COMPLIANCE RESULT")
print("==============================")

print(
    "Status:",
    result["compliance"]["status"]
)

print(
    "Violations:",
    result["compliance"]["violation_count"]
)

print("\n------------------------------")
print("EXTRACTED FIELDS")
print("------------------------------")

for field, data in result["fields"].items():

    print(
        f"{field}:",
        data
    )

print("\n------------------------------")
print("VIOLATIONS")
print("------------------------------")

for violation in result["violations"]:

    print(
        f"[{violation['severity']}] "
        f"{violation['name']}: "
        f"{violation['message']}"
    )
    