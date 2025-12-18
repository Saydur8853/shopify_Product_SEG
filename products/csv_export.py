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


def queryset_to_shopify_csv_response(*, queryset, filename_prefix: str = "shopify_products") -> HttpResponse:
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

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.csv"

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(headers)
    for obj in queryset.iterator():
        row = []
        for header in headers:
            field_name = field_by_column.get(header)
            value = getattr(obj, field_name) if field_name else ""
            row.append(_coerce_value(value))
        writer.writerow(row)

    return response
