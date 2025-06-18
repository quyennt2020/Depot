from django import forms
from django.forms import inlineformset_factory # For managing multiple line items
from .models import (
    Case, Client, EquipmentModel, SparePart, Brand, Region,
    MalfunctionType, Supplier, StorageLocation, EquipmentInstance, SalesPerson,
    Quotation, QuotationLineItem, # Existing models
    CaseItem, CaseSparePartUsage # Added CaseItem for formset parent, CaseSparePartUsage for form
)
# We might need User model if we are creating SalesPerson through a combined form
# from django.contrib.auth.models import User

class CaseRegistrationForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = [
            'case_no', 'client', 'status',
            'contact_person_override', 'contact_phone_override',
            'sales_in_charge', 'ward_clinic_department', 'reference_case_no',
        ]
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'address', 'region', 'contact_person', 'phone']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class EquipmentModelForm(forms.ModelForm):
    class Meta:
        model = EquipmentModel
        fields = ['name', 'brand', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class EquipmentInstanceForm(forms.ModelForm):
    class Meta:
        model = EquipmentInstance
        fields = ['serial_no', 'model', 'current_client', 'purchase_date', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
        }

class SparePartForm(forms.ModelForm):
    class Meta:
        model = SparePart
        fields = ['part_no', 'name', 'brand', 'unit_price', 'stock_quantity']

class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name']

class RegionForm(forms.ModelForm):
    class Meta:
        model = Region
        fields = ['name']

class MalfunctionTypeForm(forms.ModelForm):
    class Meta:
        model = MalfunctionType
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'email', 'phone']

class StorageLocationForm(forms.ModelForm):
    class Meta:
        model = StorageLocation
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class SalesPersonForm(forms.ModelForm):
    class Meta:
        model = SalesPerson
        fields = ['user', 'phone_extension', 'region']


class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = [
            'quotation_no',
            'expiry_date',
            'status',
            'notes',
        ]
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'quotation_no': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class QuotationLineItemForm(forms.ModelForm):
    class Meta:
        model = QuotationLineItem
        fields = ['spare_part', 'description', 'quantity', 'unit_price']
        widgets = {
            'spare_part': forms.Select(attrs={'class': 'form-control spare-part-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control quantity-input', 'min': '1'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control unit-price-input', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.fields.get('spare_part'):
            self.fields['description'].required = False

QuotationLineItemFormSet = inlineformset_factory(
    Quotation,
    QuotationLineItem,
    form=QuotationLineItemForm,
    fields=('spare_part', 'description', 'quantity', 'unit_price'),
    extra=1,
    can_delete=True,
)

# --- New Case Spare Part Usage Forms ---

class CaseSparePartUsageForm(forms.ModelForm):
    class Meta:
        model = CaseSparePartUsage
        fields = ['spare_part', 'quantity_used', 'unit_price_at_usage']
        # 'case_item' will be set programmatically or by the formset context.
        widgets = {
            'spare_part': forms.Select(attrs={'class': 'form-control spare-part-select'}),
            'quantity_used': forms.NumberInput(attrs={'class': 'form-control quantity-input', 'min': '1'}),
            'unit_price_at_usage': forms.NumberInput(attrs={'class': 'form-control unit-price-input', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter spare parts to show only those in stock
        self.fields['spare_part'].queryset = SparePart.objects.filter(stock_quantity__gt=0).order_by('name')

        # Attempt to auto-fill unit_price_at_usage when a spare_part is selected (primarily for new forms)
        # This is a basic implementation. JavaScript would be better for dynamic updates in the browser.
        if 'instance' not in kwargs or not kwargs['instance'].pk : # New form
            if 'initial' in kwargs and 'spare_part' in kwargs['initial']:
                try:
                    spare_part_id = kwargs['initial']['spare_part']
                    selected_part = SparePart.objects.get(id=spare_part_id)
                    self.initial['unit_price_at_usage'] = selected_part.unit_price
                except SparePart.DoesNotExist:
                    pass # Handle case where initial spare_part_id is invalid
            # elif self.data.get('spare_part'): # If form submitted with data (less reliable here)
            #    pass

        elif self.instance and self.instance.spare_part_id and not self.initial.get('unit_price_at_usage'):
             # For existing forms, if unit_price_at_usage wasn't set, default from spare part.
             # However, this field should ideally be set at the time of usage and stored.
             self.initial['unit_price_at_usage'] = self.instance.spare_part.unit_price


CaseSparePartUsageFormSet = inlineformset_factory(
    CaseItem,  # Parent model: Spare parts are used for a specific CaseItem
    CaseSparePartUsage,  # Inline model
    form=CaseSparePartUsageForm,
    fields=('spare_part', 'quantity_used', 'unit_price_at_usage'),
    extra=1,  # Number of empty forms to display
    can_delete=True  # Allow deletion of existing spare part usage records
)
