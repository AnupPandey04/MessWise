# 🍽️ MessWise --- Smart Mess Demand & Food Waste Analytics

**MessWise** is a MongoDB-powered analytics dashboard that helps explore
meal preparation, attendance, food leftovers, recorded food waste, and
short-term meal-demand forecasts.

-   **Live dashboard:** https://messwise.streamlit.app/
-   **GitHub repository:** https://github.com/AnupPandey04/MessWise

> **Data notice:** The current dashboard uses simulated sample records.
> Forecasts are estimates generated from this sample data, not real
> attendance or operational predictions.

## Overview

MessWise brings mess-related data into one dashboard so users can
inspect meal performance, compare expected and actual attendance,
analyze recorded waste, and view predicted demand by meal type.

### Features

-   Operational KPIs for meals prepared, meals served, leftovers, and
    leftover rate
-   Prepared-versus-served meal analysis
-   Expected-versus-actual attendance analysis
-   Food-waste analysis by menu item, with detailed waste records
-   Meal and attendance summary tables
-   Seven-day demand forecasts for breakfast, lunch, and dinner
-   Random Forest model evaluation against a historical-mean baseline
-   MongoDB schema validation and indexes
-   Query-performance comparison between an indexed query and a
    collection scan

## Technology Stack

-   **Language:** Python
-   **Database:** MongoDB Atlas
-   **Database driver:** PyMongo
-   **Dashboard:** Streamlit
-   **Data processing:** Pandas
-   **Visualizations:** Plotly
-   **Machine learning:** scikit-learn (Random Forest)

## Architecture

``` text
Simulated sample records
          |
          v
     MongoDB Atlas
          |
          v
  PyMongo data services
   |        |         |
   v        v         v
Analytics  Forecasts  Query-performance checks
   |        |
   +--------+
       |
       v
 Streamlit dashboard
       |
       v
KPIs, charts, tables, forecasts and evaluation metrics
```

## Database Design

The application uses the following five MongoDB collections:

  Collection       Purpose
  ---------------- ----------------------------------------------
  `menu_items`     Menu item information
  `meal_records`   Meal preparation and serving records
  `attendance`     Expected and actual attendance records
  `waste_logs`     Recorded food-waste events
  `predictions`    Forecast records and model evaluation output

The project includes MongoDB schema validators and indexes configured by
the database modules. The seed script creates sample data for the
dashboard and **replaces the contents of the project's five collections
when run**. Use it carefully, especially against a database containing
data you want to keep.

## Repository Structure

``` text
MessWise/
├── app.py
├── config.py
├── requirements.txt
├── .gitignore
├── database/
│   ├── connection.py
│   ├── validators.py
│   ├── indexes.py
│   └── seed_data.py
├── services/
│   ├── analytics_service.py
│   ├── prediction_service.py
│   └── query_performance.py
└── tests/
    └── test_database.py
```

## Getting Started

### 1. Prerequisites

-   Python installed
-   A MongoDB Atlas cluster, or a local MongoDB server
-   Git (optional, for cloning the repository)

### 2. Clone the repository

``` bash
git clone https://github.com/AnupPandey04/MessWise.git
cd MessWise
```

### 3. Create and activate a virtual environment

**Windows PowerShell:**

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script activation, use Command Prompt instead:

``` bat
.venv\Scripts\activate.bat
```

### 4. Install dependencies

``` bash
python -m pip install -r requirements.txt
```

### 5. Configure MongoDB

The application reads `MONGO_URI` from Streamlit secrets first, then
from the `MONGO_URI` environment variable. If neither is available, the
configuration falls back to `mongodb://localhost:27017/`.

For local development, create `.streamlit/secrets.toml`:

``` toml
MONGO_URI = "your-mongodb-connection-string"
```

Alternatively, set an environment variable in PowerShell for the current
terminal session:

``` powershell
$env:MONGO_URI = "your-mongodb-connection-string"
```

Do not commit `.streamlit/secrets.toml`, `.env`, passwords, or
connection strings to GitHub. Use a database user with only the
permissions the application needs.

### 6. Initialize the database

Run these commands from the repository root, in order:

``` bash
python -m database.connection
python -m database.validators
python -m database.indexes
python -m database.seed_data
python -m services.prediction_service
```

**Warning:** `python -m database.seed_data` replaces the data in the
project's five collections with sample records. Run it only when that is
intended.

### 7. Launch the dashboard

``` bash
streamlit run app.py
```

Streamlit will print a local URL in the terminal, usually
`http://localhost:8501`.

## Run Checks and Query-Performance Analysis

Run the database checks:

``` bash
python -m tests.test_database
```

Run the indexed-query versus collection-scan comparison:

``` bash
python -m services.query_performance
```

The performance script compares query plans and the number of documents
examined. With a small sample dataset, measured execution times may be
too small to show a meaningful difference; report the observed metrics
rather than claiming an unmeasured speed improvement.

To regenerate model forecasts and evaluation metrics:

``` bash
python -m services.prediction_service
```

## Machine-Learning Evaluation

MessWise uses **Random Forest Regression** from scikit-learn to
forecast meal demand from historical attendance data.

The latest recorded sample run produced the following results:

| Metric                         | Result                    |
|--------------------------------|---------------------------|
| Random Forest MAE              | 18.31                     |
| Historical-mean baseline MAE   | 24.66                     |
| Improvement over baseline      | 25.75%                    |
| Training records               | 69                        |
| Test records                   | 21                        |
| Test period                    | 2026-10-12 to 2026-10-18  |

Mean Absolute Error (MAE) measures the average absolute difference
between predicted and actual attendance. Lower MAE is better.

These results use simulated sample data and a small chronological
test set. They demonstrate the model workflow and should not be
interpreted as evidence of real-world forecasting performance.

## Deployment

The dashboard is deployed on Streamlit Community Cloud:

**https://messwise.streamlit.app/**

To deploy your own copy:

1.  Push the project to a GitHub repository.

2.  Create an app in Streamlit Community Cloud and select `app.py` as
    the entry point.

3.  Add `MONGO_URI` in the app's **Settings → Secrets** using TOML
    syntax:

    ``` toml
    MONGO_URI = "your-mongodb-connection-string"
    ```

4.  Configure MongoDB Atlas network access so the deployed app can reach
    the cluster.

5.  Restart the app and verify that the dashboard sections load.

Avoid exposing database credentials. A broad Atlas IP access rule such
as `0.0.0.0/0` allows connection attempts from any IP address; use a
narrower network configuration when your hosting setup supports it.

## Limitations

-   Current records are simulated sample data, not live mess operations.
-   Forecasts are estimates and depend on the sample data and model.
-   Model evaluation results are based on a small chronological holdout
    set.
-   Query timing on a small dataset may not show a meaningful latency
    difference.

## Future Scope

-   Integrate real mess attendance and meal-production records
-   Add scheduled data ingestion and data-quality monitoring
-   Evaluate forecasts with more historical data and additional metrics
-   Add role-based access for dashboard users
-   Improve operational reporting and waste-reduction recommendations

## Author

**Anup Pandey**

## License

No license has been specified yet. Add a license file if you intend to
define reuse and distribution permissions.
