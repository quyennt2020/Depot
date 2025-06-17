from django.db import models
from django.contrib.auth.models import User

class Region(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Client(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class EquipmentModel(models.Model):
    name = models.CharField(max_length=255)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.brand} - {self.name}"

class EquipmentInstance(models.Model):
    serial_no = models.CharField(max_length=255, unique=True)
    model = models.ForeignKey(EquipmentModel, on_delete=models.CASCADE)
    current_client = models.ForeignKey(Client, null=True, blank=True, on_delete=models.SET_NULL, related_name='equipment_instances')
    purchase_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.model} ({self.serial_no})"

class SalesPerson(models.Model):
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    phone_extension = models.CharField(max_length=50, blank=True, null=True)
    region = models.ForeignKey(Region, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.user.username

class CaseStatus(models.TextChoices):
    NEW = 'NEW', 'New Registration'
    RECEIVING = 'RECEIVING', 'Receiving'
    QUOTATION = 'QUOTATION', 'Waiting for Quotation'
    REPAIRING = 'REPAIRING', 'Repairing'
    QC = 'QC', 'QC'
    DELIVERY = 'DELIVERY', 'Delivery'
    CLOSED = 'CLOSED', 'Follow-up & Closing Case'

class Case(models.Model):
    case_no = models.CharField(max_length=255, unique=True, help_text="Case Number, can be auto-generated or manually input")
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=CaseStatus.choices)
    registration_date = models.DateTimeField(auto_now_add=True)
    received_date = models.DateTimeField(null=True, blank=True)
    quotation_date = models.DateTimeField(null=True, blank=True)
    repair_start_date = models.DateTimeField(null=True, blank=True)
    qc_date = models.DateTimeField(null=True, blank=True)
    delivery_date = models.DateTimeField(null=True, blank=True)
    closed_date = models.DateTimeField(null=True, blank=True)
    contact_person_override = models.CharField(max_length=255, blank=True, null=True, help_text="Override client's default contact")
    contact_phone_override = models.CharField(max_length=50, blank=True, null=True, help_text="Override client's default phone")
    sales_in_charge = models.ForeignKey(SalesPerson, null=True, blank=True, on_delete=models.SET_NULL)
    ward_clinic_department = models.CharField(max_length=255, blank=True, null=True)
    reference_case_no = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.case_no

class MalfunctionType(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class CaseItem(models.Model):
    case = models.ForeignKey(Case, related_name='items', on_delete=models.CASCADE)
    equipment_instance = models.ForeignKey(EquipmentInstance, on_delete=models.CASCADE)
    malfunction_description = models.TextField()
    malfunction_type = models.ForeignKey(MalfunctionType, null=True, blank=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Item for {self.case.case_no} - {self.equipment_instance.serial_no}"

class SparePart(models.Model):
    part_no = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    brand = models.ForeignKey(Brand, null=True, blank=True, on_delete=models.SET_NULL)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.part_no})"

class CaseSparePartUsage(models.Model):
    case_item = models.ForeignKey(CaseItem, related_name='spare_parts_used', on_delete=models.CASCADE)
    spare_part = models.ForeignKey(SparePart, on_delete=models.CASCADE)
    quantity_used = models.PositiveIntegerField(default=1)
    unit_price_at_usage = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price at the time of usage for historical accuracy")

    def __str__(self):
        return f"{self.quantity_used} x {self.spare_part.name} for {self.case_item}"

class Supplier(models.Model):
    name = models.CharField(max_length=255, unique=True)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name

class StorageLocation(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
