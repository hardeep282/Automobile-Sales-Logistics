Customer Value & Shipping Risk Intelligence

Technologies: Python, Pandas, Scikit-Learn, Seaborn, Matplotlib, Power BI
Domain: Sales Analytics | Marketing Analytics | Operational Intelligence

📌 Project Objective

To build a data-driven customer intelligence model that combines customer value (RFM segmentation) with logistics performance (shipping reliability) in order to identify:

-	High-value customers at fulfilment risk
-	Stable VIP customers
-	Upsell opportunities
-	Operational inefficiencies affecting revenue retention

📂 Dataset Overview

Customer-level dataset derived from automobile sales transactions containing:

•	Recency of purchase
•	Purchase frequency
•	Revenue contribution
•	Product variety
•	Average order value (MSRP)
•	Shipping success ratio
•	Key geography and product categories

🧠 Key Analytical Layers

1️⃣ RFM Segmentation

•	Customers were segmented into High, Mid, and Low Value tiers based on:
•	Recency (days since last purchase)
•	Frequency (number of orders)
•	Monetary (total revenue generated)

This formed the core customer valuation layer.

2️⃣ Shipping Reliability Intelligence

A shipping reliability score was calculated for each customer using historical fulfilment success rates.
Customers were further grouped into:

•	Reliable
•	Minor Issues
•	Unreliable
•	Critical

3️⃣ Composite Value × Shipping Segmentation

By combining RFM value tiers with shipping reliability, strategic business segments were formed, such as:

•	High Value – Fulfilment Risk
•	High Value – Stable
•	Mid Value – Risk
•	Low Priority Customers
•	This layer directly supports:
•	Retention strategy
•	Logistics optimisation
•	Revenue protection

4️⃣ Behavioural Clustering (K-Means)

•	K-Means clustering was applied on:
•	RFM features
•	Shipping reliability
•	Product variety

This revealed distinct behavioural customer personas such as:

•	Core stable buyers
•	VIP heavy buyers
•	Operational risk customers

5️⃣ Supporting Revenue Regression

•	A linear regression model was built to understand numerical revenue drivers.

Key findings:
•	Order frequency, product variety, and order value were the strongest predictors.
•	Shipping reliability showed low direct revenue impact but high churn and risk segmentation value.

📊 Key Business Insights

•	A high-revenue customer segment was identified that is operationally at risk due to poor shipping performance.
•	Logistics failures impact customer stability before impacting revenue.
•	Behavioural clustering helped separate growth customers from decline-risk customers.
•	Revenue is primarily driven by frequency and product diversity, not just order value.

✅ Business Impact

•	Improved targeting for customer retention campaigns
•	Prioritised logistics audits for high-revenue risk customers
•	Data-backed upsell strategy for mid-tier customers
•	Executive-level visibility into revenue vs fulfilment trade-offs

📈 Dashboards (Power BI)

An executive-ready Power BI dashboard was built to visualise:

•	RFM customer distribution
•	Revenue by value tier
•	Shipping risk distribution
•	High-Value Fulfilment Risk customers
•	Behaviour-based customer clusters

🛠 Tools & Skills

Python, Pandas, NumPy, Scikit-Learn, Seaborn, Matplotlib, Power BI
Customer Analytics | Marketing Analytics | Operational Intelligence | Clustering | KPI Design


## How to Run Locally

git clone <repo-url>
cd Automobile-Sales-Logistics
python -m venv venv
source venv/bin/activate # or venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py



## 🛠 Tech Stack
![Python](https://img.shields.io/badge/Python-3.12-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Framework-red)
![Pandas](https://img.shields.io/badge/Pandas-Data--Analysis-green)
![Sklearn](https://img.shields.io/badge/Sklearn-ML-orange)


## 💼 Business Insights
| Segment | Behaviour | Action |
|---------|-----------|--------|
| High Value + Low Reliability | At risk | Improve logistics |
| High Value + High Reliability | Retain | Upsell |
| Low Value + High Reliability | Growth potential | Targeted offers |

## 📁 Repository Structure
```
project/
│── app.py
│── requirements.txt
│── src/
│   ├── charts.py
│   ├── data_cleaning.py
│   └── feature_engineering.py
│── Data/
│── Notebooks/
│── README.md
```

---


👤 Author

Hardeep Bamrah
Aspiring Business Analyst | Marketing & Sales Analytics | UK-based Graduate
