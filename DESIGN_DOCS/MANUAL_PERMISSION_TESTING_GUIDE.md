# Manual Permission Testing Guide

This guide outlines the steps to manually test the user permission setup in the Service Management System. It assumes that:
1.  The Django Groups (`SystemAdmin`, `ServiceManager`, `Receptionist`, `Technician`, `WarehouseStaff`, `QCStaff`) have been created in the Django Admin.
2.  The permissions have been assigned to these groups as detailed in `DESIGN_DOCS/ADMIN_SETUP_USER_ROLES.md`.
3.  The `@login_required` and `@permission_required` decorators, and conditional template logic, have been applied as per the development plan.

## I. Test User Setup

Create the following users in the Django Admin (`/admin/auth/user/add/`) and assign them to the specified groups. Ensure each user has a password.

1.  **TestUser_NoPerms:**
    *   Username: `noperms_user`
    *   Groups: None (or a group with absolutely no permissions related to `service_manager`)
    *   Active: Yes
    *   Staff status: No (unless needed to log into admin for some other reason, but for app testing, not required)
2.  **TestUser_Receptionist:**
    *   Username: `receptionist_user`
    *   Groups: `Receptionist`
    *   Active: Yes
3.  **TestUser_Technician:**
    *   Username: `technician_user`
    *   Groups: `Technician`
    *   Active: Yes
4.  **TestUser_ServiceManager:**
    *   Username: `manager_user`
    *   Groups: `ServiceManager`
    *   Active: Yes
5.  **TestUser_Admin (Superuser):**
    *   This is your existing superuser account used for Django Admin.

## II. Test Scenarios

For each scenario, log in as the specified test user and attempt the actions. Record if the actual outcome matches the expected outcome.

---

### Scenario A: Unauthenticated User

*   **Action:** Attempt to access any application URL (e.g., `/app/workplace/`, `/app/config/clients/`).
*   **Expected Outcome:** Redirected to the login page (`/accounts/login/?next=...`).

---

### Scenario B: `TestUser_NoPerms` (Authenticated, No Specific App Permissions)

1.  **Action:** Log in as `noperms_user`.
2.  **Action:** Attempt to access Workplace Dashboard (`/app/workplace/`).
    *   **Expected Outcome:** 403 Forbidden page (due to `@permission_required('service_manager.view_case')`).
3.  **Action:** Attempt to access Case Registration (`/app/workplace/cases/register/`).
    *   **Expected Outcome:** 403 Forbidden page.
4.  **Action:** Attempt to access Configuration Dashboard (`/app/config/`).
    *   **Expected Outcome:** 403 Forbidden page.
5.  **Action:** Attempt to access Client List (`/app/config/clients/`).
    *   **Expected Outcome:** 403 Forbidden page.

---

### Scenario C: `TestUser_Receptionist`

1.  **Action:** Log in as `receptionist_user`.
2.  **Workplace Dashboard (`/app/workplace/`):**
    *   **Expected UI:** "Register New Case" link/button should be VISIBLE.
    *   **Expected Access:** Access GRANTED.
3.  **Case Registration (`/app/workplace/cases/register/`):**
    *   **Expected Access:** Access GRANTED. Can submit new cases.
4.  **Case Detail (`/app/workplace/cases/<case_no>/` for an existing case):**
    *   **Expected Access:** Access GRANTED.
    *   **Expected UI (if case status is 'NEW'):** "Confirm Physical Receipt" button should be HIDDEN (Receptionist usually doesn't have `change_case` for this specific status update by default, unless explicitly given). *Correction based on `ADMIN_SETUP_USER_ROLES.md`: Receptionist does not have `change_case` by default for this specific action. WarehouseStaff or Manager would.*
5.  **Confirm Receiving (`/app/workplace/cases/<case_no>/confirm_receiving/` - attempt via URL or button if visible):**
    *   **Expected Access:** 403 Forbidden page (Receptionist lacks `change_case` for this).
6.  **Client List (`/app/config/clients/`):**
    *   **Expected Access:** Access GRANTED (Receptionist has `view_client`).
    *   **Expected UI:** "Add New Client" button VISIBLE. "Edit" links VISIBLE.
7.  **Client Add (`/app/config/clients/add/`):**
    *   **Expected Access:** Access GRANTED.
8.  **Brand List (`/app/config/brands/`):**
    *   **Expected Access:** Access GRANTED (Receptionist has `view_brand`).
    *   **Expected UI:** "Add New Brand" button HIDDEN. "Edit" links HIDDEN.
9.  **Brand Add (`/app/config/brands/add/` - attempt via URL):**
    *   **Expected Access:** 403 Forbidden page.
10. **Configuration Dashboard (`/app/config/`):**
    *   **Expected Access:** Access GRANTED (due to `view_client` permission).
    *   **Expected UI:** "Manage Clients" link VISIBLE. Other management links (Brands, Models, Instances) HIDDEN.

---

### Scenario D: `TestUser_Technician`

1.  **Action:** Log in as `technician_user`.
2.  **Workplace Dashboard (`/app/workplace/`):**
    *   **Expected UI:** "Register New Case" link/button should be HIDDEN.
    *   **Expected Access:** Access GRANTED (has `view_case`).
3.  **Case Registration (`/app/workplace/cases/register/` - attempt via URL):**
    *   **Expected Access:** 403 Forbidden page (Technician lacks `add_case`).
4.  **Case Detail (`/app/workplace/cases/<case_no>/` for an existing case):**
    *   **Expected Access:** Access GRANTED.
    *   **Expected UI (if case status is 'NEW'):** "Confirm Physical Receipt" button should be VISIBLE (Technician has `change_case` which is the permission for `case_confirm_receiving`). *Self-correction: The guide `ADMIN_SETUP_USER_ROLES.md` gives `change_case` to Technician. This implies they *could* do this action if no further business logic prevents it. This test verifies the permission itself.*
5.  **Confirm Receiving (`POST` to `/app/workplace/cases/<case_no>/confirm_receiving/`):**
    *   **Expected Access:** Action SUCCEEDS (if case is 'NEW').
6.  **Client List (`/app/config/clients/` - attempt via URL):**
    *   **Expected Access:** 403 Forbidden page (Technician lacks `view_client`).

---

### Scenario E: `TestUser_ServiceManager`

1.  **Action:** Log in as `manager_user`.
2.  **Workplace Dashboard (`/app/workplace/`):**
    *   **Expected UI:** "Register New Case" link/button VISIBLE.
    *   **Expected Access:** Access GRANTED.
3.  **All Case actions (Register, Detail, Confirm Receiving):**
    *   **Expected Access:** GRANTED.
4.  **Configuration Dashboard (`/app/config/`):**
    *   **Expected Access:** Access GRANTED.
    *   **Expected UI:** All management links (Clients, Brands, Models, Instances) VISIBLE.
5.  **All Configuration CRUD views (Client, Brand, Equipment Model, Equipment Instance - List, Add, Edit):**
    *   **Expected Access:** GRANTED for all.
    *   **Expected UI:** All "Add" and "Edit" buttons/links VISIBLE within these sections.

---

### Scenario F: `TestUser_Admin` (Superuser)

*   **Action:** Log in as the superuser.
*   **Expected Outcome:** Access GRANTED to ALL application URLs and actions. All UI elements for actions should be VISIBLE. Superusers bypass permission checks by default.

## III. Notes

*   Replace `<case_no>` with an actual case number from your test data.
*   Create test data (Clients, Brands, Models, Instances, Cases) as needed, preferably using a mix of user roles or the superuser via Django Admin.
*   If `raise_exception=True` was not used with `@permission_required`, the expected outcome for failed permission checks would be a redirect to the login page (even if already logged in), which is less user-friendly for this type of application.
*   This guide focuses on the permissions applied in the current development phase. More tests will be needed as new views and permissions are added.
```
