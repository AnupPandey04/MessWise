import streamlit as st
import pandas as pd
import plotly.express as px

from database.connection import db
from services.analytics_service import (
    get_meal_summary,
    get_waste_by_menu_item,
    get_attendance_summary,
)

st.set_page_config(
    page_title="MessWise | Smart Mess Analytics",
    page_icon="🍽️",
    layout="wide",
)

# -------------------- PAGE HEADER --------------------
st.title("🍽️ MessWise")
st.caption("Smart Mess Demand & Food Waste Analytics")
st.markdown(
    "Monitor meal preparation, attendance, food waste, "
    "and predicted demand from MongoDB."
)

# -------------------- LOAD DATA --------------------
meal_data = get_meal_summary()
waste_data = get_waste_by_menu_item()
attendance_data = get_attendance_summary()

if not meal_data:
    st.warning("No meal data found. Run the seed script first.")
    st.stop()

meals = pd.DataFrame(meal_data)
waste = pd.DataFrame(waste_data)
attendance = pd.DataFrame(attendance_data)

# -------------------- SIDEBAR --------------------
st.sidebar.title("MessWise")
st.sidebar.caption("Analytics Control Panel")
st.sidebar.divider()

meal_options = ["All"] + sorted(meals["meal_type"].unique().tolist())
selected_meal = st.sidebar.selectbox(
    "Filter by meal",
    meal_options,
)

st.sidebar.info(
    "Data currently uses simulated sample records. "
    "Forecasts are estimates, not actual attendance."
)

# Filter the summary data by meal type
filtered_meals = meals.copy()
filtered_attendance = attendance.copy()

if selected_meal != "All":
    filtered_meals = filtered_meals[
        filtered_meals["meal_type"] == selected_meal
    ]
    filtered_attendance = filtered_attendance[
        filtered_attendance["meal_type"] == selected_meal
    ]

# -------------------- KPI CALCULATIONS --------------------
total_prepared = int(filtered_meals["total_prepared"].sum())
total_served = int(filtered_meals["total_served"].sum())
total_leftovers = int(filtered_meals["total_leftovers"].sum())

leftover_rate = (
    total_leftovers / total_prepared * 100
    if total_prepared else 0
)

total_waste_kg = (
    float(waste["total_waste_kg"].sum())
    if not waste.empty else 0
)

# -------------------- KPI CARDS --------------------
st.subheader("Operational Overview")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Meals Prepared", f"{total_prepared:,}")
c2.metric("Meals Served", f"{total_served:,}")
c3.metric("Leftover Meals", f"{total_leftovers:,}")
c4.metric("Leftover Rate", f"{leftover_rate:.2f}%")

st.divider()

# -------------------- MEAL ANALYTICS --------------------
left, right = st.columns(2)

with left:
    st.subheader("Meal Performance")

    fig = px.bar(
        filtered_meals,
        x="meal_type",
        y=["total_prepared", "total_served"],
        barmode="group",
        labels={
            "meal_type": "Meal",
            "value": "Number of meals",
            "variable": "Metric",
        },
        title="Prepared vs Served",
        template="plotly_white",
    )
    fig.update_layout(legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Attendance Analysis")

    fig = px.bar(
        filtered_attendance,
        x="meal_type",
        y=["total_expected", "total_actual"],
        barmode="group",
        labels={
            "meal_type": "Meal",
            "value": "Number of students",
            "variable": "Metric",
        },
        title="Expected vs Actual Attendance",
        template="plotly_white",
    )
    fig.update_layout(legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# -------------------- WASTE ANALYSIS --------------------
st.subheader("♻️ Food Waste Analysis")
st.caption(f"Total recorded waste: {total_waste_kg:.2f} kg")

if not waste.empty:
    waste_sorted = waste.sort_values(
        "total_waste_kg", ascending=True
    )

    fig = px.bar(
        waste_sorted,
        x="total_waste_kg",
        y="item_name",
        orientation="h",
        labels={
            "total_waste_kg": "Recorded waste (kg)",
            "item_name": "Menu item",
        },
        title="Recorded Waste by Menu Item",
        template="plotly_white",
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("View detailed waste records"):
        st.dataframe(waste, use_container_width=True, hide_index=True)
else:
    st.info("No waste records are available.")

# -------------------- SUMMARY TABLES --------------------
with st.expander("View Meal Summary"):
    st.dataframe(
        filtered_meals,
        use_container_width=True,
        hide_index=True,
    )

with st.expander("View Attendance Summary"):
    st.dataframe(
        filtered_attendance,
        use_container_width=True,
        hide_index=True,
    )

st.divider()

# -------------------- DEMAND FORECASTS --------------------
st.header("🔮 Meal Demand Prediction")
st.caption(
    "Random Forest forecasts generated from historical attendance data."
)

forecast_records = list(
    db.predictions.find(
        {"model_name": "random_forest_v1"},
        {
            "_id": 0,
            "target_date": 1,
            "meal_type": 1,
            "predicted_demand": 1,
            "model_name": 1,
        },
    ).sort([
        ("target_date", 1),
        ("meal_type", 1),
    ])
)

if forecast_records:
    forecasts = pd.DataFrame(forecast_records)
    forecasts["target_date"] = pd.to_datetime(
        forecasts["target_date"]
    )

    min_date = forecasts["target_date"].min().date()
    max_date = forecasts["target_date"].max().date()

    col_start, col_end = st.columns(2)

    with col_start:
        start_date = st.date_input(
            "Forecast start date",
            value=min_date,
            min_value=min_date,
            max_value=max_date,
            key="forecast_start_date",
        )

    with col_end:
        end_date = st.date_input(
            "Forecast end date",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            key="forecast_end_date",
        )

    if start_date <= end_date:
        filtered_forecasts = forecasts[
            forecasts["target_date"].dt.date.between(
                start_date, end_date
            )
        ].copy()
    else:
        st.warning("Start date must be on or before end date.")
        filtered_forecasts = forecasts.iloc[0:0].copy()

    if selected_meal != "All":
        filtered_forecasts = filtered_forecasts[
            filtered_forecasts["meal_type"] == selected_meal
        ]

    if not filtered_forecasts.empty:
        c1, c2 = st.columns(2)

        c1.metric(
            "Forecast Records",
            len(filtered_forecasts),
        )
        c2.metric(
            "Average Predicted Demand",
            f"{filtered_forecasts['predicted_demand'].mean():.0f}",
        )

        fig = px.line(
            filtered_forecasts,
            x="target_date",
            y="predicted_demand",
            color="meal_type",
            markers=True,
            title="Predicted Demand by Meal Type",
            labels={
                "target_date": "Forecast date",
                "predicted_demand": "Predicted students",
                "meal_type": "Meal type",
            },
            template="plotly_white",
        )
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("View Forecast Details", expanded=True):
            display_forecasts = filtered_forecasts.copy()
            display_forecasts["target_date"] = (
                display_forecasts["target_date"].dt.date
            )
            st.dataframe(
                display_forecasts,
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.info("No forecasts match the selected filters.")
else:
    st.warning(
        "No Random Forest forecasts found. Run "
        "`python -m services.prediction_service` to generate them."
    )



# -------------------- MODEL EVALUATION --------------------
st.divider()
st.header("📊 Model Evaluation")
st.caption(
    "Performance measured on a chronological holdout set. "
    "Lower MAE indicates smaller average prediction errors."
)

evaluation = db.model_evaluations.find_one(
    {"evaluation_name": "latest"},
    {"_id": 0},
)

if evaluation:
    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Random Forest MAE",
        f"{evaluation['model_mae']:.2f}",
        help="Mean Absolute Error on the held-out test records.",
    )

    c2.metric(
        "Baseline MAE",
        f"{evaluation['baseline_mae']:.2f}",
        help="Error from predicting the training-set mean for each meal type.",
    )

    c3.metric(
        "Improvement over Baseline",
        f"{evaluation['improvement_percent']:.2f}%",
        help="Positive means Random Forest has lower MAE than the baseline.",
    )

    st.write(f"**Evaluation result:** {evaluation['result']}")
    st.write(
        f"**Training records:** {evaluation['training_records']}  |  "
        f"**Test records:** {evaluation['test_records']}"
    )

    if evaluation.get("test_start_date") and evaluation.get("test_end_date"):
        st.caption(
            "Test period: "
            f"{evaluation['test_start_date'].date()} to "
            f"{evaluation['test_end_date'].date()}"
        )
else:
    st.info(
        "Evaluation metrics are not available yet. "
        "Run `python -m services.prediction_service` first."
    )



# -------------------- FOOTER --------------------
st.divider()
st.caption(
    "MessWise | MongoDB • Streamlit • Plotly • "
    "scikit-learn | Uses simulated sample data."
)
