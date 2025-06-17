from django import forms
from .models import (
    Case, Client, EquipmentModel, SparePart, Brand, Region,
    MalfunctionType, Supplier, StorageLocation, EquipmentInstance, SalesPerson
)
# We might need User model if we are creating SalesPerson through a combined form
# from django.contrib.auth.models import User

class CaseRegistrationForm(forms.ModelForm):
    # Custom fields for searching/selecting client and equipment if needed
    # For example, a CharField for client search that doesn't map directly to a model field
    # client_search = forms.CharField(required=False, help_text="Search for existing client")
    # equipment_serial_search = forms.CharField(required=False, help_text="Search for existing equipment by serial number")

    class Meta:
        model = Case
        fields = [
            'case_no', 'client', 'status',
            'contact_person_override', 'contact_phone_override',
            'sales_in_charge', 'ward_clinic_department', 'reference_case_no',
            # Dates like registration_date are auto_now_add, others might be set programmatically
        ]
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            # Add more widgets if necessary
        }

    # Additional fields for equipment to be added to the case will likely be handled
    # by a formset or separate logic in the view, as a case can have multiple items.
    # For now, this form focuses on the main Case details.

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

# Consider a form for SalesPerson if it's not solely managed via Django Admin
# This might involve creating/linking a User and a SalesPerson profile.
class SalesPersonForm(forms.ModelForm):
    # If you want to create the User as well:
    # username = forms.CharField(max_length=150)
    # password = forms.CharField(widget=forms.PasswordInput)
    # email = forms.EmailField(required=False)
    # first_name = forms.CharField(max_length=30, required=False)
    # last_name = forms.CharField(max_length=150, required=False)

    class Meta:
        model = SalesPerson
        fields = ['user', 'phone_extension', 'region'] # 'user' would be a ModelChoiceField

    # def save(self, commit=True):
    #     # Custom save logic if creating User and SalesPerson together
    #     # user = User.objects.create_user(
    #     #     username=self.cleaned_data['username'],
    #     #     password=self.cleaned_data['password'],
    #     #     email=self.cleaned_data.get('email'),
    #     #     first_name=self.cleaned_data.get('first_name'),
    #     #     last_name=self.cleaned_data.get('last_name')
    #     # )
    #     # sales_person = super().save(commit=False)
    #     # sales_person.user = user
    #     # if commit:
    #     #     sales_person.save()
    #     # return sales_person
