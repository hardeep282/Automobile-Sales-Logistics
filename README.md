#***🚗 Automobile Sales & Logistics Intelligence Platform***

**_Author: Hardeep Bamrah_**

Role Focus: Business Analyst | Data Analyst | BI Analyst
Domain: Sales Performance • Logistics Risk • Customer Intelligence

📌 **_Project Overview_**

This project delivers an end-to-end sales and logistics intelligence solution that combines customer value analysis, operational risk monitoring, and revenue performance using Python, SQL, and Power BI.

The objective is not just to calculate metrics, but to connect customer behaviour, fulfilment reliability, and revenue risk into a single analytical framework that supports operational and commercial decision-making.

🎯 Business Objectives

- Identify high-revenue customers and products exposed to logistics risk

- Measure operational reliability and failure patterns across countries and time

- Understand revenue concentration and risk exposure

- Support retention, logistics optimisation, and revenue protection     decisions

- Provide executive-ready dashboards backed by robust KPI logic

📂 **_Dataset Overview_**

The analysis is based on historical automobile sales transactions and was transformed into customer- and order-level analytical datasets, containing:

- Order dates, status, and fulfilment outcomes

- Revenue and pricing (MSRP-based)

- Customer purchase behaviour (frequency, recency, value)

- Product and country attributes

🏗️ **_Analytics Style_**

The solution follows a layered analytics approach, mirroring real-world data workflows.

🟦 **_Python — Exploratory & Advanced Analytics Layer_**

Used for exploration, validation, and behavioural intelligence before productionising KPIs.

Key work includes:

- RFM segmentation (Recency, Frequency, Monetary)

- Customer value tiering (High / Mid / Low)

- Shipping reliability scoring at customer level

- Composite Customer Value × Shipping Risk segmentation

- K-Means clustering to identify behavioural personas

- Regression analysis to understand revenue drivers

Python answers:
“What patterns exist, and which KPIs actually matter?”

🟨 **_SQL — Data Modeling & KPI Engine_**

SQL acts as the single source of truth for business logic and KPIs.

A Bronze → Silver → Gold structure was used:

- Bronze: Raw transactional data

- Silver: Cleaned, standardised, business-ready tables

- Gold: Aggregated KPI views and operational intelligence

**Core SQL KPIs**

- Total Revenue

- Total Orders

- Revenue per Order

- Gross Profit (Proxy)

- Order Failure Rate

- High-Risk Order Percentage

- Revenue Concentration

- Country & Month-based Logistics Status

SQL answers:
“What numbers are officially correct and reusable?”

🟩 **_Power BI — Decision & Storytelling Layer_**

Power BI dashboards were built on top of the SQL Gold layer to provide clear, executive-level visibility without exposing analytical complexity.

Power BI answers:
“So what should the business do?”

📊 **_Power BI Dashboards_**


Page 1️⃣ – **Executive Operations Overview**

- Total Revenue & Orders

- Revenue per Order

- Failure Rate & High-Risk Order %

- Overall operational health snapshot

Page 2️⃣ – **_Country Risk Deep-Dive_**

- Country-wise logistics risk

- Failure and high-risk order patterns

- Geographic exposure analysis

Page 3️⃣ – Order Status & Backlog Monitoring

Order status distribution

Backlog and delay monitoring

Early warning indicators for fulfilment issues

Page 4️⃣ – Product / Revenue at Risk Analysis

Revenue concentration

Products contributing disproportionately to risk

Identification of revenue exposed to logistics failures

💡 Key Business Insights

A small share of orders and products account for a disproportionate share of operational risk

Logistics failures tend to impact customer stability before revenue declines

Revenue is driven more by order frequency and product diversity than order value alone

High-value customers with low shipping reliability represent critical retention risk

✅ Business Impact

Targeted retention strategies for high-value, high-risk customers

Prioritised logistics audits for revenue-critical regions

Clear visibility into revenue vs fulfilment trade-offs

Decision-ready insights without exposing technical complexity

🛠️ Tech Stack

SQL Server — Data modeling & KPI engine

Python — Pandas, NumPy, Scikit-Learn (EDA, segmentation, validation)

Power BI — Executive dashboards & operational monitoring

Git & GitHub — Version control & portfolio presentation

```
automobile-sales-logistics/
│
├── Python/        # EDA, segmentation, clustering, regression
├── sql/           # Bronze → Silver → Gold KPI logic
├── powerbi/       # Executive dashboards
├── streamlit/     # (Optional) interactive app layer
├── screenshots/   # Dashboard images
└── README.md

```


🧠 Final Note

This project demonstrates a full analyst workflow:

From exploration → validation → production KPIs

From raw data → structured logic → executive decisions

It reflects how analytics is applied in real organisations, not just how tools are used.

📄 License

MIT License