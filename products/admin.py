from django.contrib import admin, messages
from django import forms
from django.core.exceptions import PermissionDenied
from django.db import models as dj_models
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.urls import path

from .models import ProductUploadRow, Vendor
from .csv_export import queryset_to_shopify_csv_response
from .excel_import import import_csv_to_model, import_xlsx_to_model, import_xls_to_model
from .xlsx_export import queryset_to_shopify_xlsx_response

try:
    import openpyxl
except Exception:  # pragma: no cover
    openpyxl = None

# Customize admin branding
admin.site.site_header = "GOODDEGG Administration"
admin.site.site_title = "GOODDEGG Admin"
admin.site.index_title = "GOODDEGG"

class ProductUploadRowAdminForm(forms.ModelForm):
    class Meta:
        model = ProductUploadRow
        fields = "__all__"
        help_texts = {
            "title": "Product title shown on storefront.",
            "url_handle": "Shopify handle (URL-friendly). Leave blank to let Shopify generate.",
            "tags": "Comma-separated tags.",
            "published_on_online_store": "TRUE/FALSE to publish on Online Store channel.",
            "status": "Typically: active, draft, archived.",
            "sku": "Variant SKU (unique per variant).",
            "barcode": "UPC/EAN/ISBN/GTIN.",
            "price": "Price for this variant (e.g. 19.99).",
            "compare_at_price": "Optional original price to show a sale.",
            "inventory_quantity": "Available inventory quantity.",
            "continue_selling_when_out_of_stock": "TRUE/FALSE.",
            "weight_value_grams": "Weight in grams (number).",
            "requires_shipping": "TRUE/FALSE.",
            "product_image_url": "Full image URL (https://...).",
            "variant_image_url": "Variant image URL (optional).",
            "seo_title": "Max 70 characters (recommended).",
            "seo_description": "Max 320 characters (recommended).",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, form_field in self.fields.items():
            model_field = self._meta.model._meta.get_field(field_name)
            csv_column = getattr(model_field, "db_column", None) or str(model_field.verbose_name)
            existing = form_field.help_text or ""
            suffix = f"CSV column: {csv_column}"
            form_field.help_text = f"{existing} ({suffix})" if existing else suffix

            if isinstance(form_field.widget, forms.Textarea):
                form_field.widget.attrs.setdefault("rows", 1)
                form_field.widget.attrs.setdefault("cols", 40)
                form_field.widget.attrs.setdefault("style", "resize: vertical;")


class ProductUploadRowExcelImportForm(forms.Form):
    file = forms.FileField(help_text="Upload a .csv, .xlsx, or .xls file with headers matching the Shopify CSV columns.")
    sheet_name = forms.CharField(
        required=False,
        help_text="Optional: Excel sheet name. Leave blank to use the first sheet.",
    )

    def clean_file(self):
        f = self.cleaned_data["file"]
        name = (getattr(f, "name", "") or "").lower()
        if name.endswith(".xlsx"):
            if openpyxl is None:
                raise forms.ValidationError("Excel import is not available (openpyxl is not installed).")
            return f
        if name.endswith(".xls"):
            try:
                import xlrd  # noqa: F401
            except Exception:
                raise forms.ValidationError("XLS import is not available (xlrd is not installed).")
            return f
        if name.endswith(".csv"):
            return f
        raise forms.ValidationError("Please upload a .csv, .xlsx, or .xls file.")
        return f


@admin.register(ProductUploadRow)
class ProductUploadRowAdmin(admin.ModelAdmin):
    form = ProductUploadRowAdminForm
    formfield_overrides = {
        dj_models.TextField: {"widget": forms.Textarea(attrs={"rows": 1, "cols": 40, "style": "resize: vertical;"})},
    }
    readonly_fields = ("uploaded_at",)
    prepopulated_fields = {"url_handle": ("title",)}
    list_display = (
        "id",
        "uploaded_at",
        "title",
        "vendor",
        "status",
        "sku",
        "price",
        "inventory_quantity",
    )
    search_fields = ("title", "sku", "barcode", "vendor__name", "tags", "url_handle")
    list_filter = (
        ("uploaded_at", admin.DateFieldListFilter),
        "status",
        "vendor",
        "published_on_online_store",
        "requires_shipping",
    )
    date_hierarchy = "uploaded_at"
    ordering = ("-id",)
    actions = ("export_selected_to_shopify_csv",)
    fieldsets = (
        ("Identifiers", {"fields": ("sku", "barcode")}),
        ("Upload metadata", {"fields": ("uploaded_at",)}),
        (
            "Core product info",
            {
                "fields": (
                    "title",
                    "url_handle",
                    "description",
                    "vendor",
                    "product_category",
                    "type",
                    "tags",
                    "published_on_online_store",
                    "status",
                )
            },
        ),
        (
            "Variant options",
            {
                "fields": (
                    "option1_name",
                    "option1_value",
                    "option2_name",
                    "option2_value",
                    "option3_name",
                    "option3_value",
                )
            },
        ),
        (
            "Pricing and tax",
            {
                "fields": (
                    "price",
                    "price_international",
                    "compare_at_price",
                    "compare_at_price_international",
                    "cost_per_item",
                    "charge_tax",
                    "tax_code",
                )
            },
        ),
        (
            "Unit price measures",
            {
                "fields": (
                    "unit_price_total_measure",
                    "unit_price_total_measure_unit",
                    "unit_price_base_measure",
                    "unit_price_base_measure_unit",
                )
            },
        ),
        ("Inventory", {"fields": ("inventory_tracker", "inventory_quantity", "continue_selling_when_out_of_stock")}),
        ("Shipping", {"fields": ("weight_value_grams", "weight_unit_for_display", "requires_shipping", "fulfillment_service")}),
        ("Images", {"fields": ("product_image_url", "image_position", "image_alt_text", "variant_image_url")}),
        ("Product type flags", {"fields": ("gift_card",)}),
        ("SEO", {"fields": ("seo_title", "seo_description")}),
        (
            "Google Shopping",
            {
                "fields": (
                    "google_shopping_google_product_category",
                    "google_shopping_gender",
                    "google_shopping_age_group",
                    "google_shopping_mpn",
                    "google_shopping_adwords_grouping",
                    "google_shopping_adwords_labels",
                    "google_shopping_condition",
                    "google_shopping_custom_product",
                    "google_shopping_custom_label_0",
                    "google_shopping_custom_label_1",
                    "google_shopping_custom_label_2",
                    "google_shopping_custom_label_3",
                    "google_shopping_custom_label_4",
                )
            },
        ),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "import-excel/",
                self.admin_site.admin_view(self.import_excel_view),
                name="products_productuploadrow_import_excel",
            ),
            path(
                "export/",
                self.admin_site.admin_view(self.export_view),
                name="products_productuploadrow_export",
            ),
            path(
                "delete-all/",
                self.admin_site.admin_view(self.delete_all_view),
                name="products_productuploadrow_delete_all",
            ),
        ]
        return custom_urls + urls

    def _delete_all_in_chunks(self, *, chunk_size: int) -> tuple[int, int]:
        chunk_size = max(1, int(chunk_size))
        deleted_rows = 0
        batches = 0
        cursor = 0
        model = self.model

        while True:
            last_pk = (
                model.objects.filter(pk__gt=cursor)
                .order_by("pk")
                .values_list("pk", flat=True)[chunk_size - 1 : chunk_size]
                .first()
            )
            if last_pk is None:
                remaining = model.objects.filter(pk__gt=cursor).count()
                if remaining:
                    model.objects.filter(pk__gt=cursor).delete()
                    deleted_rows += remaining
                    batches += 1
                break

            batch_qs = model.objects.filter(pk__gt=cursor, pk__lte=last_pk)
            batch_count = batch_qs.count()
            batch_qs.delete()
            deleted_rows += batch_count
            batches += 1
            cursor = last_pk

        return deleted_rows, batches

    def import_excel_view(self, request: HttpRequest):
        if request.method == "POST":
            form = ProductUploadRowExcelImportForm(request.POST, request.FILES)
            if form.is_valid():
                uploaded_file = form.cleaned_data["file"]
                name = (getattr(uploaded_file, "name", "") or "").lower()
                if name.endswith(".csv"):
                    count = import_csv_to_model(model=ProductUploadRow, file=uploaded_file)
                elif name.endswith(".xlsx"):
                    workbook = openpyxl.load_workbook(uploaded_file, read_only=True, data_only=True)
                    count = import_xlsx_to_model(
                        model=ProductUploadRow,
                        workbook=workbook,
                        sheet_name=form.cleaned_data.get("sheet_name") or None,
                    )
                else:
                    count = import_xls_to_model(
                        model=ProductUploadRow,
                        file=uploaded_file,
                        sheet_name=form.cleaned_data.get("sheet_name") or None,
                    )
                self.message_user(request, f"Imported {count} rows.", level=messages.SUCCESS)
                return redirect("..")
        else:
            form = ProductUploadRowExcelImportForm()

        context = dict(
            self.admin_site.each_context(request),
            form=form,
            opts=self.model._meta,
            title="Import ProductUploadRow from Excel",
        )
        return render(request, "admin/products/productuploadrow/import_excel.html", context)

    def export_view(self, request: HttpRequest):
        if not self.has_view_permission(request):
            raise PermissionDenied

        fmt = (request.GET.get("format") or "").strip().lower()
        preserved = request.GET.copy()
        preserved.pop("format", None)

        original_get = request.GET
        request.GET = preserved
        try:
            changelist = self.get_changelist_instance(request)
            queryset = changelist.get_queryset(request)
        finally:
            request.GET = original_get

        if fmt in {"csv", "xlsx"}:
            filename_prefix = "product_upload_rows"
            if fmt == "csv":
                return queryset_to_shopify_csv_response(queryset=queryset, filename_prefix=filename_prefix)
            try:
                return queryset_to_shopify_xlsx_response(queryset=queryset, filename_prefix=filename_prefix)
            except RuntimeError as exc:
                self.message_user(request, str(exc), level=messages.ERROR)
                return redirect(request.path + (f"?{preserved.urlencode()}" if preserved else ""))

        context = dict(
            self.admin_site.each_context(request),
            opts=self.model._meta,
            title="Export ProductUploadRow",
            total=queryset.count(),
            preserved_filters=preserved.urlencode(),
        )
        return render(request, "admin/products/productuploadrow/export.html", context)

    def delete_all_view(self, request: HttpRequest):
        if not self.has_delete_permission(request):
            raise PermissionDenied

        total = self.model.objects.count()
        default_chunk_size = 500

        if request.method == "POST":
            try:
                chunk_size = int(request.POST.get("chunk_size") or default_chunk_size)
            except ValueError:
                chunk_size = default_chunk_size

            deleted_rows, batches = self._delete_all_in_chunks(chunk_size=chunk_size)
            self.message_user(
                request,
                f"Deleted {deleted_rows} rows in {batches} batches.",
                level=messages.SUCCESS,
            )
            return redirect("..")

        context = dict(
            self.admin_site.each_context(request),
            opts=self.model._meta,
            title="Delete all ProductUploadRow rows",
            total=total,
            chunk_size=default_chunk_size,
        )
        return render(request, "admin/products/productuploadrow/delete_all.html", context)

    @admin.action(description="Export selected rows to Shopify CSV")
    def export_selected_to_shopify_csv(self, request: HttpRequest, queryset):
        return queryset_to_shopify_csv_response(queryset=queryset)


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    ordering = ("name",)
