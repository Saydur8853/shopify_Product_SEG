from __future__ import annotations

from datetime import datetime
from io import BytesIO

from django.http import HttpResponse

from .csv_export import get_shopify_headers, _shopify_cell_value

try:
    import openpyxl
except Exception:  # pragma: no cover
    openpyxl = None


def queryset_to_shopify_xlsx_response(*, queryset, filename_prefix: str = "shopify_products") -> HttpResponse:
    if openpyxl is None:  # pragma: no cover
        raise RuntimeError("Excel export is not available (openpyxl is not installed).")

    model = queryset.model
    headers = get_shopify_headers(model)

    field_by_column: dict[str, str] = {}
    for field in model._meta.fields:
        if field.primary_key:
            continue
        column = getattr(field, "db_column", None) or str(field.verbose_name)
        field_by_column[column] = field.name

    def _split_image_values(value: str | None) -> list[str]:
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

    workbook = openpyxl.Workbook(write_only=True)
    sheet = workbook.create_sheet("Products")

    sheet.append(headers)
    for obj in queryset.iterator():
        for row in _rows_for_obj(obj):
            sheet.append(row)

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.xlsx"

    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
