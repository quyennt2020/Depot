from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse # Keep for other placeholders
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
# Add EquipmentInstanceForm
from .forms import CaseRegistrationForm, ClientForm, BrandForm, EquipmentModelForm, EquipmentInstanceForm
# EquipmentInstance was already imported, ensure Client, EquipmentModel also present for form choices
from .models import Case, Client, EquipmentInstance, CaseItem, EquipmentModel, Region, Brand

# --- Retain all previously implemented views ---
def workplace_dashboard(request):
    cases = Case.objects.all().order_by('-registration_date')[:10]
    new_registration_cases_count = Case.objects.filter(status='NEW').count()
    return render(request, 'service_manager/workplace_dashboard.html', {
        'cases': cases,
        'new_registration_cases_count': new_registration_cases_count
    })

# --- Modified Case Registration View ---
def case_registration(request):
    new_equipment_form = EquipmentInstanceForm(request.POST or None, prefix="new_equip")

    if request.method == 'POST':
        form = CaseRegistrationForm(request.POST)
        equipment_choice = request.POST.get('equipment_choice', 'existing')
        existing_equipment_id = request.POST.get('existing_equipment_instance')
        malfunction_description = request.POST.get('malfunction_description')

        if form.is_valid():
            case = form.save(commit=False)

            if not case.client: # Client is required on Case model, but also for equipment logic
                messages.error(request, "Client selection is mandatory for case registration.")
                # Re-render form with error
                return render(request, 'service_manager/case_registration.html', {
                    'form': form, # Main case form with its errors
                    'new_equipment_form': new_equipment_form, # New equipment form (might have its own errors if new was chosen)
                    'equipment_instances_for_client': EquipmentInstance.objects.none(),
                })
            case.save() # Save case now that client is confirmed valid (form.is_valid() checks this if client is required in CaseForm)

            equipment_to_add_to_case = None

            if equipment_choice == 'existing' and existing_equipment_id:
                try:
                    equipment_to_add_to_case = EquipmentInstance.objects.get(id=existing_equipment_id, current_client=case.client)
                except EquipmentInstance.DoesNotExist:
                    messages.error(request, "Selected existing equipment not found or does not belong to the client.")

            elif equipment_choice == 'new':
                if new_equipment_form.is_valid():
                    new_equip_instance = new_equipment_form.save(commit=False)
                    new_equip_instance.current_client = case.client
                    new_equip_instance.save()
                    equipment_to_add_to_case = new_equip_instance
                    messages.success(request, f"New equipment '{new_equip_instance.serial_no}' registered and assigned to client '{case.client.name}'.")
                else:
                    messages.error(request, "Error registering new equipment. Please check the new equipment details provided.")
                    # Re-render form with errors for new_equipment_form
                    client_equipment = EquipmentInstance.objects.filter(current_client=case.client) if case.client else EquipmentInstance.objects.none()
                    return render(request, 'service_manager/case_registration.html', {
                        'form': form,
                        'new_equipment_form': new_equipment_form,
                        'equipment_instances_for_client': client_equipment,
                    })

            if equipment_to_add_to_case and malfunction_description:
                CaseItem.objects.create(
                    case=case,
                    equipment_instance=equipment_to_add_to_case,
                    malfunction_description=malfunction_description
                )
                messages.success(request, f"Case {case.case_no} registered successfully with equipment item and malfunction description.")
            elif equipment_to_add_to_case and not malfunction_description:
                 messages.warning(request, f"Case {case.case_no} registered with equipment, but no malfunction description was provided.")
            elif not equipment_to_add_to_case and malfunction_description: # Malfunction description but no equipment
                messages.warning(request, f"Case {case.case_no} registered. Malfunction description provided, but no equipment was selected or registered.")
            else: # Case registered but no equipment selected/error and no malfunction
                messages.success(request, f"Case {case.case_no} registered successfully.")

            return redirect('service_manager:workplace_dashboard')
        else: # Main CaseRegistrationForm is not valid
            messages.error(request, "Please correct the errors in the main case form.")
            # Need to re-populate client_equipment for the template if client was selected
            selected_client_id = form.data.get('client') # form.data as form is bound
            client_equipment = EquipmentInstance.objects.none()
            if selected_client_id:
                try:
                    client_obj = Client.objects.get(id=selected_client_id)
                    client_equipment = EquipmentInstance.objects.filter(current_client=client_obj)
                except Client.DoesNotExist: pass # Should not happen if form validation is correct

            return render(request, 'service_manager/case_registration.html', {
                'form': form, # Main case form with errors
                'new_equipment_form': new_equipment_form, # Potentially with its own errors if 'new' was chosen
                'equipment_instances_for_client': client_equipment,
            })

    else: # GET request
        form = CaseRegistrationForm()
        new_equipment_form = EquipmentInstanceForm(prefix="new_equip")
        # For GET, no client selected yet, so no specific equipment to show.
        # AJAX would be better to populate existing equipment when client is selected.
        client_equipment = EquipmentInstance.objects.none()

    return render(request, 'service_manager/case_registration.html', {
        'form': form,
        'new_equipment_form': new_equipment_form,
        'equipment_instances_for_client': client_equipment,
    })

def case_detail(request, case_no):
    case = get_object_or_404(Case, case_no=case_no)
    case_items = case.items.all()
    return render(request, 'service_manager/case_detail.html', {'case': case, 'case_items': case_items})

def queue_new_registration(request):
    new_cases = Case.objects.filter(status='NEW').order_by('-registration_date')
    return render(request, 'service_manager/case_list.html', {
        'cases_list': new_cases,
        'list_title': 'New Registrations Queue',
        'status_filter': 'NEW'
    })

def case_confirm_receiving(request, case_no):
    case = get_object_or_404(Case, case_no=case_no)
    if request.method == 'POST':
        if case.status == 'NEW':
            case.status = 'RECEIVING'
            case.received_date = timezone.now()
            case.save()
            messages.success(request, f"Case {case.case_no} status updated to 'Receiving'.")
        else:
            messages.error(request, f"Case {case.case_no} is not in 'New Registration' status.")
        return redirect('service_manager:case_detail', case_no=case.case_no)
    messages.info(request, "To confirm receiving, please use the button on the case detail page.")
    return redirect('service_manager:case_detail', case_no=case.case_no)

def config_dashboard(request):
    return render(request, 'service_manager/config_dashboard.html')

def client_list(request):
    clients = Client.objects.all().order_by('name')
    return render(request, 'service_manager/client_list.html', {'clients': clients})

def client_add(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Client '{form.cleaned_data['name']}' added successfully.")
            return redirect('service_manager:client_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ClientForm()
    return render(request, 'service_manager/client_form.html', {'form': form, 'form_title': 'Add New Client'})

def client_edit(request, client_id):
    client_instance = get_object_or_404(Client, id=client_id)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client_instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"Client '{form.cleaned_data['name']}' updated successfully.")
            return redirect('service_manager:client_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ClientForm(instance=client_instance)
    return render(request, 'service_manager/client_form.html', {'form': form, 'form_title': f"Edit Client: {client_instance.name}"})

def brand_list(request):
    brands = Brand.objects.all().order_by('name')
    return render(request, 'service_manager/brand_list.html', {'brands': brands})

def brand_add(request):
    if request.method == 'POST':
        form = BrandForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Brand '{form.cleaned_data['name']}' added successfully.")
            return redirect('service_manager:brand_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = BrandForm()
    return render(request, 'service_manager/brand_form.html', {'form': form, 'form_title': 'Add New Brand'})

def brand_edit(request, brand_id):
    brand_instance = get_object_or_404(Brand, id=brand_id)
    if request.method == 'POST':
        form = BrandForm(request.POST, instance=brand_instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"Brand '{form.cleaned_data['name']}' updated successfully.")
            return redirect('service_manager:brand_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = BrandForm(instance=brand_instance)
    return render(request, 'service_manager/brand_form.html', {'form': form, 'form_title': f"Edit Brand: {brand_instance.name}"})

def equipment_model_list(request):
    equipment_models = EquipmentModel.objects.select_related('brand').all().order_by('brand__name', 'name')
    return render(request, 'service_manager/equipment_model_list.html', {'equipment_models': equipment_models})

def equipment_model_add(request):
    if request.method == 'POST':
        form = EquipmentModelForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Equipment Model '{form.cleaned_data['name']}' added successfully.")
            return redirect('service_manager:equipment_model_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = EquipmentModelForm()
    return render(request, 'service_manager/equipment_model_form.html', {'form': form, 'form_title': 'Add New Equipment Model'})

def equipment_model_edit(request, model_id):
    model_instance = get_object_or_404(EquipmentModel, id=model_id)
    if request.method == 'POST':
        form = EquipmentModelForm(request.POST, instance=model_instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"Equipment Model '{form.cleaned_data['name']}' updated successfully.")
            return redirect('service_manager:equipment_model_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = EquipmentModelForm(instance=model_instance)
    return render(request, 'service_manager/equipment_model_form.html', {'form': form, 'form_title': f"Edit Equipment Model: {model_instance.name}"})

# --- New Equipment Instance Management Views ---
def equipment_instance_list(request):
    instances = EquipmentInstance.objects.select_related('model', 'model__brand', 'current_client').all().order_by('serial_no')
    return render(request, 'service_manager/equipment_instance_list.html', {'instances': instances})

def equipment_instance_add(request):
    if request.method == 'POST':
        form = EquipmentInstanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Equipment Instance '{form.cleaned_data['serial_no']}' added successfully.")
            return redirect('service_manager:equipment_instance_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = EquipmentInstanceForm()
    return render(request, 'service_manager/equipment_instance_form.html', {'form': form, 'form_title': 'Add New Equipment Instance'})

def equipment_instance_edit(request, instance_id):
    instance = get_object_or_404(EquipmentInstance, id=instance_id)
    if request.method == 'POST':
        form = EquipmentInstanceForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"Equipment Instance '{form.cleaned_data['serial_no']}' updated successfully.")
            return redirect('service_manager:equipment_instance_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = EquipmentInstanceForm(instance=instance)
    return render(request, 'service_manager/equipment_instance_form.html', {'form': form, 'form_title': f"Edit Equipment Instance: {instance.serial_no}"})

# --- Retain ALL other placeholder views for other modules ---
def case_quotation(request, case_no): return HttpResponse(f"Case Quotation for {case_no}")
def case_repair(request, case_no): return HttpResponse(f"Case Repair for {case_no}")
def case_qc(request, case_no): return HttpResponse(f"Case QC for {case_no}")
def case_delivery(request, case_no): return HttpResponse(f"Case Delivery for {case_no}")
def case_close(request, case_no): return HttpResponse(f"Case Close for {case_no}")
def queue_waiting_quotation(request): return HttpResponse("Queue: Waiting for Quotation")
def queue_waiting_repair(request): return HttpResponse("Queue: Waiting for Repair")
def queue_completed(request): return HttpResponse("Queue: Completed Cases")

def spare_part_list(request): return HttpResponse("Spare Part List Placeholder")
def spare_part_add(request): return HttpResponse("Add New Spare Part Form")
def spare_part_edit(request, part_id): return HttpResponse(f"Edit Spare Part {part_id}")
def user_list(request): return HttpResponse("User List")
def user_add(request): return HttpResponse("Add New User/SalesPerson Form")
def region_list(request): return HttpResponse("Region List")
def region_add(request): return HttpResponse("Add New Region Form")
def region_edit(request, region_id): return HttpResponse(f"Edit Region {region_id}")
def malfunction_list(request): return HttpResponse("Malfunction Type List")
def malfunction_add(request): return HttpResponse("Add New Malfunction Type Form")
def malfunction_edit(request, mf_id): return HttpResponse(f"Edit Malfunction Type {mf_id}")
def supplier_list(request): return HttpResponse("Supplier List")
def supplier_add(request): return HttpResponse("Add New Supplier Form")
def supplier_edit(request, sup_id): return HttpResponse(f"Edit Supplier {sup_id}")
def storage_location_list(request): return HttpResponse("Storage Location List")
def storage_location_add(request): return HttpResponse("Add New Storage Location Form")
def storage_location_edit(request, loc_id): return HttpResponse(f"Edit Storage Location {loc_id}")
