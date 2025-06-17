# Key Workflows for Service Management System

This document outlines the primary user workflows and conceptual processes within the Django-based Service Management System.

## 1. Core Case Workflow

The system manages the entire lifecycle of a service case through a series of statuses. Each status typically corresponds to a specific tab or queue in the 'WORKPLACE' module.

**Initial Case Statuses (defined in `Case` model choices):**
*   `NEW`: New Registration
*   `RECEIVING`: Receiving
*   `QUOTATION`: Waiting for Quotation
*   `REPAIRING`: Repairing
*   `QC`: QC (Quality Control)
*   `DELIVERY`: Delivery
*   `CLOSED`: Follow-up & Closing Case

**Workflow Steps:**

**A. Registration (`WORKPLACE -> Registration`)**
    *   **User:** Typically a receptionist or front-desk staff.
    *   **Action:**
        1.  Navigates to the 'Case Registration' form.
        2.  **Client Information:**
            *   Searches for an existing client. If found, client details (contact person, phone) are auto-filled.
            *   If not found, the user might be prompted to register the new client first (via `CONFIGURATION -> Setup Client` or a quick-add feature).
        3.  **Equipment Information (for each item needing service):**
            *   **Option 1: Scan Serial No.** (Conceptual - implies barcode scanner integration or quick serial input)
                *   System attempts to find `EquipmentInstance` by `serial_no`.
                *   If found, model and client ownership (if any) might be displayed.
            *   **Option 2: Select Existing Equipment:**
                *   User searches/selects from a list of `EquipmentInstance` records already associated with the chosen `Client`.
            *   **Option 3: Register New Equipment:**
                *   User is presented with fields to create a new `EquipmentInstance` (linking to an `EquipmentModel`). This might open a modal or a separate section in the form.
            *   For each equipment item, user inputs `MalfunctionDescription` and optionally selects a `MalfunctionType`.
        4.  Enters other relevant case details: `ward_clinic_department`, `sales_in_charge`, `reference_case_no`.
        5.  Submits the form.
    *   **System Response:**
        *   A new `Case` record is created with `status = 'NEW'`.
        *   Associated `CaseItem` records are created for each piece of equipment.
        *   The case appears in the "New Registration" queue/tab.
    *   **Next Status:** `RECEIVING` (manual trigger by staff)

**B. Receiving (`WORKPLACE -> Receiving` tab/queue)**
    *   **User:** Warehouse or receiving staff.
    *   **Action:**
        1.  Views cases with `status = 'NEW'`.
        2.  Locates the specific case.
        3.  Physically receives the equipment from the client.
        4.  Confirms receipt in the system (e.g., clicks a "Confirm Receipt" button on the case detail page).
    *   **System Response:**
        *   `Case.status` changes from `NEW` to `RECEIVING`.
        *   `Case.received_date` is populated.
        *   The case moves to the "Waiting for Quotation" queue/tab.
    *   **Next Status:** `QUOTATION`

**C. Quotation (`WORKPLACE -> Quotation` tab/queue)**
    *   **User:** Technician or service advisor.
    *   **Action:**
        1.  Views cases with `status = 'RECEIVING'`.
        2.  Opens a case to assess the required repairs for each `CaseItem`.
        3.  Determines necessary `SparePart`s and labor.
        4.  Generates a quotation (details of this process, like adding line items for parts and labor, are part of a more detailed quotation feature design).
        5.  Submits the quotation for internal approval or directly to the client (depending on business rules).
        6.  Once the quotation is approved (by client/manager), the user updates the case.
    *   **System Response:**
        *   `Case.status` changes from `RECEIVING` to `QUOTATION` (or a sub-status like 'Quotation Pending Approval', then to 'Quotation Approved'). For simplicity, we'll assume it moves to `QUOTATION` when ready for repair after approval.
        *   `Case.quotation_date` might be populated.
        *   The case moves to the "Waiting for Repair" queue/tab.
    *   **Next Status:** `REPAIRING`

**D. Repairing (`WORKPLACE -> Repairing` tab/queue)**
    *   **User:** Technician.
    *   **Action:**
        1.  Views cases with `status = 'QUOTATION'` (or an equivalent like 'Approved for Repair').
        2.  Picks up a case.
        3.  Performs the repair work on the `CaseItem`(s).
        4.  Records `SparePart`s used via `CaseSparePartUsage` for each `CaseItem`.
        5.  Updates repair notes or logs.
        6.  Marks the repair as complete.
    *   **System Response:**
        *   `Case.status` changes from `QUOTATION` to `REPAIRING`.
        *   `Case.repair_start_date` might be populated when work begins.
        *   When repair is done, status changes to `QC`.
        *   The case moves to the "QC" queue/tab.
    *   **Next Status:** `QC`

**E. QC (Quality Control) (`WORKPLACE -> QC` tab/queue)**
    *   **User:** QC personnel or a different technician.
    *   **Action:**
        1.  Views cases with `status = 'REPAIRING'` (or a sub-status 'Repair Complete, Pending QC').
        2.  Inspects the repaired equipment.
        3.  If QC passes: Marks QC as passed.
        4.  If QC fails: Reverts the case status (e.g., back to `REPAIRING` or a specific 'QC Failed' status) with notes for re-work.
    *   **System Response (on pass):**
        *   `Case.status` changes from `REPAIRING` to `QC`.
        *   `Case.qc_date` is populated.
        *   The case moves to the "Delivery" queue/tab.
    *   **Next Status:** `DELIVERY`

**F. Delivery (`WORKPLACE -> Delivery` tab/queue)**
    *   **User:** Dispatch or front-desk staff.
    *   **Action:**
        1.  Views cases with `status = 'QC'`.
        2.  Arranges for the equipment to be returned to the client.
        3.  Confirms the equipment has been delivered/picked up by the client.
    *   **System Response:**
        *   `Case.status` changes from `QC` to `DELIVERY`.
        *   `Case.delivery_date` is populated.
        *   The case moves to the "Follow-up & Closing Case" queue/tab.
    *   **Next Status:** `CLOSED`

**G. Follow-up & Closing Case (`WORKPLACE -> Follow-up & Closing Case` tab/queue)**
    *   **User:** Service advisor or administrative staff.
    *   **Action:**
        1.  Views cases with `status = 'DELIVERY'`.
        2.  Performs any necessary follow-up with the client (e.g., satisfaction check).
        3.  Completes any final paperwork or system entries.
        4.  Formally closes the case.
    *   **System Response:**
        *   `Case.status` changes from `DELIVERY` to `CLOSED`.
        *   `Case.closed_date` is populated.
        *   The case is now considered complete and archived (still searchable but removed from active queues).

## 2. Status Queues (Sidebar in WORKPLACE)

*   The sidebar in the 'WORKPLACE' module is envisioned to display a list of statuses (New Registration, Waiting for Quotation, etc.).
*   Next to each status, a count of active cases in that particular status will be shown.
*   Clicking on a status in the sidebar will filter the main content area to display a list of only those cases.
*   This provides an at-a-glance overview of the workload in different stages of the repair process.

## 3. Configuration Module Workflows (Admin Panel)

Workflows in the 'CONFIGURATION' module are generally simpler, involving CRUD (Create, Read, Update, Delete) operations for master data.

**Example: Setup Client**
    1.  **User:** Administrator or authorized staff.
    2.  **Action:**
        *   Navigates to `CONFIGURATION -> Setup Client`.
        *   Views a list of existing clients.
        *   Clicks "Add New Client".
        *   Fills in the `ClientForm` (name, address, region, etc.).
        *   Saves the form.
    3.  **System Response:**
        *   New `Client` record is created.
        *   The list is updated.
    *   Similar workflows apply to `Setup Equipment Model`, `Setup Spare Part`, `Setup Brand`, `Setup Region`, etc., each using their respective Django forms and models.

**User Management (`Setup User / Setup Profile`)**
*   Leverages Django's built-in User model.
*   The `SalesPerson` model extends the User model with a `OneToOneField`.
*   Full user creation and permission management will primarily be handled via the Django Admin interface (`/admin/`).
*   Simplified forms (`SalesPersonForm`) might be provided in the `CONFIGURATION` module for creating `SalesPerson` profiles, potentially creating the `User` record simultaneously or linking to an existing one.

This conceptual outline will guide the implementation of views, templates, and business logic in the Django application.
