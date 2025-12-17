from django.test import TestCase

from .excel_import import build_objects_from_rows
from .models import ProductUploadRow, Vendor
from .csv_export import queryset_to_shopify_csv_response
from .xlsx_export import queryset_to_shopify_xlsx_response

from io import BytesIO

try:
    import openpyxl
except Exception:  # pragma: no cover
    openpyxl = None


class TitleNormalizationTests(TestCase):
    def test_import_strips_title_after_comma_and_generates_handle(self):
        headers = ["Title", "URL handle"]
        rows = [["STAVROS Chest, Gray", None]]
        objects = build_objects_from_rows(model=ProductUploadRow, headers=headers, rows=rows)
        self.assertEqual(objects[0].title, "STAVROS Chest")
        self.assertEqual(objects[0].url_handle, "stavros-chest")

    def test_import_handles_whitespace_around_comma(self):
        headers = ["Title"]
        rows = [["  STAVROS Chest  ,   Gray  "]]
        objects = build_objects_from_rows(model=ProductUploadRow, headers=headers, rows=rows)
        self.assertEqual(objects[0].title, "STAVROS Chest")
        self.assertEqual(objects[0].url_handle, "stavros-chest")

    def test_model_save_strips_title_after_comma(self):
        obj = ProductUploadRow.objects.create(title="STAVROS Chest, Gray")
        obj.refresh_from_db()
        self.assertEqual(obj.title, "STAVROS Chest")


class ExportTests(TestCase):
    def test_csv_export_includes_headers_and_values(self):
        vendor = Vendor.objects.create(name="Acme")
        ProductUploadRow.objects.create(title="STAVROS Chest, Gray", vendor=vendor)
        response = queryset_to_shopify_csv_response(queryset=ProductUploadRow.objects.all())
        content = response.content.decode("utf-8")
        self.assertIn("Title", content.splitlines()[0])
        self.assertIn("STAVROS Chest", content)
        self.assertIn("Acme", content)

    def test_xlsx_export_includes_headers_and_values(self):
        if openpyxl is None:  # pragma: no cover
            self.skipTest("openpyxl not installed")

        vendor = Vendor.objects.create(name="Acme")
        ProductUploadRow.objects.create(title="STAVROS Chest, Gray", vendor=vendor)
        response = queryset_to_shopify_xlsx_response(queryset=ProductUploadRow.objects.all())

        workbook = openpyxl.load_workbook(BytesIO(response.content))
        sheet = workbook["Products"]
        self.assertEqual(sheet["A1"].value, "Title")
        self.assertEqual(sheet["A2"].value, "STAVROS Chest")
