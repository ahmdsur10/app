import streamlit as st
import json
import pandas as pd
import folium
from shapely.geometry import shape
from streamlit_folium import st_folium

# -------------------------
# تحميل البيانات
# -------------------------
@st.cache_data
def load_data():
    with open("network.geojson", "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []

    for i, feature in enumerate(data["features"]):

        geom_data = feature.get("geometry")

        if not geom_data:
            continue

        try:
            geom = shape(geom_data)
        except:
            continue

        if geom.is_empty:
            continue

        props = feature.get("properties", {})

        rows.append({
            "id": i,
            "type": props.get("type", "pipe"),
            "length": float(geom.length),
            "geometry": geom_data
        })

    return pd.DataFrame(rows)

df = load_data()

# -------------------------
# UI
# -------------------------
st.title("💧 Storm Network Cost Calculator")

pipe_price = st.number_input("Pipe price", value=100)
box_price = st.number_input("Box price", value=200)

# -------------------------
# Session state
# -------------------------
if "selected_ids" not in st.session_state:
    st.session_state.selected_ids = []

# -------------------------
# 🔥 مهم: التأكد أن البيانات ليست فاضية
# -------------------------
if df.empty:
    st.error("❌ لا توجد بيانات صالحة في GeoJSON")
    st.stop()

# -------------------------
# إنشاء الخريطة (مهم: tiles مضافة)
# -------------------------
m = folium.Map(
    location=[24.7, 46.7],
    zoom_start=11,
    tiles="OpenStreetMap"   # 🔥 هذا يحل مشكلة عدم ظهور الخريطة
)

# -------------------------
# رسم العناصر
# -------------------------
for _, row in df.iterrows():

    color = "blue" if row["type"] == "pipe" else "red"

    if row["id"] in st.session_state.selected_ids:
        color = "green"

    folium.GeoJson(
        row["geometry"],
        style_function=lambda x, color=color: {
            "color": color,
            "weight": 5
        },
        tooltip=f"ID: {row['id']} | {row['type']}",
        popup=str(row["id"])
    ).add_to(m)

# -------------------------
# عرض الخريطة (هذا السطر هو المهم)
# -------------------------
map_output = st_folium(
    m,
    width=900,
    height=500,
    returned_objects=["last_object_clicked"]
)

# -------------------------
# اختيار من الخريطة
# -------------------------
if map_output and map_output.get("last_object_clicked"):

    try:
        clicked = map_output["last_object_clicked"]

        if "popup" in clicked:
            clicked_id = int(clicked["popup"])

            if clicked_id not in st.session_state.selected_ids:
                st.session_state.selected_ids.append(clicked_id)

    except:
        pass

# -------------------------
# النتائج
# -------------------------
st.write("📍 Selected:", st.session_state.selected_ids)

selected = df[df["id"].isin(st.session_state.selected_ids)]

if not selected.empty:

    selected["cost"] = selected.apply(
        lambda r: r["length"] * (pipe_price if r["type"] == "pipe" else box_price),
        axis=1
    )

    st.subheader("📊 Results")
    st.dataframe(selected[["id", "type", "length", "cost"]])

    st.metric("💰 Total Cost", f"{selected['cost'].sum():,.2f}")

    st.bar_chart(selected.groupby("type")["cost"].sum())

# -------------------------
# Reset
# -------------------------
if st.button("Reset"):
    st.session_state.selected_ids = []
