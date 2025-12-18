from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime
from typing import Any

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify


def _normalize_header(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_cell(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value).strip()


def _normalize_title(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    head, _separator, _tail = cleaned.partition(",")
    cleaned = head.strip()
    return cleaned or None


def _db_column_to_field_name(model) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for field in model._meta.fields:
        if field.primary_key:
            continue
        db_column = getattr(field, "db_column", None)
        if not db_column:
            continue
        mapping[str(db_column)] = field.name
    return mapping


def build_objects_from_rows(
    *,
    model,
    headers: list[str],
    rows: Iterable[list[Any]],
    fk_resolvers: dict[str, Any] | None = None,
):
    db_column_to_field = _db_column_to_field_name(model)
    header_to_field: dict[int, str] = {}
    for idx, header in enumerate(headers):
        field_name = db_column_to_field.get(header)
        if field_name:
            header_to_field[idx] = field_name

    now = timezone.now()
    objects = []
    for row_values in rows:
        data: dict[str, Any] = {}
        for col_idx, field_name in header_to_field.items():
            if col_idx >= len(row_values):
                continue
            value = _normalize_cell(row_values[col_idx])
            if value is not None:
                model_field = model._meta.get_field(field_name)
                if model_field.many_to_one and getattr(model_field, "remote_field", None):
                    resolver = (fk_resolvers or {}).get(field_name)
                    if resolver:
                        resolved = resolver(value)
                        if resolved is not None:
                            data[field_name] = resolved
                    continue
                data[field_name] = value

        title = _normalize_title(data.get("title"))
        if title is not None:
            data["title"] = title
        elif "title" in data:
            data.pop("title", None)

        if not data.get("url_handle") and title:
            data["url_handle"] = slugify(title)[:255]

        if "uploaded_at" in {f.name for f in model._meta.fields} and "uploaded_at" not in data:
            data["uploaded_at"] = now

        objects.append(model(**data))
    return objects


@transaction.atomic
def import_xlsx_to_model(*, model, workbook, sheet_name: str | None = None) -> int:
    if sheet_name:
        sheet = workbook[sheet_name]
    else:
        sheet = workbook.active

    rows_iter = sheet.iter_rows(values_only=True)
    try:
        header_row = next(rows_iter)
    except StopIteration:
        return 0

    headers = [_normalize_header(h) for h in header_row]
    cleaned_rows = [list(r) for r in rows_iter]

    fk_resolvers: dict[str, Any] = {}
    try:
        from .models import Vendor

        def _vendor_resolver(v: Any):
            name = _normalize_cell(v)
            if not name:
                return None
            vendor, _created = Vendor.objects.get_or_create(name=name)
            return vendor

        fk_resolvers["vendor"] = _vendor_resolver
    except Exception:
        fk_resolvers = {}

    objects = build_objects_from_rows(model=model, headers=headers, rows=cleaned_rows, fk_resolvers=fk_resolvers)
    if not objects:
        return 0

    model.objects.bulk_create(objects, batch_size=1000)
    return len(objects)


@transaction.atomic
def import_csv_to_model(*, model, file) -> int:
    import csv

    # `file` is typically an UploadedFile; ensure we read text with BOM support.
    text = file.read().decode("utf-8-sig")
    reader = csv.reader(text.splitlines())

    try:
        headers = next(reader)
    except StopIteration:
        return 0

    headers = [_normalize_header(h) for h in headers]

    fk_resolvers: dict[str, Any] = {}
    try:
        from .models import Vendor

        def _vendor_resolver(v: Any):
            name = _normalize_cell(v)
            if not name:
                return None
            vendor, _created = Vendor.objects.get_or_create(name=name)
            return vendor

        fk_resolvers["vendor"] = _vendor_resolver
    except Exception:
        fk_resolvers = {}

    rows = list(reader)

    objects = build_objects_from_rows(model=model, headers=headers, rows=rows, fk_resolvers=fk_resolvers)
    if not objects:
        return 0

    model.objects.bulk_create(objects, batch_size=1000)
    return len(objects)


@transaction.atomic
def import_xls_to_model(*, model, file, sheet_name: str | None = None) -> int:
    try:
        import xlrd
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("XLS import is not available (xlrd is not installed).") from exc

    workbook = xlrd.open_workbook(file_contents=file.read())

    if sheet_name:
        sheet = workbook.sheet_by_name(sheet_name)
    else:
        sheet = workbook.sheet_by_index(0)

    if sheet.nrows <= 0:
        return 0

    def _row_values(row_idx: int) -> list[Any]:
        values: list[Any] = []
        for col_idx in range(sheet.ncols):
            cell = sheet.cell(row_idx, col_idx)
            value: Any = cell.value
            if cell.ctype == xlrd.XL_CELL_DATE:
                try:
                    value = xlrd.xldate.xldate_as_datetime(cell.value, workbook.datemode)
                except Exception:
                    value = cell.value
            elif cell.ctype == xlrd.XL_CELL_BOOLEAN:
                value = bool(cell.value)
            values.append(value)
        return values

    headers = [_normalize_header(v) for v in _row_values(0)]
    rows = [_row_values(i) for i in range(1, sheet.nrows)]

    fk_resolvers: dict[str, Any] = {}
    try:
        from .models import Vendor

        def _vendor_resolver(v: Any):
            name = _normalize_cell(v)
            if not name:
                return None
            vendor, _created = Vendor.objects.get_or_create(name=name)
            return vendor

        fk_resolvers["vendor"] = _vendor_resolver
    except Exception:
        fk_resolvers = {}

    objects = build_objects_from_rows(model=model, headers=headers, rows=rows, fk_resolvers=fk_resolvers)
    if not objects:
        return 0

    model.objects.bulk_create(objects, batch_size=1000)
    return len(objects)
