# Generic Store Management — Testing Guide

This guide provides a step-by-step walkthrough to test the **Generic Store Management** module. This module acts as the core product and catalog foundation for Point-of-Sale (POS), Retail, and Warehouse operations.

## Prerequisites
Ensure the application is running via Docker:
```bash
docker compose up -d
```
All URLs referenced below assume the application is accessible at `http://localhost:8000`.

---

## Phase 1: Foundational Taxonomy Configuration

Before creating products, you must set up the foundational units, taxes, and brands.

1. **Create a Unit of Measure (UOM)**
   - Navigate to your Django Admin dashboard: [http://localhost:8000/admin/](http://localhost:8000/admin/)
   - Go to **Generic_Store_Mgmt** > **Units of Measure** and click **Add Unit of Measure**.
   - **Name**: `Pieces`
   - **Code**: `PCS`
   - Click **Save and add another**.
   - Create another one: **Name**: `Kilograms`, **Code**: `KG`.

2. **Create a Tax Bracket**
   - Go to **Generic_Store_Mgmt** > **Tax Brackets** and click **Add Tax Bracket**.
   - **Name**: `Standard GST 18%`
   - **CGST Rate**: `9.00`
   - **SGST Rate**: `9.00`
   - **IGST Rate**: `18.00`
   - Click **Save**.

3. **Create Categories & Brands**
   - Navigate to **Categories**. Add a parent category (e.g., `Electronics`) and a sub-category (e.g., `Laptops` with `Electronics` as the parent).
   - Navigate to **Brands**. Add a brand (e.g., `TechCorp`).

---

## Phase 2: Product Catalog & Master Data

1. **Create a Product**
   - Go to **Generic_Store_Mgmt** > **Products** and click **Add Product**.
   - **Name**: `TechCorp ProBook 15`
   - **Product Type**: `Goods`
   - **Category**: `Laptops`
   - **Brand**: `TechCorp`
   - **UOM**: `Pieces (PCS)`
   - **Tax Bracket**: `Standard GST 18%`
   - **Purchase Price**: `800.00`
   - **Selling Price**: `1200.00`
   - **MRP**: `1499.99`
   - **Manage Stock**: Checked
   - *Note: Leave SKU and Barcode blank; the system will automatically auto-generate a unique `PROD-...` SKU on save.*
   - Click **Save**.

2. **Verify SKU Generation**
   - Open the newly created product and verify that the `SKU` field was automatically populated by the backend signal override.

---

## Phase 3: Multi-Tier Pricing Lists

Different channels (e.g., Retail vs Wholesale) may require different pricing models for the same product.

1. **Create a Price List**
   - Go to **Generic_Store_Mgmt** > **Price Lists** and click **Add Price List**.
   - **Name**: `B2B Wholesale Tier 1`
   - Click **Save**.

2. **Add Price List Items (Inline)**
   - Open the `B2B Wholesale Tier 1` Price List.
   - In the **Items** inline form at the bottom, select the `TechCorp ProBook 15` product.
   - Override the default selling price by setting a custom **Rate** (e.g., `950.00`).
   - Click **Save**.
   
3. **Validation Test**
   - Attempt to add a second inline item for the *exact same* product (`TechCorp ProBook 15`) to the *same* price list with a different rate. 
   - Click **Save**. 
   - The system should safely reject this due to the `unique_together` constraint enforcing only one specific rate per product per price list.
