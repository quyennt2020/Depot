from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse # Keep for other placeholders
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta # Added timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q

from .forms import (
    CaseRegistrationForm, ClientForm, BrandForm, EquipmentModelForm, EquipmentInstanceForm,
    QuotationForm, QuotationLineItemFormSet, CaseSparePartUsageFormSet, SparePartForm,
    RegionForm, MalfunctionTypeForm, SupplierForm, StorageLocationForm # Added StorageLocationForm
)
from .models import (
    Case, Client, EquipmentInstance, CaseItem, EquipmentModel, Region, Brand,
    Quotation, QuotationLineItem, SparePart, CaseStatus, CaseSparePartUsage,
    MalfunctionType, Supplier, StorageLocation # Added StorageLocation
)

# --- Workplace Views ---
@login_required
@permission_required('service_manager.view_case', raise_exception=True)
def workplace_dashboard(request):
    # Existing: Recent cases list
    recent_cases = Case.objects.all().order_by('-registration_date')[:10]

    # Statistics Calculation
    new_registration_cases_count = Case.objects.filter(status=CaseStatus.NEW).count()

    total_open_cases = Case.objects.exclude(
        Q(status=CaseStatus.CLOSED) | Q(status=CaseStatus.QUOTATION_REJECTED)
    ).count()

    awaiting_quotation_count = Case.objects.filter(status=CaseStatus.AWAITING_QUOTATION).count()
    pending_quotation_approval_count = Case.objects.filter(status=CaseStatus.QUOTATION_SUBMITTED).count()
    ready_for_repair_count = Case.objects.filter(status=CaseStatus.QUOTATION_APPROVED).count()
    repair_in_progress_count = Case.objects.filter(status=CaseStatus.REPAIR_IN_PROGRESS).count()

    qc_queue_count = Case.objects.filter(status=CaseStatus.REPAIR_COMPLETED).count()
    delivery_queue_count = Case.objects.filter(status=CaseStatus.QC_PASSED).count()

    seven_days_ago = timezone.now() - timedelta(days=7)
    recently_closed_cases_count = Case.objects.filter(
        status=CaseStatus.CLOSED,
        closed_date__gte=seven_days_ago
    ).count()

    repair_queue_link_count = ready_for_repair_count + repair_in_progress_count

    context = {
        'recent_cases': recent_cases,

        'new_registration_cases_count': new_registration_cases_count,
        'repair_queue_count': repair_queue_link_count,
        'qc_queue_count': qc_queue_count,
        'delivery_queue_count': delivery_queue_count,

        'total_open_cases': total_open_cases,
        'stat_awaiting_quotation': awaiting_quotation_count,
        'stat_pending_quotation_approval': pending_quotation_approval_count,
        'stat_ready_for_repair': ready_for_repair_count,
        'stat_repair_in_progress': repair_in_progress_count,
        'stat_pending_qc': qc_queue_count,
        'stat_pending_delivery': delivery_queue_count,
        'stat_recently_closed': recently_closed_cases_count,
    }
    return render(request, 'service_manager/workplace_dashboard.html', context)

@login_required
@permission_required('service_manager.add_case', raise_exception=True)
def case_registration(request):
    new_equipment_form = EquipmentInstanceForm(request.POST or None, prefix="new_equip")
    if request.method == 'POST':
        form = CaseRegistrationForm(request.POST)
        equipment_choice = request.POST.get('equipment_choice', 'existing')
        existing_equipment_id = request.POST.get('existing_equipment_instance')
        malfunction_description = request.POST.get('malfunction_description')
        if form.is_valid():
            case = form.save(commit=False)
            if not case.client:
                messages.error(request, "Client selection is mandatory for case registration.")
                return render(request, 'service_manager/case_registration.html', {'form': form, 'new_equipment_form': new_equipment_form, 'equipment_instances_for_client': EquipmentInstance.objects.none()})
            case.save()
            equipment_to_add_to_case = None
            if equipment_choice == 'existing' and existing_equipment_id:
                try: equipment_to_add_to_case = EquipmentInstance.objects.get(id=existing_equipment_id, current_client=case.client)
                except EquipmentInstance.DoesNotExist: messages.error(request, "Selected existing equipment not found or does not belong to the client.")
            elif equipment_choice == 'new':
                if new_equipment_form.is_valid():
                    new_equip_instance = new_equipment_form.save(commit=False)
                    new_equip_instance.current_client = case.client
                    new_equip_instance.save()
                    equipment_to_add_to_case = new_equip_instance
                    messages.success(request, f"New equipment '{new_equip_instance.serial_no}' registered.")
                else:
                    messages.error(request, "Error registering new equipment.")
                    client_equipment = EquipmentInstance.objects.filter(current_client=case.client) if case.client else EquipmentInstance.objects.none()
                    return render(request, 'service_manager/case_registration.html', {'form': form, 'new_equipment_form': new_equipment_form, 'equipment_instances_for_client': client_equipment})
            if equipment_to_add_to_case and malfunction_description:
                CaseItem.objects.create(case=case, equipment_instance=equipment_to_add_to_case, malfunction_description=malfunction_description)
                messages.success(request, f"Case {case.case_no} registered with item.")
            elif equipment_to_add_to_case and not malfunction_description:
                 messages.warning(request, f"Case {case.case_no} registered with equipment, but no malfunction description was provided.")
            elif not equipment_to_add_to_case and malfunction_description:
                messages.warning(request, f"Case {case.case_no} registered. Malfunction description provided, but no equipment was selected or registered.")
            else:
                messages.success(request, f"Case {case.case_no} registered successfully.")
            return redirect('service_manager:workplace_dashboard')
        else:
            messages.error(request, "Please correct errors in the case form.")
            selected_client_id = form.data.get('client')
            client_equipment = EquipmentInstance.objects.filter(current_client_id=selected_client_id) if selected_client_id else EquipmentInstance.objects.none()
            return render(request, 'service_manager/case_registration.html', {'form': form, 'new_equipment_form': new_equipment_form, 'equipment_instances_for_client': client_equipment})
    else:
        form = CaseRegistrationForm(); new_equipment_form = EquipmentInstanceForm(prefix="new_equip")
    return render(request, 'service_manager/case_registration.html', {'form': form, 'new_equipment_form': new_equipment_form, 'equipment_instances_for_client': EquipmentInstance.objects.none()})

@login_required
@permission_required('service_manager.view_case', raise_exception=True)
def case_detail(request, case_no):
    case = get_object_or_404(Case, case_no=case_no)
    case_items = case.items.all()
    return render(request, 'service_manager/case_detail.html', {'case': case, 'case_items': case_items})

@login_required
@permission_required('service_manager.view_case', raise_exception=True)
def queue_new_registration(request):
    new_cases = Case.objects.filter(status=CaseStatus.NEW).order_by('-registration_date')
    return render(request, 'service_manager/case_list.html', {'cases_list': new_cases, 'list_title': 'New Registrations Queue', 'status_filter': CaseStatus.NEW})

@login_required
@permission_required('service_manager.change_case', raise_exception=True)
def case_confirm_receiving(request, case_no):
    case = get_object_or_404(Case, case_no=case_no)
    if request.method == 'POST':
        if case.status == CaseStatus.NEW:
            case.status = CaseStatus.AWAITING_QUOTATION
            case.received_date = timezone.now()
            case.save(update_fields=['status', 'received_date'])
            messages.success(request, f"Case {case.case_no} status: '{case.get_status_display()}'.")
        else: messages.error(request, f"Case not in '{CaseStatus.NEW.label}' status.")
        return redirect('service_manager:case_detail', case_no=case.case_no)
    messages.info(request, "Use button on case detail page.")
    return redirect('service_manager:case_detail', case_no=case.case_no)

# --- Quotation Views ---
@login_required
# @permission_required('service_manager.add_quotation', raise_exception=True)
def create_quotation_for_case(request, case_no):
    case = get_object_or_404(Case, case_no=case_no)
    if hasattr(case, 'quotation') and case.quotation:
        messages.info(request, f"Quotation for case {case.case_no} exists.")
        return redirect('service_manager:view_quotation', quotation_id=case.quotation.id)
    if request.method == 'POST':
        form = QuotationForm(request.POST)
        formset = QuotationLineItemFormSet(request.POST, prefix='lineitems')
        if form.is_valid() and formset.is_valid():
            quotation = form.save(commit=False)
            quotation.case = case
            if not quotation.quotation_no: quotation.quotation_no = f"QUO-{case.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            quotation.save(); formset.instance = quotation; formset.save()
            quotation.total_amount = quotation.calculate_total_amount()
            quotation.save(update_fields=['total_amount'])
            case.status = CaseStatus.QUOTATION_SUBMITTED; case.quotation_date = timezone.now()
            case.save(update_fields=['status', 'quotation_date'])
            messages.success(request, f"Quotation {quotation.quotation_no} created.")
            return redirect('service_manager:view_quotation', quotation_id=quotation.id)
        else: messages.error(request, "Correct errors.")
    else:
        form = QuotationForm(initial={'quotation_no': f"QUO-{case.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"})
        formset = QuotationLineItemFormSet(prefix='lineitems')
    return render(request, 'service_manager/quotation_form.html', {'form': form, 'formset': formset, 'case': case, 'form_title': f'Create Quotation for Case {case.case_no}'})

@login_required
# @permission_required('service_manager.view_quotation', raise_exception=True)
def view_quotation(request, quotation_id):
    quotation = get_object_or_404(Quotation.objects.prefetch_related('lineitems', 'lineitems__spare_part'), id=quotation_id)
    return render(request, 'service_manager/quotation_detail.html', {'quotation': quotation})

@login_required
# @permission_required('service_manager.change_quotation', raise_exception=True)
def update_quotation_status(request, quotation_id):
    quotation = get_object_or_404(Quotation, id=quotation_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in [s[0] for s in Quotation.QUOTATION_STATUS_CHOICES]:
            quotation.status = new_status; quotation.save()
            messages.success(request, f"Quotation status: {quotation.get_status_display()}.")
            if new_status == 'APPROVED': quotation.case.status = CaseStatus.QUOTATION_APPROVED
            elif new_status == 'REJECTED': quotation.case.status = CaseStatus.QUOTATION_REJECTED
            quotation.case.save(update_fields=['status'])
        else: messages.error(request, "Invalid status.")
    return redirect('service_manager:view_quotation', quotation_id=quotation.id)

# --- Repair Views ---
@login_required
@permission_required('service_manager.view_case', raise_exception=True)
def repair_queue_view(request):
    repair_cases = Case.objects.filter(
        Q(status=CaseStatus.QUOTATION_APPROVED) | Q(status=CaseStatus.REPAIR_IN_PROGRESS)
    ).order_by('registration_date').select_related('client')
    return render(request, 'service_manager/case_list.html', {
        'cases_list': repair_cases, 'list_title': 'Repair Queue', 'status_filter': 'RepairPhase'
    })

@login_required
@permission_required('service_manager.change_case', raise_exception=True)
def manage_case_repair(request, case_no):
    case = get_object_or_404(Case.objects.prefetch_related('items', 'items__equipment_instance__model__brand'), case_no=case_no)
    item_formsets = {}
    if request.method == 'POST':
        action = request.POST.get('action')
        all_formsets_valid = True
        temp_formsets_for_validation = {}
        if action == 'mark_repair_complete' or action == 'save_parts':
            for item in case.items.all():
                formset = CaseSparePartUsageFormSet(request.POST, instance=item, prefix=f'item-{item.id}-parts')
                temp_formsets_for_validation[item.id] = formset
                if not formset.is_valid(): all_formsets_valid = False; messages.error(request, f"Errors in parts for item: {item.equipment_instance.serial_no if item.equipment_instance else 'N/A'}.")
            if all_formsets_valid:
                for item_id, formset in temp_formsets_for_validation.items(): formset.save()
                if action == 'mark_repair_complete':
                    if case.status == CaseStatus.REPAIR_IN_PROGRESS:
                        case.status = CaseStatus.REPAIR_COMPLETED; case.save(update_fields=['status'])
                        messages.success(request, f"Repair completed for Case {case.case_no} & parts saved.")
                    else: messages.warning(request, f"Case not in 'Repair In Progress'. Parts saved, status not changed.")
                else: messages.success(request, "Spare parts usage updated.")
            else: item_formsets = temp_formsets_for_validation
        elif action == 'start_repair' and case.status == CaseStatus.QUOTATION_APPROVED:
            case.status = CaseStatus.REPAIR_IN_PROGRESS; case.repair_start_date = timezone.now()
            case.save(update_fields=['status', 'repair_start_date']); messages.success(request, f"Repair started for Case {case.case_no}.")
        else: messages.warning(request, "No action or invalid action.")
        if all_formsets_valid: return redirect('service_manager:manage_case_repair', case_no=case.case_no)
    for item in case.items.all():
        if item.id not in item_formsets: item_formsets[item.id] = CaseSparePartUsageFormSet(instance=item, prefix=f'item-{item.id}-parts')
    return render(request, 'service_manager/manage_case_repair.html', {'case': case, 'item_formsets': item_formsets})

# --- QC Views ---
@login_required
@permission_required('service_manager.view_case', raise_exception=True)
def qc_queue_view(request):
    qc_cases = Case.objects.filter(status=CaseStatus.REPAIR_COMPLETED).order_by('registration_date').select_related('client')
    return render(request, 'service_manager/case_list.html', {'cases_list': qc_cases, 'list_title': 'QC Queue (Pending QC)', 'status_filter': 'QCPhase'})

@login_required
@permission_required('service_manager.change_case', raise_exception=True)
def manage_case_qc(request, case_no):
    case = get_object_or_404(Case.objects.select_related('client', 'quotation'), case_no=case_no)
    if request.method == 'POST':
        action = request.POST.get('qc_action'); qc_notes_from_form = request.POST.get('qc_notes', '')
        if action == 'passed':
            if case.status == CaseStatus.REPAIR_COMPLETED:
                case.status = CaseStatus.QC_PASSED
                if hasattr(case, 'qc_date'): case.qc_date = timezone.now()
                if hasattr(case, 'qc_notes'): case.qc_notes = qc_notes_from_form if qc_notes_from_form else "QC Passed."
                case.save(); messages.success(request, f"Case {case.case_no} QC Passed.")
            else: messages.error(request, f"Case not in '{CaseStatus.REPAIR_COMPLETED.label}' status.")
            return redirect('service_manager:qc_queue')
        elif action == 'failed':
            if case.status == CaseStatus.REPAIR_COMPLETED:
                case.status = CaseStatus.QC_FAILED
                if hasattr(case, 'qc_date'): case.qc_date = timezone.now()
                if hasattr(case, 'qc_notes'): case.qc_notes = qc_notes_from_form
                elif hasattr(case, 'notes') and qc_notes_from_form: case.notes = (case.notes + "\n" if case.notes else "") + f"QC Failed Notes: {qc_notes_from_form}"
                case.save(); messages.warning(request, f"Case {case.case_no} QC Failed. Notes: '{qc_notes_from_form}'.")
            else: messages.error(request, f"Case not in '{CaseStatus.REPAIR_COMPLETED.label}' status.")
            return redirect('service_manager:qc_queue')
        else: messages.error(request, "Invalid QC action.")
    return render(request, 'service_manager/manage_case_qc.html', {'case': case})

# --- Delivery and Closing Views ---
@login_required
@permission_required('service_manager.view_case', raise_exception=True)
def delivery_queue_view(request):
    delivery_cases = Case.objects.filter(status=CaseStatus.QC_PASSED).order_by('qc_date', 'registration_date').select_related('client')
    return render(request, 'service_manager/case_list.html', {
        'cases_list': delivery_cases, 'list_title': 'Delivery Queue (Pending Delivery)', 'status_filter': 'DeliveryPhase'
    })

@login_required
@permission_required('service_manager.change_case', raise_exception=True)
def manage_case_delivery(request, case_no):
    case = get_object_or_404(Case.objects.select_related('client'), case_no=case_no)
    if request.method == 'POST':
        if 'confirm_delivery' in request.POST:
            if case.status == CaseStatus.QC_PASSED:
                case.status = CaseStatus.DELIVERED_PENDING_CLOSING
                case.delivery_date = timezone.now()
                delivery_notes = request.POST.get('delivery_notes', '')
                if hasattr(case, 'delivery_notes'): case.delivery_notes = delivery_notes
                elif delivery_notes and hasattr(case, 'notes'): case.notes = (case.notes + "\n" if case.notes else "") + f"Delivery Notes: {delivery_notes}"
                case.save(); messages.success(request, f"Case {case.case_no} marked as delivered.")
            else: messages.error(request, f"Case not in '{CaseStatus.QC_PASSED.label}' status.")
        else: messages.error(request, "Invalid action.")
        return redirect('service_manager:case_detail', case_no=case.case_no)
    return render(request, 'service_manager/manage_case_delivery.html', {'case': case})

@login_required
@permission_required('service_manager.change_case', raise_exception=True)
def final_close_case_view(request, case_no):
    case = get_object_or_404(Case.objects.select_related('client'), case_no=case_no)
    if request.method == 'POST':
        if 'confirm_close' in request.POST:
            if case.status == CaseStatus.DELIVERED_PENDING_CLOSING:
                case.status = CaseStatus.CLOSED
                case.closed_date = timezone.now()
                closing_notes = request.POST.get('closing_notes', '')
                if hasattr(case, 'closing_notes'): case.closing_notes = closing_notes
                elif closing_notes and hasattr(case, 'notes'): case.notes = (case.notes + "\n" if case.notes else "") + f"Closing Notes: {closing_notes}"
                case.save(); messages.success(request, f"Case {case.case_no} closed.")
            else: messages.error(request, f"Case not in '{CaseStatus.DELIVERED_PENDING_CLOSING.label}' status for closing.")
        else: messages.error(request, "Invalid action.")
        return redirect('service_manager:case_detail', case_no=case.case_no)
    return render(request, 'service_manager/final_close_case_form.html', {'case': case})

# --- Configuration Views ---
@login_required
@permission_required('service_manager.view_client', raise_exception=True)
def config_dashboard(request): return render(request, 'service_manager/config_dashboard.html')

@login_required
@permission_required('service_manager.view_client', raise_exception=True)
def client_list(request): return render(request, 'service_manager/client_list.html', {'clients': Client.objects.all().order_by('name')})

@login_required
@permission_required('service_manager.add_client', raise_exception=True)
def client_add(request):
    if request.method == 'POST':
        form = ClientForm(request.POST);
        if form.is_valid(): form.save(); messages.success(request, "Client added."); return redirect('service_manager:client_list')
    else: form = ClientForm()
    return render(request, 'service_manager/client_form.html', {'form': form, 'form_title': 'Add Client'})

@login_required
@permission_required('service_manager.change_client', raise_exception=True)
def client_edit(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client);
        if form.is_valid(): form.save(); messages.success(request, "Client updated."); return redirect('service_manager:client_list')
    else: form = ClientForm(instance=client)
    return render(request, 'service_manager/client_form.html', {'form': form, 'form_title': 'Edit Client'})

@login_required
@permission_required('service_manager.view_brand', raise_exception=True)
def brand_list(request): return render(request, 'service_manager/brand_list.html', {'brands': Brand.objects.all().order_by('name')})

@login_required
@permission_required('service_manager.add_brand', raise_exception=True)
def brand_add(request):
    if request.method == 'POST':
        form = BrandForm(request.POST);
        if form.is_valid(): form.save(); messages.success(request, "Brand added."); return redirect('service_manager:brand_list')
    else: form = BrandForm()
    return render(request, 'service_manager/brand_form.html', {'form': form, 'form_title': 'Add Brand'})

@login_required
@permission_required('service_manager.change_brand', raise_exception=True)
def brand_edit(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)
    if request.method == 'POST':
        form = BrandForm(request.POST, instance=brand);
        if form.is_valid(): form.save(); messages.success(request, "Brand updated."); return redirect('service_manager:brand_list')
    else: form = BrandForm(instance=brand)
    return render(request, 'service_manager/brand_form.html', {'form': form, 'form_title': 'Edit Brand'})

@login_required
@permission_required('service_manager.view_equipmentmodel', raise_exception=True)
def equipment_model_list(request): return render(request, 'service_manager/equipment_model_list.html', {'equipment_models': EquipmentModel.objects.select_related('brand').all().order_by('brand__name', 'name')})

@login_required
@permission_required('service_manager.add_equipmentmodel', raise_exception=True)
def equipment_model_add(request):
    if request.method == 'POST':
        form = EquipmentModelForm(request.POST);
        if form.is_valid(): form.save(); messages.success(request, "Model added."); return redirect('service_manager:equipment_model_list')
    else: form = EquipmentModelForm()
    return render(request, 'service_manager/equipment_model_form.html', {'form': form, 'form_title': 'Add Model'})

@login_required
@permission_required('service_manager.change_equipmentmodel', raise_exception=True)
def equipment_model_edit(request, model_id):
    model = get_object_or_404(EquipmentModel, id=model_id)
    if request.method == 'POST':
        form = EquipmentModelForm(request.POST, instance=model);
        if form.is_valid(): form.save(); messages.success(request, "Model updated."); return redirect('service_manager:equipment_model_list')
    else: form = EquipmentModelForm(instance=model)
    return render(request, 'service_manager/equipment_model_form.html', {'form': form, 'form_title': 'Edit Model'})

@login_required
@permission_required('service_manager.view_equipmentinstance', raise_exception=True)
def equipment_instance_list(request): return render(request, 'service_manager/equipment_instance_list.html', {'instances': EquipmentInstance.objects.select_related('model', 'model__brand', 'current_client').all().order_by('serial_no')})

@login_required
@permission_required('service_manager.add_equipmentinstance', raise_exception=True)
def equipment_instance_add(request):
    if request.method == 'POST':
        form = EquipmentInstanceForm(request.POST);
        if form.is_valid(): form.save(); messages.success(request, "Instance added."); return redirect('service_manager:equipment_instance_list')
    else: form = EquipmentInstanceForm()
    return render(request, 'service_manager/equipment_instance_form.html', {'form': form, 'form_title': 'Add Instance'})

@login_required
@permission_required('service_manager.change_equipmentinstance', raise_exception=True)
def equipment_instance_edit(request, instance_id):
    instance = get_object_or_404(EquipmentInstance, id=instance_id)
    if request.method == 'POST':
        form = EquipmentInstanceForm(request.POST, instance=instance);
        if form.is_valid(): form.save(); messages.success(request, "Instance updated."); return redirect('service_manager:equipment_instance_list')
    else: form = EquipmentInstanceForm(instance=instance)
    return render(request, 'service_manager/equipment_instance_form.html', {'form': form, 'form_title': 'Edit Instance'})

@login_required
@permission_required('service_manager.view_sparepart', raise_exception=True)
def spare_part_list(request):
    spare_parts = SparePart.objects.select_related('brand').all().order_by('name')
    return render(request, 'service_manager/spare_part_list.html', {'spare_parts': spare_parts})

@login_required
@permission_required('service_manager.add_sparepart', raise_exception=True)
def spare_part_add(request):
    if request.method == 'POST':
        form = SparePartForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Spare Part '{form.cleaned_data['name']}' added successfully.")
            return redirect('service_manager:spare_part_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SparePartForm()
    return render(request, 'service_manager/spare_part_form.html', {
        'form': form,
        'form_title': 'Add New Spare Part'
    })

@login_required
@permission_required('service_manager.change_sparepart', raise_exception=True)
def spare_part_edit(request, part_id):
    spare_part_instance = get_object_or_404(SparePart, id=part_id)
    if request.method == 'POST':
        form = SparePartForm(request.POST, instance=spare_part_instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"Spare Part '{form.cleaned_data['name']}' updated successfully.")
            return redirect('service_manager:spare_part_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SparePartForm(instance=spare_part_instance)
    return render(request, 'service_manager/spare_part_form.html', {
        'form': form,
        'form_title': f"Edit Spare Part: {spare_part_instance.name}"
    })

@login_required
@permission_required('service_manager.view_region', raise_exception=True)
def region_list(request):
    regions = Region.objects.all().order_by('name')
    return render(request, 'service_manager/region_list.html', {'regions': regions})

@login_required
@permission_required('service_manager.add_region', raise_exception=True)
def region_add(request):
    if request.method == 'POST':
        form = RegionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Region '{form.cleaned_data['name']}' added successfully.")
            return redirect('service_manager:region_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegionForm()
    return render(request, 'service_manager/region_form.html', {
        'form': form,
        'form_title': 'Add New Region'
    })

@login_required
@permission_required('service_manager.change_region', raise_exception=True)
def region_edit(request, region_id):
    region_instance = get_object_or_404(Region, id=region_id)
    if request.method == 'POST':
        form = RegionForm(request.POST, instance=region_instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"Region '{form.cleaned_data['name']}' updated successfully.")
            return redirect('service_manager:region_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegionForm(instance=region_instance)
    return render(request, 'service_manager/region_form.html', {
        'form': form,
        'form_title': f"Edit Region: {region_instance.name}"
    })

@login_required
@permission_required('service_manager.view_malfunctiontype', raise_exception=True)
def malfunction_type_list(request):
    malfunction_types = MalfunctionType.objects.all().order_by('name')
    return render(request, 'service_manager/malfunction_type_list.html', {'malfunction_types': malfunction_types})

@login_required
@permission_required('service_manager.add_malfunctiontype', raise_exception=True)
def malfunction_type_add(request):
    if request.method == 'POST':
        form = MalfunctionTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Malfunction Type '{form.cleaned_data['name']}' added successfully.")
            return redirect('service_manager:malfunction_type_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = MalfunctionTypeForm()
    return render(request, 'service_manager/malfunction_type_form.html', {
        'form': form,
        'form_title': 'Add New Malfunction Type'
    })

@login_required
@permission_required('service_manager.change_malfunctiontype', raise_exception=True)
def malfunction_type_edit(request, mf_id):
    malfunction_type_instance = get_object_or_404(MalfunctionType, id=mf_id)
    if request.method == 'POST':
        form = MalfunctionTypeForm(request.POST, instance=malfunction_type_instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"Malfunction Type '{form.cleaned_data['name']}' updated successfully.")
            return redirect('service_manager:malfunction_type_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = MalfunctionTypeForm(instance=malfunction_type_instance)
    return render(request, 'service_manager/malfunction_type_form.html', {
        'form': form,
        'form_title': f"Edit Malfunction Type: {malfunction_type_instance.name}"
    })

@login_required
@permission_required('service_manager.view_supplier', raise_exception=True)
def supplier_list(request):
    suppliers = Supplier.objects.all().order_by('name')
    return render(request, 'service_manager/supplier_list.html', {'suppliers': suppliers})

@login_required
@permission_required('service_manager.add_supplier', raise_exception=True)
def supplier_add(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Supplier '{form.cleaned_data['name']}' added successfully.")
            return redirect('service_manager:supplier_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SupplierForm()
    return render(request, 'service_manager/supplier_form.html', {
        'form': form,
        'form_title': 'Add New Supplier'
    })

@login_required
@permission_required('service_manager.change_supplier', raise_exception=True)
def supplier_edit(request, sup_id):
    supplier_instance = get_object_or_404(Supplier, id=sup_id)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier_instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"Supplier '{form.cleaned_data['name']}' updated successfully.")
            return redirect('service_manager:supplier_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SupplierForm(instance=supplier_instance)
    return render(request, 'service_manager/supplier_form.html', {
        'form': form,
        'form_title': f"Edit Supplier: {supplier_instance.name}"
    })

@login_required
def storage_location_list(request): return HttpResponse("Storage Location List") # Placeholder
@login_required
def storage_location_add(request): return HttpResponse("Add New Storage Location Form") # Placeholder
@login_required
def storage_location_edit(request, loc_id): return HttpResponse(f"Edit Storage Location {loc_id}") # Placeholder

# --- Other Placeholder views ---
@login_required
def case_quotation(request, case_no): return HttpResponse(f"Case Quotation for {case_no}")
@login_required
def case_repair(request, case_no): return HttpResponse(f"Case Repair for {case_no}")
@login_required
def case_qc(request, case_no): return HttpResponse(f"Case QC for {case_no}")
@login_required
def case_delivery(request, case_no): return HttpResponse(f"Case Delivery for {case_no}")
@login_required
def case_close(request, case_no): return HttpResponse(f"Case Close for {case_no}")
@login_required
def queue_waiting_quotation(request): return HttpResponse("Queue: Waiting for Quotation")
@login_required
def queue_waiting_repair(request): return HttpResponse("Queue: Waiting for Repair")
@login_required
def queue_completed(request): return HttpResponse("Queue: Completed Cases")

@login_required
def user_list(request): return HttpResponse("User List")
@login_required
def user_add(request): return HttpResponse("Add New User/SalesPerson Form")


[end of repair_service_project/service_manager/views.py]
