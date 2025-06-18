from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError


class Region(models.Model):
    name = models.CharField(max_length=255)
    def __str__(self): return self.name

class Client(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    def __str__(self): return self.name

class Brand(models.Model):
    name = models.CharField(max_length=255, unique=True)
    def __str__(self): return self.name

class EquipmentModel(models.Model):
    name = models.CharField(max_length=255)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    def __str__(self): return f"{self.brand} - {self.name}"

class EquipmentInstance(models.Model):
    serial_no = models.CharField(max_length=255, unique=True)
    model = models.ForeignKey(EquipmentModel, on_delete=models.CASCADE)
    current_client = models.ForeignKey(Client, null=True, blank=True, on_delete=models.SET_NULL, related_name='equipment_instances')
    purchase_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    def __str__(self): return f"{self.model} ({self.serial_no})"

class SalesPerson(models.Model):
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    phone_extension = models.CharField(max_length=50, blank=True, null=True)
    region = models.ForeignKey(Region, null=True, blank=True, on_delete=models.SET_NULL)
    def __str__(self): return self.user.username

class CaseStatus(models.TextChoices):
    NEW = 'NEW', 'New Registration'
    RECEIVING = 'RECEIVING', 'Receiving Equipment'
    AWAITING_QUOTATION = 'AWAITING_QUOTATION', 'Awaiting Quotation Creation'
    QUOTATION_SUBMITTED = 'QUOTATION_SUBMITTED', 'Quotation Submitted to Client'
    QUOTATION_APPROVED = 'QUOTATION_APPROVED', 'Quotation Approved (Pending Repair)'
    QUOTATION_REJECTED = 'QUOTATION_REJECTED', 'Quotation Rejected by Client'
    REPAIR_IN_PROGRESS = 'REPAIR_IN_PROGRESS', 'Repair in Progress'
    REPAIR_COMPLETED = 'REPAIR_COMPLETED', 'Repair Completed (Pending QC)'
    QC_PASSED = 'QC_PASSED', 'QC Passed (Pending Delivery)'
    QC_FAILED = 'QC_FAILED', 'QC Failed (Requires Rework)'
    # New/Updated Delivery & Closing Statuses
    DELIVERED_PENDING_CLOSING = 'DELIVERED_PENDING_CLOSING', 'Delivered to Client (Pending Closing)' # New
    # DELIVERY = 'DELIVERY', 'Pending Delivery/Collection' # Removed
    CLOSED = 'CLOSED', 'Case Closed' # Existing, suitable as final state

class Case(models.Model):
    case_no = models.CharField(max_length=255, unique=True, help_text="Case Number")
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    status = models.CharField(max_length=30, choices=CaseStatus.choices, default=CaseStatus.NEW)
    registration_date = models.DateTimeField(auto_now_add=True)
    received_date = models.DateTimeField(null=True, blank=True)
    quotation_date = models.DateTimeField(null=True, blank=True)
    repair_start_date = models.DateTimeField(null=True, blank=True)
    # qc_date field was already present from a previous step, ensuring it's correctly placed and defined.
    qc_date = models.DateTimeField(null=True, blank=True, help_text="Date when QC was performed")
    delivery_date = models.DateTimeField(null=True, blank=True)
    closed_date = models.DateTimeField(null=True, blank=True)
    contact_person_override = models.CharField(max_length=255, blank=True, null=True)
    contact_phone_override = models.CharField(max_length=50, blank=True, null=True)
    sales_in_charge = models.ForeignKey(SalesPerson, null=True, blank=True, on_delete=models.SET_NULL)
    ward_clinic_department = models.CharField(max_length=255, blank=True, null=True)
    reference_case_no = models.CharField(max_length=255, blank=True, null=True)
    qc_notes = models.TextField(blank=True, null=True, help_text="Notes from the Quality Control process")

    # New Delivery & Closing Notes fields
    delivery_notes = models.TextField(blank=True, null=True, help_text="Notes related to the delivery process")
    closing_notes = models.TextField(blank=True, null=True, help_text="Final notes upon closing the case")

    def __str__(self): return self.case_no

class MalfunctionType(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    def __str__(self): return self.name

class CaseItem(models.Model):
    case = models.ForeignKey(Case, related_name='items', on_delete=models.CASCADE)
    equipment_instance = models.ForeignKey(EquipmentInstance, on_delete=models.CASCADE)
    malfunction_description = models.TextField()
    malfunction_type = models.ForeignKey(MalfunctionType, null=True, blank=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True, null=True)
    def __str__(self): return f"Item for {self.case.case_no} - {self.equipment_instance.serial_no}"

class SparePart(models.Model):
    part_no = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    brand = models.ForeignKey(Brand, null=True, blank=True, on_delete=models.SET_NULL)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.part_no}) - Stock: {self.stock_quantity}"

    def decrease_stock(self, quantity_to_decrease):
        if not isinstance(quantity_to_decrease, int) or quantity_to_decrease <= 0:
            raise ValueError("Quantity to decrease must be a positive integer.")
        if self.stock_quantity < quantity_to_decrease:
            raise ValidationError(f"Not enough stock for {self.name} (Part No: {self.part_no}). Available: {self.stock_quantity}, Requested: {quantity_to_decrease}")
        self.stock_quantity -= quantity_to_decrease
        self.save(update_fields=['stock_quantity'])

    def increase_stock(self, quantity_to_increase):
        if not isinstance(quantity_to_increase, int) or quantity_to_increase <= 0:
            raise ValueError("Quantity to increase must be a positive integer.")
        self.stock_quantity += quantity_to_increase
        self.save(update_fields=['stock_quantity'])

class CaseSparePartUsage(models.Model):
    case_item = models.ForeignKey(CaseItem, related_name='spare_parts_used', on_delete=models.CASCADE)
    spare_part = models.ForeignKey(SparePart, on_delete=models.PROTECT)
    quantity_used = models.PositiveIntegerField(default=1)
    unit_price_at_usage = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price at the time of usage")

    def __str__(self):
        return f"{self.quantity_used} x {self.spare_part.name} for {self.case_item}"

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.pk is None:
                old_quantity = 0
                original_spare_part = None
            else:
                try:
                    original_instance = CaseSparePartUsage.objects.get(pk=self.pk)
                    old_quantity = original_instance.quantity_used
                    original_spare_part = original_instance.spare_part
                except CaseSparePartUsage.DoesNotExist:
                    old_quantity = 0
                    original_spare_part = None

            super().save(*args, **kwargs)

            if original_spare_part and original_spare_part.id != self.spare_part.id:
                original_spare_part.increase_stock(old_quantity)
                self.spare_part.decrease_stock(self.quantity_used)
            else:
                quantity_difference = self.quantity_used - old_quantity
                if quantity_difference > 0:
                    self.spare_part.decrease_stock(quantity_difference)
                elif quantity_difference < 0:
                    self.spare_part.increase_stock(abs(quantity_difference))

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            part_to_return_stock = self.spare_part
            quantity_to_return = self.quantity_used
            super().delete(*args, **kwargs)
            if part_to_return_stock and quantity_to_return > 0:
                part_to_return_stock.increase_stock(quantity_to_return)


class Supplier(models.Model):
    name = models.CharField(max_length=255, unique=True)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    def __str__(self): return self.name

class StorageLocation(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    def __str__(self): return self.name

class Quotation(models.Model):
    QUOTATION_STATUS_CHOICES = [
        ('DRAFT', 'Draft'), ('SUBMITTED', 'Submitted'), ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'), ('EXPIRED', 'Expired'),
    ]
    case = models.OneToOneField(Case, on_delete=models.CASCADE, related_name='quotation')
    quotation_no = models.CharField(max_length=50, unique=True)
    created_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=QUOTATION_STATUS_CHOICES, default='DRAFT')
    notes = models.TextField(blank=True, null=True)
    def __str__(self): return f"Quotation {self.quotation_no} for Case {self.case.case_no}"
    def calculate_total_amount(self):
        total = sum(item.total_price for item in self.lineitems.all() if item.total_price is not None)
        self.total_amount = total; return total
    class Meta: ordering = ['-created_date']

class QuotationLineItem(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='lineitems')
    spare_part = models.ForeignKey(SparePart, null=True, blank=True, on_delete=models.SET_NULL)
    description = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    def save(self, *args, **kwargs):
        if not self.description and self.spare_part: self.description = self.spare_part.name
        calc_quantity = self.quantity if self.quantity is not None else 0
        calc_unit_price = self.unit_price if self.unit_price is not None else 0
        self.total_price = calc_quantity * calc_unit_price
        super().save(*args, **kwargs)
        current_total = self.quotation.calculate_total_amount()
        if self.quotation.total_amount != current_total:
            self.quotation.total_amount = current_total
            self.quotation.save(update_fields=['total_amount'])
    def __str__(self): return f"{self.description} (Qty: {self.quantity}) for Quotation {self.quotation.quotation_no}"
