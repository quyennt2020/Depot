# Manual Admin Customization Test Guide

This guide outlines steps to manually review and test the customizations applied to the Django Admin interface for the Service Management System.

**Prerequisites:**
*   A superuser account exists.
*   The Django development server is running.
*   Some sample data has been created for models like `Region`, `Client`, `Brand`, `EquipmentModel`, `EquipmentInstance`, `Case` (with `CaseItem`s), and `SparePart` to effectively test listings, searches, filters, and inlines. This data can be created via the Django Admin itself or programmatically.

## I. General Admin Interface Checks

1.  **Login:** Log in to the Django Admin (`/admin/`) as a superuser.
2.  **App Section:** Verify that a section for "SERVICE_MANAGER" (or the app's display name) is visible on the admin dashboard.
3.  **Model List:** Confirm that all registered models are listed under the "SERVICE_MANAGER" section:
    *   Brands, Cases, Case Items, Case Spare Part Usages, Clients, Equipment Instances, Equipment Models, Malfunction Types, Regions, Sales People, Spare Parts, Storage Locations, Suppliers.

## II. Model-Specific Customization Tests

For each model admin customized (`Client`, `Brand`, `EquipmentModel`, `EquipmentInstance`, `Case`, `SparePart`), perform the following checks:

---

### A. Client Admin (`service_manager.Client`)

1.  **Navigate:** Click on "Clients".
2.  **`list_display` Verification:**
    *   **Expected Columns:** The list view should display columns for: `NAME`, `REGION`, `CONTACT PERSON`, `PHONE`.
    *   Verify data appears correctly in these columns for any existing client records.
3.  **`search_fields` Test:**
    *   Use the search bar at the top of the list.
    *   **Test 1:** Search by a known client name. Expected: Only clients matching the name should appear.
    *   **Test 2:** Search by a known contact person's name. Expected: Only clients matching that contact person should appear.
4.  **`list_filter` Test:**
    *   Locate the filter sidebar (usually on the right).
    *   **Expected Filter:** "By region".
    *   Test filtering by selecting a region (if multiple regions with clients exist). Expected: List updates to show only clients from the selected region.
5.  **Inlines (`EquipmentInstanceInlineForClient`) Test:**
    *   Click on an existing client to go to its change (edit) page.
    *   **Expected Section:** An inline section for "Equipment Instances" (or similar title based on `EquipmentInstance` verbose name) should be visible.
    *   **Expected Content:** It should list equipment instances linked to this client.
    *   **Expected Readonly Fields:** Fields like `SERIAL NO`, `MODEL`, `PURCHASE DATE`, `NOTES` within this inline section should be read-only.
    *   **Expected Behavior:** `extra` was 0 and `can_delete` was `False`, so no "Add another..." link and no delete checkboxes should be present for these inlines by default.

---

### B. Brand Admin (`service_manager.Brand`)

1.  **Navigate:** Click on "Brands".
2.  **`list_display` Verification:**
    *   **Expected Columns:** `NAME`.
    *   (Search and filter were not added to BrandAdmin in this phase, so no specific tests for those here).

---

### C. Equipment Model Admin (`service_manager.EquipmentModel`)

1.  **Navigate:** Click on "Equipment models".
2.  **`list_display` Verification:**
    *   **Expected Columns:** `NAME`, `BRAND`, `DESCRIPTION`.
3.  **`search_fields` Test:**
    *   **Test 1:** Search by a known model name.
    *   **Test 2:** Search by a known brand name associated with a model (e.g., if "Dell" is a brand, search "Dell").
4.  **`list_filter` Test:**
    *   **Expected Filter:** "By brand".
    *   Test filtering by selecting a brand.
5.  **Inlines (`EquipmentInstanceInlineForModel`) Test:**
    *   Click on an existing equipment model.
    *   **Expected Section:** An inline section for "Equipment Instances".
    *   **Expected Content:** Lists equipment instances of this model type.
    *   **Expected Readonly Fields:** `SERIAL NO`, `CURRENT CLIENT`, `PURCHASE DATE`, `NOTES` within the inline should be read-only.
    *   **Expected Behavior:** `extra = 0`, `can_delete = False`.

---

### D. Equipment Instance Admin (`service_manager.EquipmentInstance`)

1.  **Navigate:** Click on "Equipment instances".
2.  **`list_display` Verification:**
    *   **Expected Columns:** `SERIAL NO`, `MODEL`, `CURRENT CLIENT`, `PURCHASE DATE`.
3.  **`search_fields` Test:**
    *   **Test 1:** Search by a known serial number.
    *   **Test 2:** Search by a known model name.
    *   **Test 3:** Search by a known client name associated with an instance.
4.  **`list_filter` Test:**
    *   **Expected Filters:** "By model brand", "By model".
    *   Test filtering by these options.
    *   Also check "By purchase date" filter (added by worker in previous step).

---

### E. Case Admin (`service_manager.Case`)

1.  **Navigate:** Click on "Cases".
2.  **`list_display` Verification:**
    *   **Expected Columns:** `CASE NO`, `CLIENT`, `STATUS`, `REGISTRATION DATE`, `SALES IN CHARGE`.
3.  **`search_fields` Test:**
    *   **Test 1:** Search by a known case number.
    *   **Test 2:** Search by a known client name associated with a case.
    *   **Test 3:** Search by a serial number of an equipment item linked to a case (this tests `items__equipment_instance__serial_no`).
4.  **`list_filter` Test:**
    *   **Expected Filters:** "By status", "By client region", "By registration date".
    *   Test filtering, especially the date hierarchy for `registration_date`.
5.  **Inlines (`CaseItemInline`) Test:**
    *   Click on an existing case to go to its change page.
    *   **Expected Section:** An inline section for "Case Items".
    *   **Expected Fields:** `EQUIPMENT INSTANCE`, `MALFUNCTION DESCRIPTION`, `MALFUNCTION TYPE`, `NOTES` should be visible and editable.
    *   **Expected Behavior:** `extra = 1` should provide one empty row for adding a new case item. Test adding a new item.
6.  **`fieldsets` and `readonly_fields` Test:**
    *   On the case change page:
        *   **Verify Sections:** Confirm fields are grouped into: "Case Core Information", "Contact Overrides" (collapsible), "Location & Reference", "Case Timestamps (Read-Only)" (collapsible).
        *   **Test Collapsible:** Click on the title of "Contact Overrides" and "Case Timestamps" to ensure they expand/collapse.
        *   **Verify Readonly Fields:** Confirm that fields under "Case Timestamps" (`registration_date`, `received_date`, etc.) are displayed but not editable.

---

### F. Spare Part Admin (`service_manager.SparePart`)

1.  **Navigate:** Click on "Spare parts".
2.  **`list_display` Verification:**
    *   **Expected Columns:** `PART NO`, `NAME`, `BRAND`, `UNIT PRICE`, `STOCK QUANTITY`.
3.  **`search_fields` Test:**
    *   **Test 1:** Search by part number.
    *   **Test 2:** Search by name.
4.  **`list_filter` Test:**
    *   **Expected Filter:** "By brand".
    *   Test filtering by brand.

---

## III. General Usability Notes

*   Are the column headers clear?
*   Is the search responsive?
*   Do filters apply correctly?
*   Is the layout of add/change pages (especially for `Case`) logical and easy to navigate?
*   Are there any broken links or unexpected errors encountered during navigation or data manipulation within the admin?

This guide should help ensure that the Django Admin customizations provide a good experience for administrators.
```
