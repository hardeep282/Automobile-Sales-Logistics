# Power BI Dashboard Notes

## Dashboard File

**Recommended file name:** `Automobile_Sales_Logistics_Dashboard.pbix`

This dashboard is designed to combine commercial performance and operational risk into one decision-support view.

---

## Report Pages

### 1. Operations Overview
Purpose:
- Provide an executive snapshot of revenue, order volume, shipping reliability, failure rate, and revenue at risk.

Key visuals:
- KPI cards for Total Orders, Total Revenue, Shipping Reliability %, Failure %, Revenue at Risk
- Trend charts for Shipping Reliability % and Failure % over time
- Country comparison for Revenue at Risk %

Suggested business interpretation:
- This page helps leadership quickly understand whether revenue performance is supported by stable operations.
- It highlights where operational problems may start affecting commercial outcomes.

Recommended polish:
- Add clear visual titles
- Keep KPI formatting consistent
- Add one more KPI such as Revenue per Order or High-Risk Order %

---

### 2. Country Risk
Purpose:
- Compare countries on order volume, revenue, operational reliability, and risk exposure.

Key visuals:
- Matrix / pivot view by country
- Scatter chart with Failure % vs Revenue at Risk %, sized by Total Orders
- Country and time slicers

Suggested business interpretation:
- This page identifies which countries require operational intervention.
- It supports prioritisation by combining scale, failure rate, and revenue exposure.

Recommended polish:
- Apply conditional formatting to Failure %, Stuck %, and Revenue at Risk %
- Ensure the scatter chart has a clear title and axis labels

---

### 3. Order Status
Purpose:
- Monitor fulfilment patterns and backlog behaviour over time.

Key visuals:
- Order status distribution by country
- Backlog Orders trend over time
- Time and country slicers

Suggested business interpretation:
- This page acts as an early-warning operational view.
- It helps identify whether backlog and non-shipped statuses are increasing before revenue impact becomes visible.

Recommended polish:
- Add one more supporting visual, such as stuck/failure status comparison by month
- Make titles highly explicit for interview presentation

---

### 4. Product / Revenue at Risk
Purpose:
- Show which product lines contribute most to high-risk exposure and revenue at risk.

Key visuals:
- KPI cards for Product Orders, Allocated Revenue, Allocated Revenue at Risk %
- Bar charts for Product High Risk %, Allocated Revenue at Risk %, and Allocated Revenue by product line
- Product line and time slicers

Suggested business interpretation:
- This page helps identify where operational issues are concentrated at the product-line level.
- It supports prioritisation of product categories that combine high exposure with meaningful revenue contribution.

Recommended polish:
- Rename any temporary/internal-sounding measures such as `Product High Risk % Fresh`
- Sort bars intentionally and use clean number formatting

---

## KPI Definitions

- **Total Orders**: Number of distinct orders in the filtered context
- **Total Revenue**: Total sales value in the filtered context
- **Shipping Reliability %**: Share of shipped or operationally successful orders
- **Failure %**: Share of cancelled/disputed/failed orders
- **Stuck %**: Share of orders in delayed, on-hold, or unresolved states
- **Revenue at Risk**: Revenue linked to operationally risky orders
- **Revenue at Risk %**: Share of revenue exposed to operational risk
- **Backlog Orders**: Orders still pending fulfilment action
- **Allocated Revenue**: Revenue distributed to product-line level using allocation logic
- **Allocated Revenue at Risk %**: Share of allocated product-line revenue exposed to risk

---

## Recommended Final Improvements

1. Add strong visual titles to every chart and card section
2. Keep number formatting consistent across currency, counts, and percentages
3. Use conditional formatting on matrix values for risk metrics
4. Remove temporary naming from measures
5. Add drill-through or tooltip pages if needed for deeper analysis
6. Ensure alignment, spacing, and font sizes are consistent across all pages

---

## Interview Talking Points

Use this project to explain:
- how you linked revenue performance with operational reliability
- why revenue-only dashboards can hide fulfilment risks
- how country and product-level analysis supports prioritisation
- how Power BI acts as the decision layer on top of SQL KPI logic
- how the dashboard supports both executive reporting and root-cause analysis

---

## Suggested Recruiter Summary

This Power BI dashboard translates sales and logistics data into an executive reporting layer that combines revenue visibility, operational risk, backlog monitoring, and product-level exposure analysis.
