import streamlit as st
import pandas as pd
import plotly.express as px

# ================================
# Page Config
# ================================
st.set_page_config(page_title="Sales & Profit Dashboard", layout="wide")
st.title("📊 Sales & Profit Insights (Jul–Sep)")

# ================================
# Load Data
# ================================
@st.cache_data
def load_sales_data(file_path):
    df = pd.read_excel(file_path)
    df["Item Code"] = df["Item Code"].astype(str)
    return df.fillna(0)

@st.cache_data
def load_price_list(file_path):
    df = pd.read_excel(file_path)
    df["Item Bar Code"] = df["Item Bar Code"].astype(str)
    return df.fillna(0)

# ================================
# File paths
# ================================
sales_file = "july to sep safa2025.Xlsx"
price_file = "price list.xlsx"

sales_df = load_sales_data(sales_file)
price_df = load_price_list(price_file)

# ================================
# Clean & Prepare Data
# ================================
sales_cols = [
    "Jul-2025 Total Sales", "Jul-2025 Total Profit",
    "Aug-2025 Total Sales", "Aug-2025 Total Profit",
    "Sep-2025 Total Sales", "Sep-2025 Total Profit"
]
for col in sales_cols:
    if col not in sales_df.columns:
        sales_df[col] = 0

# Merge both datasets initially (base data)
merged_df = pd.merge(price_df, sales_df, left_on="Item Bar Code", right_on="Item Code", how="left")
merged_df.fillna(0, inplace=True)

if "Category" not in merged_df.columns:
    merged_df["Category"] = "Unknown"
else:
    merged_df["Category"] = merged_df["Category"].astype(str).replace("", "Unknown")

# ================================
# Sidebar Filters
# ================================
st.sidebar.header("🔍 Filters")

# Search inputs
item_search = st.sidebar.text_input("Search Item Name")
barcode_search = st.sidebar.text_input("Search Item Bar Code")

# Category filter
all_categories = ["All"] + sorted(merged_df["Category"].dropna().unique().tolist())
selected_category = st.sidebar.selectbox("Select Category", all_categories)

# ================================
# Apply Filters
# ================================
filtered_df = merged_df.copy()

# Category filter first
if selected_category != "All":
    filtered_df = filtered_df[filtered_df["Category"] == selected_category]

# Search filters next
if item_search:
    filtered_df = filtered_df[filtered_df["Item Name"].astype(str).str.contains(item_search, case=False, na=False)]
if barcode_search:
    filtered_df = filtered_df[filtered_df["Item Bar Code"].astype(str).str.contains(barcode_search, case=False, na=False)]

# ================================
# Compute Totals
# ================================
def compute_totals(df):
    df["Total Sales"] = df["Jul-2025 Total Sales"] + df["Aug-2025 Total Sales"] + df["Sep-2025 Total Sales"]
    df["Total Profit"] = df["Jul-2025 Total Profit"] + df["Aug-2025 Total Profit"] + df["Sep-2025 Total Profit"]
    df["Overall GP"] = df.apply(lambda x: (x["Total Profit"] / x["Total Sales"]) if x["Total Sales"] != 0 else 0, axis=1)
    return df

filtered_df = compute_totals(filtered_df)

# ================================
# Key Metrics
# ================================
st.markdown(f"### 🔑 Key Metrics {'(All Categories)' if selected_category == 'All' else f'({selected_category})'}")

total_sales = filtered_df["Total Sales"].sum()
total_profit = filtered_df["Total Profit"].sum()
overall_gp = (total_profit / total_sales) if total_sales != 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total Sales", f"{total_sales:,.0f}")
col2.metric("Total Profit", f"{total_profit:,.0f}")
col3.metric("Overall GP", f"{overall_gp:.2%}")

# ================================
# Monthly Performance
# ================================
st.markdown("### 📅 Month-wise Performance")

months = ["Jul-2025", "Aug-2025", "Sep-2025"]
month_data = []
for month in months:
    sales_col = f"{month} Total Sales"
    profit_col = f"{month} Total Profit"
    month_data.append({"Month": month, "Type": "Sales", "Value": filtered_df[sales_col].sum()})
    month_data.append({"Month": month, "Type": "Profit", "Value": filtered_df[profit_col].sum()})

monthly_df = pd.DataFrame(month_data)
fig_monthly = px.bar(
    monthly_df, x="Month", y="Value", color="Type", barmode="group",
    text="Value", title=f"Monthly Sales & Profit ({selected_category})"
)
st.plotly_chart(fig_monthly, use_container_width=True)

# ================================
# Category-wise Summary
# ================================
category_summary = merged_df.groupby("Category").agg({
    "Total Sales": "sum",
    "Total Profit": "sum"
}).reset_index()
category_summary["GP%"] = category_summary["Total Profit"] / category_summary["Total Sales"].replace(0, 1)

st.markdown("### 🏷 Category-wise Overview")

fig_sales = px.bar(category_summary, x="Category", y="Total Sales", color="Total Sales",
                   text="Total Sales", title="Total Sales by Category")
st.plotly_chart(fig_sales, use_container_width=True)

fig_profit = px.bar(category_summary, x="Category", y="Total Profit", color="Total Profit",
                    text="Total Profit", title="Total Profit by Category")
st.plotly_chart(fig_profit, use_container_width=True)

fig_gp = px.bar(category_summary, x="Category", y="GP% ", color="GP% ",
                text=category_summary["GP%"].apply(lambda x: f"{x:.2%}"),
                title="Gross Profit % by Category")
st.plotly_chart(fig_gp, use_container_width=True)

# ================================
# Item-wise Table
# ================================
st.markdown("### 📝 Item-wise Details")

table_cols = [
    "Item Bar Code", "Item Name", "Category", "Cost", "Selling", "Stock",
    "Total Sales", "Total Profit", "Overall GP",
    "Jul-2025 Total Sales", "Jul-2025 Total Profit",
    "Aug-2025 Total Sales", "Aug-2025 Total Profit",
    "Sep-2025 Total Sales", "Sep-2025 Total Profit"
]

for col in table_cols:
    if col not in filtered_df.columns:
        filtered_df[col] = 0

filtered_df["Overall GP"] = filtered_df["Overall GP"].apply(lambda x: f"{x:.2%}")

st.dataframe(filtered_df[table_cols].sort_values("Total Sales", ascending=False),
             use_container_width=True, hide_index=True)
