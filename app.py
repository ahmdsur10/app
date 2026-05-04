import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium

# -------------------------
# تحميل البيانات
# -------------------------
@st.cache_data
def load_data():
    gdf = gpd.read_file("network.json")  # أو shapefile
    gdf = gdf.to_crs(epsg=3857)
    gdf["length"] = gdf.geometry.length  # حساب الطول
    return gdf

gdf = load_data()

# -------------------------
# واجهة المستخدم
# -------------------------
st.title("💧 Storm Network Cost Calculator")

# أسعار
pipe_price = st.number_input("سعر المتر للـ Pipe", value=100)
box_price = st.number_input("سعر المتر للـ Box", value=200)

# -------------------------
# إنشاء الخريطة
# -------------------------
m = folium.Map(location=[24.7, 46.7], zoom_start=10)

for idx, row in gdf.iterrows():
    color = "blue" if row["type"] == "pipe" else "red"

    folium.GeoJson(
        row["geometry"],
        tooltip=f"ID: {idx}",
        style_function=lambda x, color=color: {
            "color": color,
            "weight": 4
        }
    ).add_to(m)

# عرض الخريطة
map_data = st_folium(m, width=700, height=500)

# -------------------------
# اختيار الخطوط (بشكل بسيط)
# -------------------------
selected_ids = st.multiselect("اختر ID الخطوط", gdf.index)

selected = gdf.loc[selected_ids]

# -------------------------
# الحسابات
# -------------------------
if not selected.empty:
    selected["cost"] = selected.apply(
        lambda row: row["length"] * (pipe_price if row["type"] == "pipe" else box_price),
        axis=1
    )

    total_cost = selected["cost"].sum()

    st.subheader("📊 النتائج")
    st.write(selected[["type", "length", "cost"]])

    st.metric("💰 التكلفة الإجمالية", f"{total_cost:,.2f}")

    # Dashboard بسيط
    summary = selected.groupby("type")["cost"].sum()
    st.bar_chart(summary)
