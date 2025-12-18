from __future__ import annotations

from datetime import datetime
from io import BytesIO

from django.http import HttpResponse

from .csv_export import get_shopify_headers

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

    def _coerce_value(value):
        if value is None:
            return ""
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        return str(value)

    workbook = openpyxl.Workbook(write_only=True)
    sheet = workbook.create_sheet("Products")

    sheet.append(headers)
    for obj in queryset.iterator():
        row = []
        for header in headers:
            field_name = field_by_column.get(header)
            value = getattr(obj, field_name) if field_name else ""
            row.append(_coerce_value(value))
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
