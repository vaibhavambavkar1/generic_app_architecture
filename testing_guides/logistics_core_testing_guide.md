# Logistics Core (`logistics_core`) Testing Guide

## 1. Overview
This document outlines the testing suite for the **Logistics Core** app within the Generic Logistics Management System (LMS). This app serves as the geographical and operational backbone for the LMS, providing the master data models used by the Courier, Freight, and 3PL modules.

## 2. Prerequisites & Setup
The `logistics_core` module consists exclusively of master data models, so there are fewer external application dependencies compared to transactional apps like Freight or Courier. 

- **Organization:** A valid Organization record is still required by the central ERP framework.
- **Database Backend:** The tests are designed to execute against the local test database instance via Docker.

To run the tests without interactive database destruction prompts:
```bash
docker exec erp_framework_web_dev python manage.py test logistics_core --noinput
```

## 3. Core Functionality Tested

### 3.1. Geography & Zoning
- **Zone Creation:** Verifies that geographical bounding zones (e.g., "North America", "Local Region A") can be instantiated and retain active states.
- **Location Constraints:** Evaluates the `Location` model. Confirms that specific location types (`HUB`, `PORT`, `AIRPORT`, `CUSTOMER`) correctly associate with an overarching `Zone` using Foreign Keys, and validates their string representations.

### 3.2. Routing Topologies
- **Route Definitions:** Verifies the `Route` model correctly maps an Origin `Location` to a Destination `Location`. Tests ensure `distance_km` and `estimated_hours` are properly saved.
- **Unique Path Constraints:** Enforces database-level uniqueness. Tests assert that an `IntegrityError` is thrown if attempting to create duplicate identical `Route` records possessing the exact same Origin and Destination pair.

### 3.3. Service Parameters
- **Service Types:** Validates that `ServiceType` configurations (e.g., "Express Overnight") correctly map variables like `guaranteed_hours` which dictates SLAs downstream for waybill delivery calculations.

## 4. Notes for Expanding Tests
Because `logistics_core` models are the foundation of the architecture, any schema adjustments (such as adding new fields to `Location`) require corresponding updates to this testing guide and test file to guarantee dependent modules (like `freight`) do not fail from missing expected fields.
