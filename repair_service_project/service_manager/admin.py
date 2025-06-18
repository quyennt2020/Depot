from django.contrib import admin
from django.utils.html import format_html # For creating links in admin
from django.urls import reverse # For creating links in admin
from .models import (
    Region, Client, Brand, EquipmentModel, EquipmentInstance,
    Case, CaseItem, SparePart, MalfunctionType, SalesPerson,
    Supplier, StorageLocation, CaseSparePartUsage,
    Quotation, QuotationLineItem
)

# Inline Admin definitions
class CaseItemInline(admin.TabularInline):
    model = CaseItem
    fields = ('equipment_instance', 'malfunction_description', 'malfunction_type', 'notes')
    extra = 1
    autocomplete_fields = ['equipment_instance']

class EquipmentInstanceInlineForClient(admin.TabularInline):
    model = EquipmentInstance
    fk_name = 'current_client'
    extra = 0
    readonly_fields = ('serial_no', 'model', 'purchase_date', 'notes')
    can_delete = False

class EquipmentInstanceInlineForModel(admin.TabularInline):
    model = EquipmentInstance
    fk_name = 'model'
    extra = 0
    readonly_fields = ('serial_no', 'current_client', 'purchase_date', 'notes')
    can_delete = False

class QuotationLineItemInline(admin.TabularInline):
    model = QuotationLineItem
    fields = ('spare_part', 'description', 'quantity', 'unit_price', 'total_price')
    readonly_fields = ('total_price',)
    extra = 1
    autocomplete_fields = ['spare_part']

# Custom ModelAdmin definitions
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'contact_person', 'phone')
    search_fields = ('name', 'contact_person')
    list_filter = ('region',)
    inlines = [EquipmentInstanceInlineForClient]

class BrandAdmin(admin.ModelAdmin):
    list_display = ('name',)

class EquipmentModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'description')
    search_fields = ('name', 'brand__name')
    list_filter = ('brand',)
    inlines = [EquipmentInstanceInlineForModel]

class EquipmentInstanceAdmin(admin.ModelAdmin):
    list_display = ('serial_no', 'model', 'current_client', 'purchase_date')
    search_fields = ('serial_no', 'model__name', 'model__brand__name', 'current_client__name')
    list_filter = ('model__brand', 'model', 'purchase_date')

class CaseAdmin(admin.ModelAdmin):
    list_display = ('case_no', 'client', 'status', 'registration_date', 'qc_date',
                    'delivery_date', 'closed_date', 'sales_in_charge') # Added delivery_date, closed_date
    search_fields = ('case_no', 'client__name', 'items__equipment_instance__serial_no')
    list_filter = ('status', 'client__region', 'registration_date', 'qc_date',
                   'delivery_date', 'closed_date') # Added delivery_date, closed_date
    inlines = [CaseItemInline]

    readonly_fields = ('registration_date', 'received_date', 'quotation_date',
                       'repair_start_date', 'qc_date', 'delivery_date', 'closed_date')

    fieldsets = (
        ('Case Core Information', {
            'fields': ('case_no', 'client', 'status', 'sales_in_charge')
        }),
        ('Contact Overrides', {
            'classes': ('collapse',),
            'fields': ('contact_person_override', 'contact_phone_override')
        }),
        ('Location & Reference', {
            'fields': ('ward_clinic_department', 'reference_case_no')
        }),
        ('Quality Control Information', {
            'classes': ('collapse',),
            'fields': ('qc_notes',)
        }),
        ('Delivery & Closing Information', { # New fieldset
            'classes': ('collapse',),
            'fields': ('delivery_notes', 'closing_notes')
        }),
        ('Case Timestamps & Dates (Read-Only)', {
            'classes': ('collapse',),
            'fields': ('registration_date', 'received_date', 'quotation_date',
                       'repair_start_date', 'qc_date',
                       'delivery_date', 'closed_date')
        }),
    )

class SparePartAdmin(admin.ModelAdmin):
    list_display = ('part_no', 'name', 'brand', 'unit_price', 'stock_quantity')
    search_fields = ('part_no', 'name', 'brand__name')
    list_filter = ('brand',)

class QuotationAdmin(admin.ModelAdmin):
    list_display = ('quotation_no', 'case_link', 'status', 'created_date', 'total_amount')
    list_filter = ('status', 'created_date', 'case__client__region')
    search_fields = ('quotation_no', 'case__case_no', 'case__client__name')
    readonly_fields = ('total_amount', 'created_date')
    inlines = [QuotationLineItemInline]
    fieldsets = (
        (None, {
            'fields': ('quotation_no', 'case', 'status')
        }),
        ('Details & Notes', {
            'fields': ('notes', 'expiry_date')
        }),
        ('Financials (Read-Only)', {
            'fields': ('total_amount', 'created_date')
        }),
    )

    def case_link(self, obj):
        if obj.case:
            link = reverse("admin:service_manager_case_change", args=[obj.case.id])
            return format_html('<a href="{}">{}</a>', link, obj.case.case_no)
        return "N/A"
    case_link.short_description = 'Case'
    case_link.admin_order_field = 'case__case_no'

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('case', 'quotation_no')
        return self.readonly_fields

class CaseItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'case_link', 'equipment_instance_link', 'malfunction_description_short', 'malfunction_type')
    list_select_related = ('case', 'equipment_instance__model__brand', 'malfunction_type')
    search_fields = ('case__case_no', 'equipment_instance__serial_no', 'malfunction_description')
    list_filter = ('malfunction_type', 'case__status')
    raw_id_fields = ('equipment_instance', 'case', 'malfunction_type')

    def case_link(self, obj):
        if obj.case:
            link = reverse("admin:service_manager_case_change", args=[obj.case.id])
            return format_html('<a href="{}">{}</a>', link, obj.case.case_no)
        return "N/A"
    case_link.short_description = 'Case'
    case_link.admin_order_field = 'case__case_no'

    def equipment_instance_link(self, obj):
        if obj.equipment_instance:
            link = reverse("admin:service_manager_equipmentinstance_change", args=[obj.equipment_instance.id])
            return format_html('<a href="{}">{}</a>', link, obj.equipment_instance.serial_no)
        return "N/A"
    equipment_instance_link.short_description = 'Equipment Serial'
    equipment_instance_link.admin_order_field = 'equipment_instance__serial_no'

    def malfunction_description_short(self, obj, max_chars=50):
        if obj.malfunction_description:
            return (obj.malfunction_description[:max_chars] + '...') if len(obj.malfunction_description) > max_chars else obj.malfunction_description
        return "N/A"
    malfunction_description_short.short_description = 'Malfunction (Short)'

class CaseSparePartUsageAdmin(admin.ModelAdmin):
    list_display = ('id', 'case_item_admin_link', 'spare_part_link', 'quantity_used', 'unit_price_at_usage')
    list_select_related = ('case_item__case', 'case_item__equipment_instance__model', 'spare_part__brand')
    search_fields = (
        'case_item__case__case_no',
        'case_item__equipment_instance__serial_no',
        'spare_part__name',
        'spare_part__part_no'
    )
    list_filter = ('spare_part__brand', 'case_item__case__status')
    raw_id_fields = ('case_item', 'spare_part')

    def case_item_admin_link(self, obj):
        if obj.case_item:
            case_item_url = reverse("admin:service_manager_caseitem_change", args=[obj.case_item.id])
            display_text = f"Item for Case {obj.case_item.case.case_no} (Equip: {obj.case_item.equipment_instance.serial_no if obj.case_item.equipment_instance else 'N/A'})"
            return format_html('<a href="{}">{}</a>', case_item_url, display_text)
        return "N/A"
    case_item_admin_link.short_description = 'Case Item Context'
    case_item_admin_link.admin_order_field = 'case_item__case__case_no'

    def spare_part_link(self, obj):
        if obj.spare_part:
            link = reverse("admin:service_manager_sparepart_change", args=[obj.spare_part.id])
            return format_html('<a href="{}">{} ({})</a>', link, obj.spare_part.name, obj.spare_part.part_no)
        return "N/A"
    spare_part_link.short_description = 'Spare Part'
    spare_part_link.admin_order_field = 'spare_part__name'

# Register models with their custom admin classes
admin.site.register(Client, ClientAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(EquipmentModel, EquipmentModelAdmin)
admin.site.register(EquipmentInstance, EquipmentInstanceAdmin)
admin.site.register(Case, CaseAdmin)
admin.site.register(SparePart, SparePartAdmin)
admin.site.register(Quotation, QuotationAdmin)
admin.site.register(CaseItem, CaseItemAdmin)
admin.site.register(CaseSparePartUsage, CaseSparePartUsageAdmin)

# Basic registration for other models
admin.site.register(Region)
admin.site.register(MalfunctionType)
admin.site.register(SalesPerson)
admin.site.register(Supplier)
admin.site.register(StorageLocation)
