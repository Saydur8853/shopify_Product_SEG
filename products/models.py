from django.db import models
from django.utils.text import slugify


class Vendor(models.Model):
    name = models.CharField(max_length=255, unique=True, db_index=True)

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class ProductUploadRow(models.Model):
    uploaded_at = models.DateTimeField("Upload time", auto_now_add=True, null=True, blank=True, db_index=True)

    title = models.TextField(verbose_name='Title', db_column='Title', null=True, blank=True)
    url_handle = models.CharField(verbose_name='URL handle', db_column='URL handle', max_length=255, null=True, blank=True)
    description = models.TextField(verbose_name='Description', db_column='Description', null=True, blank=True)
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="product_rows",
        db_column="Vendor",
        verbose_name="Vendor",
    )
    product_category = models.TextField(verbose_name='Product category', db_column='Product category', null=True, blank=True)
    type = models.TextField(verbose_name='Type', db_column='Type', null=True, blank=True)
    tags = models.TextField(verbose_name='Tags', db_column='Tags', null=True, blank=True)
    published_on_online_store = models.TextField(verbose_name='Published on online store', db_column='Published on online store', null=True, blank=True)
    status = models.TextField(verbose_name='Status', db_column='Status', null=True, blank=True)
    sku = models.CharField(verbose_name='SKU', db_column='SKU', max_length=255, null=True, blank=True, unique=True, db_index=True)
    barcode = models.TextField(verbose_name='Barcode', db_column='Barcode', null=True, blank=True)
    option1_name = models.TextField(verbose_name='Option1 name', db_column='Option1 name', null=True, blank=True)
    option1_value = models.TextField(verbose_name='Option1 value', db_column='Option1 value', null=True, blank=True)
    option2_name = models.TextField(verbose_name='Option2 name', db_column='Option2 name', null=True, blank=True)
    option2_value = models.TextField(verbose_name='Option2 value', db_column='Option2 value', null=True, blank=True)
    option3_name = models.TextField(verbose_name='Option3 name', db_column='Option3 name', null=True, blank=True)
    option3_value = models.TextField(verbose_name='Option3 value', db_column='Option3 value', null=True, blank=True)
    price = models.TextField(verbose_name='Price', db_column='Price', null=True, blank=True)
    price_international = models.TextField(verbose_name='Price / International', db_column='Price / International', null=True, blank=True)
    compare_at_price = models.TextField(verbose_name='Compare-at price', db_column='Compare-at price', null=True, blank=True)
    compare_at_price_international = models.TextField(verbose_name='Compare-at price / International', db_column='Compare-at price / International', null=True, blank=True)
    cost_per_item = models.TextField(verbose_name='Cost per item', db_column='Cost per item', null=True, blank=True)
    charge_tax = models.TextField(verbose_name='Charge tax', db_column='Charge tax', null=True, blank=True)
    tax_code = models.TextField(verbose_name='Tax code', db_column='Tax code', null=True, blank=True)
    unit_price_total_measure = models.TextField(verbose_name='Unit price total measure', db_column='Unit price total measure', null=True, blank=True)
    unit_price_total_measure_unit = models.TextField(verbose_name='Unit price total measure unit', db_column='Unit price total measure unit', null=True, blank=True)
    unit_price_base_measure = models.TextField(verbose_name='Unit price base measure', db_column='Unit price base measure', null=True, blank=True)
    unit_price_base_measure_unit = models.TextField(verbose_name='Unit price base measure unit', db_column='Unit price base measure unit', null=True, blank=True)
    inventory_tracker = models.TextField(verbose_name='Inventory tracker', db_column='Inventory tracker', null=True, blank=True)
    inventory_quantity = models.TextField(verbose_name='Inventory quantity', db_column='Inventory quantity', null=True, blank=True)
    continue_selling_when_out_of_stock = models.TextField(verbose_name='Continue selling when out of stock', db_column='Continue selling when out of stock', null=True, blank=True)
    weight_value_grams = models.TextField(verbose_name='Weight value (grams)', db_column='Weight value (grams)', null=True, blank=True)
    weight_unit_for_display = models.TextField(verbose_name='Weight unit for display', db_column='Weight unit for display', null=True, blank=True)
    requires_shipping = models.TextField(verbose_name='Requires shipping', db_column='Requires shipping', null=True, blank=True)
    fulfillment_service = models.TextField(verbose_name='Fulfillment service', db_column='Fulfillment service', null=True, blank=True)
    product_image_url = models.TextField(verbose_name='Product image URL', db_column='Product image URL', null=True, blank=True)
    image_position = models.TextField(verbose_name='Image position', db_column='Image position', null=True, blank=True)
    image_alt_text = models.TextField(verbose_name='Image alt text', db_column='Image alt text', null=True, blank=True)
    variant_image_url = models.TextField(verbose_name='Variant image URL', db_column='Variant image URL', null=True, blank=True)
    gift_card = models.TextField(verbose_name='Gift card', db_column='Gift card', null=True, blank=True)
    seo_title = models.CharField(verbose_name='SEO title', db_column='SEO title', max_length=70, null=True, blank=True)
    seo_description = models.CharField(verbose_name='SEO description', db_column='SEO description', max_length=320, null=True, blank=True)
    google_shopping_google_product_category = models.TextField(verbose_name='Google Shopping / Google product category', db_column='Google Shopping / Google product category', null=True, blank=True)
    google_shopping_gender = models.TextField(verbose_name='Google Shopping / Gender', db_column='Google Shopping / Gender', null=True, blank=True)
    google_shopping_age_group = models.TextField(verbose_name='Google Shopping / Age group', db_column='Google Shopping / Age group', null=True, blank=True)
    google_shopping_mpn = models.TextField(verbose_name='Google Shopping / MPN', db_column='Google Shopping / MPN', null=True, blank=True)
    google_shopping_adwords_grouping = models.TextField(verbose_name='Google Shopping / AdWords Grouping', db_column='Google Shopping / AdWords Grouping', null=True, blank=True)
    google_shopping_adwords_labels = models.TextField(verbose_name='Google Shopping / AdWords labels', db_column='Google Shopping / AdWords labels', null=True, blank=True)
    google_shopping_condition = models.TextField(verbose_name='Google Shopping / Condition', db_column='Google Shopping / Condition', null=True, blank=True)
    google_shopping_custom_product = models.TextField(verbose_name='Google Shopping / Custom product', db_column='Google Shopping / Custom product', null=True, blank=True)
    google_shopping_custom_label_0 = models.TextField(verbose_name='Google Shopping / Custom label 0', db_column='Google Shopping / Custom label 0', null=True, blank=True)
    google_shopping_custom_label_1 = models.TextField(verbose_name='Google Shopping / Custom label 1', db_column='Google Shopping / Custom label 1', null=True, blank=True)
    google_shopping_custom_label_2 = models.TextField(verbose_name='Google Shopping / Custom label 2', db_column='Google Shopping / Custom label 2', null=True, blank=True)
    google_shopping_custom_label_3 = models.TextField(verbose_name='Google Shopping / Custom label 3', db_column='Google Shopping / Custom label 3', null=True, blank=True)
    google_shopping_custom_label_4 = models.TextField(verbose_name='Google Shopping / Custom label 4', db_column='Google Shopping / Custom label 4', null=True, blank=True)

    @staticmethod
    def normalize_title(title: str | None) -> str | None:
        if title is None:
            return None
        cleaned = str(title).strip()
        if not cleaned:
            return None
        head, _separator, _tail = cleaned.partition(",")
        cleaned = head.strip()
        return cleaned or None

    def save(self, *args, **kwargs):
        self.title = self.normalize_title(self.title)
        if (not self.url_handle) and self.title:
            self.url_handle = slugify(self.title)[:255]
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    product = models.ForeignKey(
        ProductUploadRow,
        to_field="sku",
        db_column="SKU",
        related_name="images",
        on_delete=models.CASCADE,
    )
    product_image_url = models.TextField(verbose_name="Product image URL", db_column="Product image URL", null=True, blank=True)
    variant_image_url = models.TextField(verbose_name="Variant image URL", db_column="Variant image URL", null=True, blank=True)
    image_position = models.PositiveIntegerField(verbose_name="Image position", db_column="Image position", null=True, blank=True)
    image_alt_text = models.TextField(verbose_name="Image alt text", db_column="Image alt text", null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["product", "image_position"]),
        ]
