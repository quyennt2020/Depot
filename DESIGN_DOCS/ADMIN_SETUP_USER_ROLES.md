# Admin Setup: User Roles, Groups, and Permissions

This document outlines the steps to be performed in the Django Admin interface (`/admin/`) to set up user roles (Groups) and assign initial permissions for the Service Management System. These correspond to the roles and responsibilities defined in `DESIGN_DOCS/USER_MANAGEMENT.md`.

**Prerequisites:**
*   A superuser account must have been created (`python manage.py createsuperuser`).
*   The Django development server should be running (`python manage.py runserver`).
*   Navigate to the Django Admin interface (typically `http://127.0.0.1:8000/admin/`).

## Step 1: Accessing Groups Management

1.  Log in to the Django Admin interface with superuser credentials.
2.  In the Admin dashboard, locate the **AUTHENTICATION AND AUTHORIZATION** section.
3.  Click on "**Groups**".

## Step 2: Creating Groups

For each role defined below, click the "**ADD GROUP +**" button and enter the group name. Then, save the group.

**Proposed Groups:**

*   `SystemAdmin`
*   `ServiceManager`
*   `Receptionist`
*   `Technician`
*   `WarehouseStaff`
*   `QCStaff`

## Step 3: Assigning Permissions to Groups

After creating each group, you need to assign permissions to it. Click on a group name in the list to edit it. The "Permissions" section will show a list of available permissions. Select the relevant permissions for each group as outlined below.

**Note:** Permissions are typically in the format `app_label | model_name | Can add model_name`, `app_label | model_name | Can change model_name`, etc. For our app, `app_label` is `service_manager`.

---

### 1. Group: `SystemAdmin`

*   **Description:** Full control over the system.
*   **Permissions:**
    *   Select **ALL** available permissions. This group should be able to do anything.
    *   This includes all permissions for `service_manager` models, `auth` models (User, Group), etc.

---

### 2. Group: `ServiceManager`

*   **Description:** Oversees workflow, manages cases, configurations, and views reports.
*   **Permissions (for `service_manager` models primarily):**
    *   **Brand:** `Can add brand`, `Can change brand`, `Can delete brand`, `Can view brand`
    *   **Case:** `Can add case`, `Can change case`, `Can delete case`, `Can view case` (and any custom case permissions like `can_approve_quotation` if defined)
    *   **CaseItem:** `Can add case item`, `Can change case item`, `Can delete case item`, `Can view case item`
    *   **CaseSparePartUsage:** `Can add case spare part usage`, `Can change case spare part usage`, `Can delete case spare part usage`, `Can view case spare part usage`
    *   **Client:** `Can add client`, `Can change client`, `Can delete client`, `Can view client`
    *   **EquipmentInstance:** `Can add equipment instance`, `Can change equipment instance`, `Can delete equipment instance`, `Can view equipment instance`
    *   **EquipmentModel:** `Can add equipment model`, `Can change equipment model`, `Can delete equipment model`, `Can view equipment model`
    *   **MalfunctionType:** `Can add malfunction type`, `Can change malfunction type`, `Can delete malfunction type`, `Can view malfunction type`
    *   **Region:** `Can add region`, `Can change region`, `Can delete region`, `Can view region`
    *   **SalesPerson:** `Can add sales person`, `Can change sales person`, `Can delete sales person`, `Can view sales person` (Also needs permissions for `auth | user` if managing users directly, but typically SystemAdmin does this).
    *   **SparePart:** `Can add spare part`, `Can change spare part`, `Can delete spare part`, `Can view spare part`
    *   **StorageLocation:** `Can add storage location`, `Can change storage location`, `Can delete storage location`, `Can view storage location`
    *   **Supplier:** `Can add supplier`, `Can change supplier`, `Can delete supplier`, `Can view supplier`
    *   Consider giving `view` permissions for `auth | user` and `auth | group` if they need to see user/group lists.

---

### 3. Group: `Receptionist`

*   **Description:** Handles case registration, client interaction, initial data entry.
*   **Permissions:**
    *   **Case:** `Can add case`, `Can change case` (potentially limited to certain fields/statuses if custom logic/forms enforce this later), `Can view case`
    *   **Client:** `Can add client`, `Can change client`, `Can view client`
    *   **EquipmentInstance:** `Can add equipment instance` (for new equipment during registration), `Can view equipment instance` (to select existing)
    *   **EquipmentModel:** `Can view equipment model` (to select models)
    *   **Brand:** `Can view brand`
    *   **Region:** `Can view region`
    *   **SalesPerson:** `Can view sales person` (to assign to cases)
    *   **MalfunctionType:** `Can view malfunction type`

---

### 4. Group: `Technician`

*   **Description:** Performs assessments, quotations (input), repairs, records spare parts.
*   **Permissions:**
    *   **Case:** `Can change case` (update status, notes), `Can view case`
    *   **CaseItem:** `Can view case item`, `Can change case item` (e.g., add repair notes - if field exists)
    *   **CaseSparePartUsage:** `Can add case spare part usage`, `Can change case spare part usage`, `Can view case spare part usage`
    *   **SparePart:** `Can view spare part` (to select parts)
    *   **EquipmentInstance:** `Can view equipment instance`
    *   **EquipmentModel:** `Can view equipment model`
    *   **MalfunctionType:** `Can view malfunction type`
    *   Optionally: `service_manager | case | can_create_quotation_details` (custom permission, if implemented)

---

### 5. Group: `WarehouseStaff`

*   **Description:** Manages receiving of physical items.
*   **Permissions:**
    *   **Case:** `Can change case` (specifically to update status to 'Receiving' and add `received_date`), `Can view case`
    *   **EquipmentInstance:** `Can view equipment instance`

---

### 6. Group: `QCStaff`

*   **Description:** Performs quality control checks.
*   **Permissions:**
    *   **Case:** `Can change case` (update status to 'QC' or revert), `Can view case`
    *   **CaseItem:** `Can view case item`
    *   **EquipmentInstance:** `Can view equipment instance`

---

## Step 4: Assigning Users to Groups (Example)

1.  Navigate to "Users" under **AUTHENTICATION AND AUTHORIZATION**.
2.  Select a user to edit.
3.  In the "Groups" section of the user's edit page, select the appropriate group(s) from the "Available groups" list and move them to the "Chosen groups" box using the arrows.
4.  Save the user.

**Important Considerations:**

*   **Granularity:** The permissions listed are a starting point. As the application develops, you might identify the need for more granular custom permissions (defined in model `Meta` classes).
*   **View-Level Checks:** These model-level permissions will be complemented by view-level checks (e.g., `@login_required`, `@permission_required`, or group membership checks) in `views.py` to control access to specific pages and actions.
*   **Testing:** Thoroughly test user access with different roles after setting up these permissions to ensure they work as expected.

This setup provides the foundation for role-based access control in the Service Management System.
