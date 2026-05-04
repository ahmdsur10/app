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
    with open("network.geojson") as f:
        data = json.load(f)

    rows = []

    for i, feature in enumerate(data["features"]):
        geom = shape(feature["geometry"])
        props = feature.get("properties", {})

        rows.append({
            "id": i,
            "type": props.get("type", "pipe"),
            "length": geom.length,
            "geometry": feature["geometry"]
        })

    return pd.DataFrame(rows)

df = load_data()

# -------------------------
# session state
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

    # إذا مختار نخليه أخضر
    if row["id"] in st.session_state.selected_ids:
        color = "green"

    geo = folium.GeoJson(
        row["geometry"],
        name=str(row["id"]),
        style_function=lambda x, color=color: {
            "color": color,
            "weight": 5
        },
        tooltip=f"Click | ID: {row['id']} | Type: {row['type']}"
    )

    geo.add_child(folium.Popup(str(row["id"])))
    geo.add_to(m)

# عرض الخريطة
map_data = st_folium(m, width=800, height=500)

# -------------------------
# التقاط الضغط
# -------------------------
if map_data and map_data.get("last_object_clicked"):
    props = map_data["last_object_clicked"].get("properties")

    if props and "name" in props:
        clicked_id = int(props["name"])

        if clicked_id not in st.session_state.selected_ids:
            st.session_state.selected_ids.append(clicked_id)

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

    # Dashboard
    summary = selected.groupby("type")["cost"].sum()
    st.bar_chart(summary)

# -------------------------
# Reset
# -------------------------
if st.button("🔄 Reset Selection"):
    st.session_state.selected_ids = []
