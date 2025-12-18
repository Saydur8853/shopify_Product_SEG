import csv
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse


def _find_template_csv_path() -> Path | None:
    candidates = [
        Path(settings.BASE_DIR) / "product_upload_template.csv",
        Path(settings.BASE_DIR).parent / "product_upload_template.csv",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def get_shopify_headers(model) -> list[str]:
    template_path = _find_template_csv_path()
    if template_path:
        with template_path.open("r", newline="", encoding="utf-8-sig") as file:
            reader = csv.reader(file)
            return next(reader)

    headers: list[str] = []
    for field in model._meta.fields:
        if field.primary_key:
            continue
        db_column = getattr(field, "db_column", None)
        if not db_column:
            continue
        headers.append(db_column)
    return headers


def _shopify_cell_value(header: str, value):
    if value is None:
        return ""

    if header == "Continue selling when out of stock":
        return "continue" if bool(value) else "deny"

    if header == "Weight unit for display":
        allowed = {"g", "kg", "lb", "oz"}
        val = str(value).strip().lower()
        return val if val in allowed else ""

    if header in {"Unit price total measure unit", "Unit price base measure unit"}:
        # Shopify-supported measurement units
        allowed = {
            "ml",
            "cl",
            "l",
            "cm3",
            "m3",
            "fl oz",
            "oz",
            "cup",
            "pt",
            "qt",
            "gal",
            "mm",
            "cm",
            "m",
            "in",
            "ft",
            "yd",
            "g",
            "kg",
            "lb",
        }
        val = str(value).strip().lower()
        return val if val in allowed else ""

    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"

    return str(value)


def _split_image_values(value: str | None) -> list[str]:
    """Split stored image URLs separated by commas or newlines."""
    if value is None:
        return []
    cleaned = str(value).replace("\r\n", "\n").replace("\r", "\n")
    parts: list[str] = []
    for chunk in cleaned.split("\n"):
        for piece in chunk.split(","):
            item = piece.strip()
            if item:
                parts.append(item)
    return parts


def queryset_to_shopify_csv_response(*, queryset, filename_prefix: str = "shopify_products") -> HttpResponse:
    model = queryset.model
    headers = get_shopify_headers(model)

    field_by_column: dict[str, str] = {}
    for field in model._meta.fields:
        if field.primary_key:
            continue
        column = getattr(field, "db_column", None) or str(field.verbose_name)
        field_by_column[column] = field.name

    def _rows_for_obj(obj):
        base_row: dict[str, str] = {}
        for header in headers:
            field_name = field_by_column.get(header)
            value = getattr(obj, field_name) if field_name else ""
            base_row[header] = _shopify_cell_value(header, value)

        product_images = _split_image_values(base_row.get("Product image URL"))
        variant_images = _split_image_values(base_row.get("Variant image URL"))
        image_count = max(len(product_images), len(variant_images))

        if image_count == 0:
            yield [base_row.get(h, "") for h in headers]
            return

        handle_header = next((h for h, f in field_by_column.items() if f == "url_handle"), None)
        for idx in range(image_count):
            row_data = base_row.copy() if idx == 0 else {h: "" for h in headers}
            if idx > 0 and handle_header:
                row_data[handle_header] = base_row.get(handle_header, "")
            row_data["Product image URL"] = product_images[idx] if idx < len(product_images) else ""
            row_data["Variant image URL"] = variant_images[idx] if idx < len(variant_images) else ""
            if "Image position" in headers:
                row_data["Image position"] = str(idx + 1)
            yield [row_data.get(h, "") for h in headers]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.csv"

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(headers)
    for obj in queryset.iterator():
        for row in _rows_for_obj(obj):
            writer.writerow(row)

    return response
