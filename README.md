**🚗 Automobile Sales & Logistics Analytics Platform**

**Author: Hardeep Bamrah**

Role Focus: Business Analyst | Commercial Analyst | BI Analyst 

Domain: Sales Performance • Logistics Risk • Customer Intelligence

Tools: SQL • Python • Power BI



📌## **Project Overview**

This project analyses automobile sales transactions to understand:

- Revenue performance
- Customer value
- Logistics risk
- Operational reliability

The objective is not just to calculate metrics, but to connect customer behaviour, fulfilment reliability, and revenue risk into a single analytical framework that supports operational and commercial decision-making.



## **Key Business Questions**

This project investigates business questions relevant to commercial and operational teams:

- Which customers generate the highest revenue?

- Which countries experience the highest logistics failure rates?  

- How concentrated is revenue across products?  

- Which high-value customers are exposed to shipping risk? 

- Which products contribute most to operational risk?




📊## **Dashboard Preview**

### Power BI Executive Dashboard

![Executive Dashboard](screenshots/powerbi_executive_dashboard.png)

### Logistics Risk by Country

![Country Risk](screenshots/country_risk_dashboard.png)

### Python Analysis – Customer Segmentation

![RFM Segmentation](screenshots/revenue_contribution_by_rfm_value.png)




##🎯 **Business Objectives**

- Identify high-revenue customers and products exposed to logistics risk

- Measure operational reliability and failure patterns across countries and time

- Understand revenue concentration and risk exposure

- Support retention, logistics optimisation, and revenue protection decisions

- Provide executive-ready dashboards backed by robust KPI logic




📂## **Dataset Overview**

The analysis is based on automobile sales transactions which were transformed into customer-level and order-level analytical datasets, containing:

- Order dates, status, and fulfilment outcomes

- Revenue and pricing (MSRP-based)

- Customer purchase behaviour (frequency, recency, value)

- Product and country attributes



🏗️## **Analytics Style**

The solution follows a layered analytics approach, mirroring real-world data workflows.

🟦 **Python — Exploratory & Advanced Analytics Layer**

Used for exploration, validation, and behavioural intelligence before finalising KPIs.

Key work includes:

- RFM segmentation (Recency, Frequency, Monetary)

- Customer value tiering (High / Mid / Low)

- Shipping reliability scoring at customer level

- Composite Customer Value × Shipping Risk segmentation

- K-Means clustering to identify behavioural personas

- Regression analysis to understand revenue drivers

Python answers:
“What patterns exist, and which KPIs actually matter?”




🟨## **SQL — Data Modeling & KPI Engine**

SQL acts as the single source for business logic and KPIs.

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




🟩## **Power BI — Decision & Storytelling Layer**

Power BI dashboards were built using SQL Gold layer to provide clear, executive-level visibility without exposing analytical complexity, to make it more understandable for non technical stakeholders.

Power BI answers:
“So what should the business do?”



📊 **Power BI Dashboards**


Page 1️⃣ – **Executive Operations Overview**

- Total Revenue & Orders

- Revenue per Order

- Failure Rate & High-Risk Order %

- Overall operational health snapshot

Page 2️⃣ – **Country Risk Deep-Dive**

- Country-wise logistics risk

- Failure and high-risk order patterns

- Geographic exposure analysis

Page 3️⃣ – **Order Status & Backlog Monitoring**

Order status distribution

Backlog and delay monitoring

Early warning indicators for fulfilment issues

Page 4️⃣ – **Product / Revenue at Risk Analysis**

Revenue concentration

Products contributing disproportionately to risk

Identification of revenue exposed to logistics failures



💡## **Key Business Insights**

A small share of orders and products account for a disproportionate share of operational risk

Logistics failures tend to impact customer stability before revenue declines

Revenue is driven more by order frequency and product diversity than order value alone

High-value customers with low shipping reliability represent critical retention risk




✅## **Business Impact**

Targeted retention strategies for high-value, high-risk customers

Prioritised logistics checks for revenue-critical regions

Clear visibility into revenue vs fulfilment trade-offs

Decision-ready insights without exposing technical complexity



🛠️## **Tech Stack**

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




## **Skills Demonstrated**

- Sales performance analysis  
- Customer segmentation (RFM)  
- Logistics risk analysis  
- Revenue concentration analysis  
- SQL data modelling (Bronze → Silver → Gold architecture)  
- Python exploratory analytics and clustering  
- Executive dashboard development in Power BI




🧠## **Final Note**

This project demonstrates a full analyst workflow:

From exploration → validation → production KPIs

From raw data → structured logic → executive decisions

It reflects how analytics is applied in real organisations, not just how tools are used.




📄## **License**

MIT License