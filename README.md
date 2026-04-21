# 🚗 Automobile Sales & Logistics Analytics Platform

**Author:** Hardeep Bamrah  
**Role Focus:** Business Analyst | Commercial Analyst | BI Analyst  
**Domain:** Sales Performance • Logistics Risk • Customer Intelligence  
**Tools:** SQL Server • Python • Power BI • GitHub

---

## Executive Summary

This project was built to show how revenue reporting becomes more valuable when it is connected to operational reliability.

Instead of treating sales and logistics as separate reporting streams, the dashboard combines both to answer three practical business questions:
- **Where is revenue being generated?**
- **Where is revenue operationally exposed?**
- **What is driving that exposure by country, status, and product line?**

The result is an analytics workflow that moves from raw transactions to KPI-ready SQL models and finally to Power BI dashboards designed for executive monitoring and risk-based decision-making.

---

## What The Dashboard Shows

The dashboard is structured around four business views:

### 1. Operations Overview
This page gives leadership an immediate view of commercial performance and operating health.

It brings together:
- **Total Orders**
- **Total Revenue**
- **Shipping Reliability %**
- **Failure %**
- **Revenue at Risk**
- monthly trends for reliability and failure
- country comparison for Revenue at Risk %

**Business value:** this page helps answer whether revenue growth is being supported by reliable fulfilment or being undermined by failures, delays, and operational exposure.

### 2. Country Risk
This page compares countries using both scale and risk.

It includes:
- country-level order volume
- country-level revenue
- Shipping Reliability %
- Failure %
- Stuck %
- Revenue at Risk %
- a scatter analysis mapping **Failure % vs Revenue at Risk %**, sized by **Total Orders**

**Business value:** this makes it easier to identify which countries are not only large in revenue terms, but also vulnerable from an operations perspective.

### 3. Order Status
This page focuses on execution quality over time.

It includes:
- order status distribution by country
- backlog orders trend over time
- time and country filters

**Business value:** this helps detect whether unresolved or delayed orders are building up before they create a visible revenue problem.

### 4. Product / Revenue at Risk
This page breaks risk down to product line level.

It includes:
- Product Orders
- Allocated Revenue
- Allocated Revenue at Risk %
- Product High Risk % by product line
- Allocated Revenue at Risk % by product line
- Allocated Revenue by product line

**Business value:** this helps prioritise product lines that combine commercial importance with higher operational exposure.

---

## Key Reporting Logic

The dashboard is not built on isolated visuals. It is driven by reusable KPI logic modelled upstream in SQL and exposed through Power BI measures.

Key metrics used across the report include:
- **Total Orders**
- **Total Revenue**
- **Shipping Reliability %**
- **Failure %**
- **Stuck %**
- **Revenue at Risk**
- **Revenue at Risk %**
- **Backlog Orders**
- **Allocated Revenue**
- **Allocated Revenue at Risk %**

This structure allows the report to move from high-level monitoring to root-cause exploration across country, order status, and product line dimensions.

---

## What Caused What In This Project

The project was designed to make cause-and-effect style analysis easier for decision-makers.

Examples of the reporting logic include:
- higher **Failure %** contributes to higher **Revenue at Risk %**
- unresolved operational states increase **Backlog Orders** and can signal fulfilment pressure
- countries with high order volumes and weak reliability are more likely to create larger revenue exposure
- product lines with high allocated revenue and high risk percentages deserve greater operational attention

This means the report does more than show performance. It helps explain **why certain parts of the business are more exposed than others**.

---

## Why This Matters For A Business

A revenue dashboard on its own can hide operational problems.
A logistics dashboard on its own can miss commercial importance.

This project combines both views so teams can:
- spot where commercial performance is vulnerable to fulfilment issues
- prioritise countries where both scale and risk are high
- monitor backlog behaviour before it becomes a larger service problem
- identify product lines where operational issues are putting meaningful revenue at risk

---

## Dashboard Preview

### Operations Overview
![Executive Dashboard](screenshots/powerbi_executive_dashboard.png)

### Country Risk View
![Country Risk](screenshots/country_risk_dashboard.png)

### Python Customer Analysis
![RFM Segmentation](screenshots/rfm_revenue_contribution.png)

---

## Architecture

```text
Raw Transaction Data
        ↓
Bronze Layer (raw structured tables)
        ↓
Silver Layer (cleaned and standardised data)
        ↓
Gold Layer (order, country, and product-line KPI views)
        ↓
Power BI Dashboard Layer
        ↓
Business Monitoring and Risk Prioritisation
```

---

## Repository Structure

```text
automobile-sales-logistics/
│
├── Data/                # Source or prepared datasets
├── python/              # EDA, segmentation, clustering, validation
├── SQL/                 # Bronze → Silver → Gold SQL modelling logic
├── PowerBI/             # Power BI dashboard file and notes
├── streamlit/           # Optional app layer
├── screenshots/         # Dashboard preview images
├── app.py               # Streamlit entry point
├── requirements.txt     # Project dependencies
└── README.md
```

---

## Tech Stack

- **SQL Server** — cleaning, modelling, KPI layer
- **Python** — customer and behavioural analysis
- **Power BI** — executive dashboarding and business reporting
- **GitHub** — project versioning and presentation

---

## How To Review This Project

1. Start with the dashboard screenshots for a quick visual overview  
2. Open the **PowerBI** folder to review the dashboard documentation  
3. Review the **SQL** layer to understand how KPI logic is built  
4. Explore the **Python** work for customer and risk-related analysis  
5. Use the README as the business narrative tying all pieces together

---

## Final Positioning

This project demonstrates how a Business Analyst / BI Analyst can connect transactional sales data, operational performance, and product-level exposure into a single reporting framework.

The main value of the work is not only showing results, but showing **where risk sits, what is driving it, and how decision-makers can act on it**.

---

## License

MIT License