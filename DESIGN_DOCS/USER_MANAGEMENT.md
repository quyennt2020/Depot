# User Management and Permissions Strategy

This document outlines the approach to user management, roles, and permissions for the Service Management System, primarily leveraging Django's built-in authentication and authorization framework.

## 1. Core User Model

*   **Django's `User` Model:** We will use the standard `django.contrib.auth.models.User` model for basic user authentication (username, password, email, first name, last name).
*   **`SalesPerson` Profile:** The existing `service_manager.models.SalesPerson` model, which has a `OneToOneField` to `User`, will be used to store additional information specific to sales personnel (e.g., `phone_extension`, `region`). Other roles might have similar profile models if specific fields are required beyond what Django's `User` model offers.

## 2. Roles and Groups

We will use Django's `Group` model (`django.contrib.auth.models.Group`) to define user roles. Each user will be assigned to one or more groups, and permissions will be granted at the group level.

**Proposed Groups:**

*   **Receptionist:** Primarily handles case registration, client interaction, and initial data entry.
*   **WarehouseStaff:** Manages receiving of physical items, possibly some inventory aspects.
*   **Technician:** Performs assessments, quotations (or provides input for them), repairs, and records spare part usage.
*   **QCStaff:** Performs quality control checks on repaired items.
*   **ServiceManager:** Oversees the entire workflow, can manage cases at any stage, handles escalations, views reports, and manages configurations.
*   **SystemAdmin:** Has full control over the system, including user management, group and permission assignments, and all configurations. This role will heavily use the Django Admin interface.

## 3. Permissions

Django's built-in permission system will be used. For each model defined in `service_manager/models.py`, Django automatically creates `add`, `change`, `delete`, and `view` permissions.

**Assigning Permissions to Groups (Examples):**

*   **Receptionist:**
    *   `Can add case`
    *   `Can change case` (limited fields/statuses, e.g., during registration)
    *   `Can view case`
    *   `Can add client`
    *   `Can change client`
    *   `Can view client`
    *   `Can view equipmentmodel` (to select models during registration)
    *   `Can add equipmentinstance` (for new equipment)
    *   `Can change equipmentinstance`
    *   `Can view equipmentinstance`
*   **WarehouseStaff:**
    *   `Can change case` (specifically to update status to 'Receiving' and add `received_date`)
    *   `Can view case`
    *   `Can view equipmentinstance`
*   **Technician:**
    *   `Can change case` (update status through 'Quotation', 'Repairing'; add repair notes)
    *   `Can view case`
    *   `Can add caseitem` (if more issues found)
    *   `Can change caseitem`
    *   `Can view caseitem`
    *   `Can add casesparepartusage`
    *   `Can change casesparepartusage`
    *   `Can view sparepart` (to select parts)
*   **QCStaff:**
    *   `Can change case` (update status to 'QC' or revert if failed)
    *   `Can view case`
*   **ServiceManager:**
    *   Has most `add`, `change`, `delete`, `view` permissions for nearly all `service_manager` models.
    *   Can access reporting features.
*   **SystemAdmin:**
    *   All permissions for all models, including `auth.User` and `auth.Group`.

**Custom Permissions:**
*   If more granular control is needed beyond the standard CRUD permissions, custom permissions can be defined in the `Meta` class of a model (e.g., `permissions = [("can_approve_quotation", "Can approve quotation")]`). These would then be assigned to groups like any other permission.

## 4. Django Admin Site

*   The Django Admin site (`/admin/`) will be the primary interface for `SystemAdmin` and potentially `ServiceManager` roles to:
    *   Create, update, and delete users.
    *   Create and manage groups.
    *   Assign users to groups.
    *   Assign permissions to groups.
    *   Manage master data directly (e.g., `Brand`, `Region`, `MalfunctionType`) if not exclusively handled through the 'CONFIGURATION' module in the main app. The 'CONFIGURATION' module provides a more user-friendly interface for these tasks for non-admin power users.

## 5. View-Level Authorization

In `service_manager/views.py`, access to views will be controlled using:

*   **`@login_required` decorator:** To ensure only authenticated users can access specific views.
    ```python
    from django.contrib.auth.decorators import login_required

    @login_required
    def case_detail(request, case_no):
        # ...
    ```
*   **`@permission_required` decorator:** To restrict access based on specific permissions.
    ```python
    from django.contrib.auth.decorators import permission_required

    @permission_required('service_manager.add_client', raise_exception=True)
    def client_add(request):
        # ...
    ```
*   **UserPassesTestMixin / @user_passes_test decorator:** For more complex logic, like checking if a user belongs to a specific group.
    ```python
    from django.contrib.auth.decorators import user_passes_test

    def is_technician(user):
        return user.groups.filter(name='Technician').exists()

    @user_passes_test(is_technician)
    def technician_dashboard(request):
        # ...
    ```
*   **Programmatic Checks:** Inside views, `request.user.has_perm('app_label.permission_codename')` can be used for fine-grained control within the view logic.

## 6. SalesPerson Model

*   The `SalesPerson` model links to a `User`.
*   Creation of `SalesPerson` instances could be:
    1.  Two-step: Create `User` in Django Admin, then create `SalesPerson` profile via 'CONFIGURATION' module or Admin, linking to the user.
    2.  One-step: A custom form (`SalesPersonForm` in `forms.py`) in the 'CONFIGURATION' module that creates both the `User` and the `SalesPerson` profile simultaneously. This is often more user-friendly for administrators.
*   Permissions related to `SalesPerson` would be managed like any other model.

This strategy provides a robust and flexible way to manage user access, leveraging Django's well-tested components. The specific permissions assigned to each group will need to be carefully reviewed and adjusted during implementation and testing.
