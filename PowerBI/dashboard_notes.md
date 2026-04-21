# Power BI Dashboard Overview

## Dashboard File

`Automobile_Sales_Logistics_Dashboard.pbix`

This Power BI dashboard combines commercial performance and operational risk into a single reporting layer for decision-making.

---

## Purpose

The dashboard is designed to help answer business questions such as:
- Which countries are driving the highest operational risk?
- How much revenue is exposed to fulfilment issues?
- Are backlog and failure trends increasing over time?
- Which product lines contribute most to revenue at risk?

---

## Report Pages

### 1. Operations Overview
Provides a high-level snapshot of business performance and operational health.

Includes:
- Total Orders
- Total Revenue
- Shipping Reliability %
- Failure %
- Revenue at Risk
- Trend views over time

### 2. Country Risk
Compares countries across revenue, order volume, and operational exposure.

Includes:
- Country-level KPI comparison
- Failure %, Stuck %, and Revenue at Risk %
- Scatter view for comparative country risk analysis

### 3. Order Status
Tracks fulfilment status and backlog behaviour over time.

Includes:
- Order status distribution
- Backlog trend monitoring
- Country and time-based filtering

### 4. Product / Revenue at Risk
Highlights which product lines contribute most to operational exposure.

Includes:
- Product-level risk metrics
- Allocated revenue analysis
- Revenue at Risk % by product line

---

## KPI Definitions

- **Total Orders**: Number of distinct orders in the filtered context
- **Total Revenue**: Total sales value in the filtered context
- **Shipping Reliability %**: Share of shipped or operationally successful orders
- **Failure %**: Share of failed orders
- **Stuck %**: Share of unresolved or delayed orders
- **Revenue at Risk**: Revenue associated with operationally risky orders
- **Revenue at Risk %**: Percentage of revenue exposed to risk
- **Backlog Orders**: Orders still pending fulfilment
- **Allocated Revenue**: Revenue distributed to product line level using allocation logic
- **Allocated Revenue at Risk %**: Percentage of allocated revenue exposed to risk

---

## Folder Contents

- `Automobile_Sales_Logistics_Dashboard.pbix` — main Power BI dashboard file
- `dashboard_notes.md` — dashboard overview and KPI definitions

---

## Summary

This dashboard was built to connect revenue performance, operational reliability, and product-level exposure in one decision-support view.
It serves as the reporting layer of the broader SQL, Python, and Power BI analytics workflow used in this project.
