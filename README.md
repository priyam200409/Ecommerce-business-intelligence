# E-Commerce Business Intelligence

## Sales, Customer, Product & Operations Analytics

An end-to-end Data Analyst portfolio project built using the Olist Brazilian E-Commerce Public Dataset.

The project analyzes e-commerce sales, customer behavior, product performance, seller performance, delivery operations, and customer experience using Python, SQL, DuckDB, and Power BI.

---

## Project Objective

The objective of this project is to transform raw e-commerce transaction data into a validated analytical data model and business intelligence solution.

The project focuses on:

- Sales performance
- Customer behavior and segmentation
- Product and category performance
- Seller performance
- Delivery operations
- Customer experience
- Geographic performance
- Business KPI reporting

The project follows a validation-first approach so that analytical results are reconciled against the underlying transactional data.

---

## Dataset

**Dataset:** Brazilian E-Commerce Public Dataset by Olist

The dataset contains anonymized Brazilian e-commerce transactions covering orders, customers, products, sellers, payments, reviews, and geographic information.

### Source Tables

- Orders
- Order Items
- Customers
- Products
- Sellers
- Order Payments
- Order Reviews
- Geolocation
- Product Category Translation

### Dataset Scale

| Dataset | Rows |
|---|---:|
| Orders | 99,441 |
| Order Items | 112,650 |
| Customers | 99,441 |
| Products | 32,951 |
| Sellers | 3,095 |
| Payments | 103,886 |
| Reviews | 99,224 |
| Geolocation | 1,000,163 |
| Category Translation | 71 |

---

# Tech Stack

- **Python**
- **Pandas**
- **NumPy**
- **Matplotlib**
- **Plotly**
- **SQL**
- **DuckDB**
- **Power BI**
- **Git / GitHub**

---

# Project Architecture

```text
Raw Olist CSV Data
        |
        v
Data Profiling
        |
        v
Data Quality Audit
        |
        v
Python Data Cleaning
        |
        v
Analytical Data Model
        |
        v
DuckDB
        |
        +--------------------+
        |                    |
        v                    v
   SQL Analytics       Python Validation
        |
        v
Business Analytics
        |
        v
Power BI
        |
        v
Business Intelligence Dashboard