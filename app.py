import pandas as pd
import plotly.express as px
import streamlit as st

from database.connection import db
from services.analytics_service import (
    get_meal_summary,
    get_waste_by_menu_item,
    get_attendance_summary,
)

# Page setup
st.set_page_config(
    page_title="MessWise",
    page_icon="🍽️",
    layout="wide",
)

st.title("🍽️ MessWise")
st.caption("Smart Mess Demand & Food Waste Analytics")
st.info("Dashboard uses simulated sample data.")

# Get summaries from MongoDB
meals = pd.DataFrame(get_meal_summary())
waste = pd.DataFrame(get_waste_by_menu_item())
attendance = pd.DataFrame(get_attendance_summary())

if meals.empty:
    st.warning("No meal data found. Run the seed script first.")
    st.stop()

# Filter by meal type
meal_types = ["All"] + sorted(meals["meal_type"].unique().tolist())
selected_meal = st.sidebar.selectbox("Select meal", meal_types)

if selected_meal != "All":
    meals = meals[meals["meal_type"] == selected_meal]
    attendance = attendance[
        attendance["meal_type"] == selected_meal
    ]

# Calculated dashboard values
prepared = int(meals["total_prepared"].sum())
served = int(meals["total_served"].sum())
leftovers = int(meals["total_leftovers"].sum())
leftover_rate = leftovers / prepared * 100 if prepared else 0
total_waste = (
    float(waste["total_waste_kg"].sum())
    if not waste.empty else 0
)

# Displayed key metrics
st.subheader("Operational Overview")
c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Meals Prepared", f"{prepared:,}")
c2.metric("Meals Served", f"{served:,}")
c3.metric("Leftovers", f"{leftovers:,}")
c4.metric("Leftover Rate", f"{leftover_rate:.2f}%")
c5.metric("Food Waste (kg)", f"{total_waste:.2f}")

# Meal and attendance charts
left, right = st.columns(2)

with left:
    st.subheader("Prepared vs Served")
    fig = px.bar(
        meals,
        x="meal_type",
        y=["total_prepared", "total_served"],
        barmode="group",
        template="plotly_white",
    )
    st.plotly_chart(fig, width="stretch")

with right:
    st.subheader("Expected vs Actual Attendance")
    fig = px.bar(
        attendance,
        x="meal_type",
        y=["total_expected", "total_actual"],
        barmode="group",
        template="plotly_white",
    )
    st.plotly_chart(fig, width="stretch")

# Food-waste chart
st.subheader("Food Waste by Menu Item")

if waste.empty:
    st.write("No waste records available.")
else:
    fig = px.bar(
        waste.sort_values("total_waste_kg"),
        x="total_waste_kg",
        y="item_name",
        orientation="h",
        labels={
            "total_waste_kg": "Waste (kg)",
            "item_name": "Menu item",
        },
        template="plotly_white",
    )
    st.plotly_chart(fig, width="stretch")

# Summary tables
with st.expander("View Summary Tables"):
    st.write("Meal Summary")
    st.dataframe(meals, width="stretch", hide_index=True)

    st.write("Attendance Summary")
    st.dataframe(attendance, width="stretch", hide_index=True)

    st.write("Food Waste Summary")
    st.dataframe(waste, width="stretch", hide_index=True)

# Random Forest demand forecasts
st.header("Seven-Day Meal Demand Forecast")

forecasts = pd.DataFrame(
    list(
        db.predictions.find(
            {"model_name": "random_forest_v1"},
            {
                "_id": 0,
                "target_date": 1,
                "meal_type": 1,
                "predicted_demand": 1,
            },
        ).sort([
            ("target_date", 1),
            ("meal_type", 1),
        ])
    )
)

if forecasts.empty:
    st.warning(
        "No forecasts found. Run "
        "python -m services.prediction_service"
    )
else:
    forecasts["target_date"] = pd.to_datetime(
        forecasts["target_date"]
    )

    if selected_meal != "All":
        forecasts = forecasts[
            forecasts["meal_type"] == selected_meal
        ]

    if not forecasts.empty:
        st.metric(
            "Average Predicted Demand",
            f"{forecasts['predicted_demand'].mean():.0f}",
        )

        fig = px.line(
            forecasts,
            x="target_date",
            y="predicted_demand",
            color="meal_type",
            markers=True,
            template="plotly_white",
            labels={
                "target_date": "Date",
                "predicted_demand": "Predicted students",
                "meal_type": "Meal",
            },
        )
        st.plotly_chart(fig, width="stretch")
        st.dataframe(forecasts, width="stretch", hide_index=True)
    else:
        st.info("No forecasts for the selected meal.")

# Model evaluation
st.header("Random Forest Model Evaluation")

evaluation = db.model_evaluations.find_one(
    {"evaluation_name": "latest"},
    {"_id": 0},
)

if evaluation:
    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Random Forest MAE",
        f"{evaluation['model_mae']:.2f}",
    )
    c2.metric(
        "Baseline MAE",
        f"{evaluation['baseline_mae']:.2f}",
    )
    c3.metric(
        "Improvement",
        f"{evaluation['improvement_percent']:.2f}%",
    )

    st.write(evaluation["result"])
    st.caption(
        f"Training records: {evaluation['training_records']} | "
        f"Test records: {evaluation['test_records']}"
    )
    st.caption("MAE measures prediction error; lower is better.")
else:
    st.info(
        "Run python -m services.prediction_service "
        "to generate evaluation results."
    )
