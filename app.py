import streamlit as st
import json
import pandas as pd
import folium
from shapely.geometry import shape
from streamlit_folium import st_folium

# -------------------------
# تحميل وتنظيف البيانات
# -------------------------
@st.cache_data
def load_data():
    with open("network.geojson", "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []

    for i, feature in enumerate(data["features"]):

        # -------------------------
        # 1) التحقق من وجود geometry
        # -------------------------
        geom_data = feature.get("geometry")

        if not geom_data:
            continue

        if "type" not in geom_data or "coordinates" not in geom_data:
            continue

        # -------------------------
        # 2) تحويل الشكل بأمان
        # -------------------------
        try:
            geom = shape(geom_data)
        except Exception:
            continue

        # تجاهل الأشكال الفارغة
        if geom.is_empty:
            continue

        props = feature.get("properties", {})

        rows.append({
            "id": i,
            "type": props.get("type", "pipe"),
            "length": geom.length,
            "geometry": geom_data
        })

    return pd.DataFrame(rows)

df = load_data()

# -------------------------
# Session State
# -------------------------
if "selected_ids" not in st.session_state:
    st.session_state.selected_ids = []

# -------------------------
# UI
# -------------------------
st.title("💧 Storm Network Cost Calculator")

pipe_price = st.number_input("سعر المتر Pipe", value=100)
box_price = st.number_input("سعر المتر Box", value=200)

# -------------------------
# الخريطة
# -------------------------
m = folium.Map(location=[24.7, 46.7], zoom_start=11)

for _, row in df.iterrows():

    color = "blue" if row["type"] == "pipe" else "red"

    if row["id"] in st.session_state.selected_ids:
        color = "green"

    geo = folium.GeoJson(
        row["geometry"],
        name=str(row["id"]),
        style_function=lambda x, color=color: {
            "color": color,
            "weight": 5
        },
        tooltip=f"ID: {row['id']} | Type: {row['type']}"
    )

    geo.add_child(folium.Popup(str(row["id"])))
    geo.add_to(m)

# عرض الخريطة
map_data = st_folium(m, width=800, height=500)

# -------------------------
# التقاط الضغط من الخريطة
# -------------------------
if map_data and map_data.get("last_object_clicked"):

    props = map_data["last_object_clicked"].get("properties")

    if props and "name" in props:
        try:
            clicked_id = int(props["name"])

            if clicked_id not in st.session_state.selected_ids:
                st.session_state.selected_ids.append(clicked_id)

        except:
            pass

# -------------------------
# عرض المختار
# -------------------------
st.write("📍 العناصر المختارة:", st.session_state.selected_ids)

selected = df[df["id"].isin(st.session_state.selected_ids)].copy()

# -------------------------
# الحساب
# -------------------------
if not selected.empty:

    selected["cost"] = selected.apply(
        lambda row: row["length"] * (pipe_price if row["type"] == "pipe" else box_price),
        axis=1
    )

    total_cost = selected["cost"].sum()

    st.subheader("📊 النتائج")

    st.dataframe(selected[["id", "type", "length", "cost"]])

    st.metric("💰 التكلفة الإجمالية", f"{total_cost:,.2f}")

    st.bar_chart(selected.groupby("type")["cost"].sum())

# -------------------------
# Reset
# -------------------------
if st.button("🔄 Reset Selection"):
    st.session_state.selected_ids = []
