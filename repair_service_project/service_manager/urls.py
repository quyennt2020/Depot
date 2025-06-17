from django.urls import path
from . import views

app_name = 'service_manager'

urlpatterns = [
    # == WORKPLACE URLs ==
    path('workplace/', views.workplace_dashboard, name='workplace_dashboard'), # A general landing page for workplace

    # Case Workflow URLs
    path('workplace/cases/register/', views.case_registration, name='case_registration'),
    path('workplace/cases/<str:case_no>/', views.case_detail, name='case_detail'), # View details of a specific case

    # New URL for confirming receipt, replacing the old placeholder
    path('workplace/cases/<str:case_no>/confirm_receiving/', views.case_confirm_receiving, name='case_confirm_receiving'),

    path('workplace/cases/<str:case_no>/quote/', views.case_quotation, name='case_quotation'),
    path('workplace/cases/<str:case_no>/repair/', views.case_repair, name='case_repair'),
    path('workplace/cases/<str:case_no>/qc/', views.case_qc, name='case_qc'),
    path('workplace/cases/<str:case_no>/deliver/', views.case_delivery, name='case_delivery'),
    path('workplace/cases/<str:case_no>/close/', views.case_close, name='case_close'),

    # Status Queue List Views
    path('workplace/queues/new/', views.queue_new_registration, name='queue_new_registration'),
    path('workplace/queues/waiting_quotation/', views.queue_waiting_quotation, name='queue_waiting_quotation'),
    path('workplace/queues/waiting_repair/', views.queue_waiting_repair, name='queue_waiting_repair'),
    path('workplace/queues/completed/', views.queue_completed, name='queue_completed'),
    # ... other status queues as needed

    # == CONFIGURATION (Admin/Setup) URLs ==
    path('config/', views.config_dashboard, name='config_dashboard'), # A general landing page for configuration

    # Client Setup
    path('config/clients/', views.client_list, name='client_list'),
    path('config/clients/add/', views.client_add, name='client_add'),
    path('config/clients/<int:client_id>/edit/', views.client_edit, name='client_edit'),

    # Equipment Model Setup
    path('config/equipment_models/', views.equipment_model_list, name='equipment_model_list'),
    path('config/equipment_models/add/', views.equipment_model_add, name='equipment_model_add'),
    path('config/equipment_models/<int:model_id>/edit/', views.equipment_model_edit, name='equipment_model_edit'),

    # Equipment Instance Setup
    path('config/equipment_instances/', views.equipment_instance_list, name='equipment_instance_list'),
    path('config/equipment_instances/add/', views.equipment_instance_add, name='equipment_instance_add'),
    path('config/equipment_instances/<int:instance_id>/edit/', views.equipment_instance_edit, name='equipment_instance_edit'),

    # Spare Part Setup
    path('config/spare_parts/', views.spare_part_list, name='spare_part_list'),
    path('config/spare_parts/add/', views.spare_part_add, name='spare_part_add'),
    path('config/spare_parts/<int:part_id>/edit/', views.spare_part_edit, name='spare_part_edit'),

    # Brand Setup
    path('config/brands/', views.brand_list, name='brand_list'),
    path('config/brands/add/', views.brand_add, name='brand_add'),
    path('config/brands/<int:brand_id>/edit/', views.brand_edit, name='brand_edit'),

    # User Setup (Leverage Django admin for full user management, but can have simplified views if needed)
    path('config/users/', views.user_list, name='user_list'), # Basic list, actual management via admin
    path('config/users/add/', views.user_add, name='user_add'), # Could be a simplified form for creating SalesPerson profiles

    # Region Setup
    path('config/regions/', views.region_list, name='region_list'),
    path('config/regions/add/', views.region_add, name='region_add'),
    path('config/regions/<int:region_id>/edit/', views.region_edit, name='region_edit'),

    # Other Configs (MalfunctionType, Supplier, StorageLocation) - similar list, add, edit patterns
    path('config/malfunctions/', views.malfunction_list, name='malfunction_list'),
    path('config/malfunctions/add/', views.malfunction_add, name='malfunction_add'),
    path('config/malfunctions/<int:mf_id>/edit/', views.malfunction_edit, name='malfunction_edit'),

    path('config/suppliers/', views.supplier_list, name='supplier_list'),
    path('config/suppliers/add/', views.supplier_add, name='supplier_add'),
    path('config/suppliers/<int:sup_id>/edit/', views.supplier_edit, name='supplier_edit'),

    path('config/storage_locations/', views.storage_location_list, name='storage_location_list'),
    path('config/storage_locations/add/', views.storage_location_add, name='storage_location_add'),
    path('config/storage_locations/<int:loc_id>/edit/', views.storage_location_edit, name='storage_location_edit'),
]
