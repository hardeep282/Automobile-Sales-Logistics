# ***Automobile Sales based on Customer Value and Shipping Risk Intelligence***



**_Customer Value & Shipping Risk Intelligence_**


🛠 _Tools & Skills_

Python, Pandas, NumPy, Scikit-Learn, Seaborn, Matplotlib, Power BI
Customer Analytics | Marketing Analytics | Operational Intelligence | Clustering | KPI Design


📌 **_Project Objective_**

To build a data-driven customer intelligence model that combines customer value (RFM segmentation) with logistics performance (shipping reliability) in order to understand:

-	Some high-value customers at fulfilment risk
-	Stable customers with overall high purchasing power and shipping reliability
-	Upsell opportunities
-	logistics inefficiencies affecting revenue retention for certain bracket of consumers

📂 **_Dataset Overview_**

A Customer-level dataset was derived from automobile sales transactions containing:

-	Recency of purchase
-	Purchase frequency
-	Revenue contribution or Monetary power
-	Product variety
-	Average order value (MSRP)
-	Shipping success ratio
-	Geographical and product categories

🧠 **_Key Analytical Layers_**

1️⃣ _RFM Segmentation_

-	Customers were categorised into High, Mid, and Low Value tiers based on:
-	Recency (days since last purchase)
-	Frequency (number of orders)
-	Monetary (total revenue generated)

This was the foundation for basic customer evaluation.

2️⃣ _Shipping Reliability Intelligence_

A shipping reliability score was calculated for each customer using historical fulfilment success rates.
Customers were further grouped into:

-	Reliable
-	Minor Issues
-	Unreliable
-	Critical

3️⃣ _Composite Value × Shipping Segmentation_

By combining RFM value tiers with shipping reliability, strategic business segments were formed, such as:

-	High Value – Fulfilment Risk
-	High Value – Stable
-	Mid Value – Risk
-	Low Priority Customers
-	This layer directly supports:
-	Retention strategy
-	Logistics optimisation
-	Revenue protection

4️⃣ _Behavioural Clustering (K-Means)_

K-Means clustering was applied on to understand the distribution pattern based on segmentation
	
-	RFM features
-	Shipping reliability
-	Product variety

This revealed distinct behavioural customer personas such as:

-	Core stable buyers
-	VIP heavy buyers
-	Operational risk customers


5️⃣ _Supporting Revenue Regression_

A linear regression model was built to understand numerical revenue drivers.	

Key findings:

-  Order frequency, product variety, and order value were the strongest predictors.
- Shipping reliability showed low direct revenue impact but high churn and risk segmentation value.


📊 _Key Business Insights_

-	A high-revenue customer segment was identified that is operationally at risk due to poor shipping         performance.
-	Logistics failures impact customer stability before impacting revenue.
-	Behavioural clustering helped separate growth customers from decline-risk customers.
-	Revenue is primarily driven by frequency and product diversity, not just order value.


💼 _Business Insights_

| Segment | Behaviour | Action |
|---------|-----------|--------|
| High Value + Low Reliability | At risk | Improve logistics |
| High Value + High Reliability | Retain | Upsell |
| Low Value + High Reliability | Growth potential | Targeted offers |



✅ Business Impact

-	Improved targeting for customer retention campaigns
-   Prioritised logistics audits for high-revenue risk customers
-	Data-backed upsell strategy for mid-tier customers
-	Executive-level visibility into revenue vs fulfilment trade-offs


📈 Dashboards (Power BI)

An executive-ready Power BI dashboard was built to visualise:

-	RFM customer distribution
-	Revenue by value tier
-	Shipping risk distribution
-	High-Value Fulfilment Risk customers
-	Behaviour-based customer clusters



## _How to Run Locally_
```
- git clone <repo-url>
- cd Automobile-Sales-Logistics
- python -m venv venv
- source venv/bin/activate # or venv\Scripts\activate
- pip install -r requirements.txt
- streamlit run app.py

```


## 🛠 _Tech Stack_
![Python](https://img.shields.io/badge/Python-3.12-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Framework-red)
![Pandas](https://img.shields.io/badge/Pandas-Data--Analysis-green)
![Sklearn](https://img.shields.io/badge/Sklearn-ML-orange)



## 📁 _Repository Structure_
```
project/
│── Data/
│── Notebooks/
│── src/
│   ├── charts.py
│   ├── init.py
│   ├── preprocessing.py
|   └── utils.py
│── .gitignore
│── LICENSE
│── README.md
│── app.py
│──requirements.txt

```

---


👤 Author

**Hardeep Bamrah**  
Aspiring Business Analyst | Marketing & Sales Analytics | UK-based Graduate

## 📄 _License_

MIT License
