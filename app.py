from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
import pydeck as pdk

st.set_page_config(page_title="MeteoGuard AI", page_icon="🌦️", layout="wide")
ROOT = Path(__file__).resolve().parent

@st.cache_data
def load_data():
    return (
        pd.read_csv(ROOT / "alerts.csv", parse_dates=["timestamp"]),
        pd.read_csv(ROOT / "metrics.csv"),
        pd.read_csv(ROOT / "extremes.csv"),
    )

alerts, metrics, extremes = load_data()
VAR = {
    "dewpoint_c": "Dew point (°C)",
    "sea_level_pressure_hpa": "Sea-level pressure (hPa)",
    "temperature_c": "Temperature (°C)",
    "visibility_m": "Visibility (m)",
    "wind_speed_ms": "Wind speed (m/s)",
}
SPLIT = {
    "seen_time_holdout": "Previously observed stations",
    "unseen_station": "New / unseen stations",
}
STATUS = {
    "suggest correction": "Review proposed correction",
    "human review": "Human review required",
}

st.markdown("""
<style>
.block-container{padding-top:1.5rem;padding-bottom:2rem}
[data-testid="stMetric"]{background:#f7fafc;border:1px solid #e2e8f0;
padding:.8rem 1rem;border-radius:.75rem}
.hero{padding:1rem 1.2rem;border-radius:.8rem;background:
linear-gradient(120deg,#0f4c5c,#1f7a8c);color:white;margin-bottom:1rem}
.hero h1{margin:0;color:white;font-size:2rem}.hero p{margin:.45rem 0 0;color:#eefbff}
.notice{padding:.8rem 1rem;border-left:4px solid #1f7a8c;
background:#f0f9fb;border-radius:.25rem;margin:.6rem 0 1rem}
.small-note{font-size:.85rem;color:#52606d}
</style>
""", unsafe_allow_html=True)

language = st.sidebar.selectbox("Language / اللغة", ["English", "العربية"])
ar = language == "العربية"
title = "MeteoGuard AI — جودة بيانات الرصد الجوي" if ar else "MeteoGuard AI — Meteorological Data Quality"
intro = (
    "نموذج أولي يدمج عدة أدلة لكشف القراءات المشبوهة، ويحمي الظواهر الجوية المتطرفة الحقيقية، ويرسل الحالات للمراجعة البشرية."
    if ar else
    "An explainable monitoring prototype that combines multiple anomaly signals, protects legitimate weather extremes, and routes suspicious observations for human review."
)
st.markdown(f'<div class="hero"><h1>🌦️ {title}</h1><p>{intro}</p></div>', unsafe_allow_html=True)

names = ["نظرة عامة", "مستكشف التنبيهات", "التقييم", "حول النظام"] if ar else [
    "Overview", "Alert explorer", "Evaluation", "About"
]
overview, explorer, evaluation, about = st.tabs(names)

with overview:
    a, b, c, d = st.columns(4)
    a.metric("Evaluated quality alerts" if not ar else "تنبيهات الجودة المقيمة", f"{len(alerts):,}")
    b.metric("Stations" if not ar else "المحطات", alerts.station_id.nunique())
    c.metric("Variables" if not ar else "المتغيرات", alerts.variable.nunique())
    d.metric(
        "Mean extreme preservation" if not ar else "متوسط الحفاظ على الظواهر المتطرفة",
        f"{extremes.preservation_rate.mean():.1%}",
    )
    note = (
        "These alerts were evaluated in archived replay experiments using public NOAA observations "
        "and controlled sensor-fault scenarios; they are not 19,460 confirmed faults in an operational NCM system."
        if not ar else
        "تم تقييم التنبيهات باستخدام رصدات NOAA العامة وسيناريوهات أعطال مضبوطة، ولا تمثل 19,460 عطلاً مؤكداً في نظام تشغيلي للمركز الوطني للأرصاد."
    )
    st.markdown(f'<div class="notice">{note}</div>', unsafe_allow_html=True)

    left, right = st.columns([1.45, 1])

    with left:
        st.subheader(
            "Station coverage" if not ar else "تغطية المحطات"
        )

        # Prepare one summary record for each station
        station_map = (
            alerts.groupby(
                [
                    "station_id",
                    "station_name",
                    "latitude",
                    "longitude"
                ],
                as_index=False
            )
            .agg(
                alert_count=("timestamp", "size"),
                variable_count=("variable", "nunique"),
                latest_alert=("timestamp", "max")
            )
        )

        # Convert values to readable tooltip text
        station_map["station_id"] = (
            station_map["station_id"].astype(str)
        )

        station_map["latest_alert"] = (
            pd.to_datetime(station_map["latest_alert"])
            .dt.strftime("%Y-%m-%d %H:%M UTC")
        )

        # Interactive station points
        station_layer = pdk.Layer(
            "ScatterplotLayer",
            data=station_map,
            id="weather-stations",
            get_position="[longitude, latitude]",
            get_radius=18000,
            get_fill_color="[15, 108, 189, 190]",
            get_line_color="[255, 255, 255]",
            line_width_min_pixels=1,
            stroked=True,
            filled=True,
            pickable=True,
            auto_highlight=True
        )

        # Initial Saudi Arabia map position
        view_state = pdk.ViewState(
            latitude=24.5,
            longitude=45.0,
            zoom=4.2,
            pitch=0
        )

        # Tooltip shown when the mouse is placed over a station
        tooltip = {
            "html": """
                <div style="font-family: Arial; line-height: 1.6;">
                    <b style="font-size: 15px;">
                        {station_name}
                    </b>
                    <br/>
                    <b>Station ID:</b> {station_id}
                    <br/>
                    <b>Quality alerts:</b> {alert_count}
                    <br/>
                    <b>Variables:</b> {variable_count}
                    <br/>
                    <b>Latest alert:</b> {latest_alert}
                    <br/>
                    <b>Location:</b>
                    {latitude}, {longitude}
                </div>
            """,
            "style": {
                "backgroundColor": "#0f4c5c",
                "color": "white",
                "borderRadius": "8px",
                "padding": "8px"
            }
        }

        station_deck = pdk.Deck(
            map_style=None,
            initial_view_state=view_state,
            layers=[station_layer],
            tooltip=tooltip
        )

        st.pydeck_chart(
            station_deck,
            use_container_width=True,
            height=430
        )

        st.caption(
            "Move the pointer over a station to view its details."
            if not ar
            else
            "ضع المؤشر فوق المحطة لعرض تفاصيلها."
        )

    with right:
        st.subheader(
            "Alert composition"
            if not ar
            else "توزيع أسباب التنبيه"
        )

        rc = (
            alerts.reason.value_counts()
            .rename_axis("Reason")
            .reset_index(name="Alerts")
        )

        fig = px.bar(
            rc.sort_values("Alerts"),
            x="Alerts",
            y="Reason",
            orientation="h",
            color="Alerts",
            color_continuous_scale="Teal"
        )

        fig.update_layout(
            coloraxis_showscale=False,
            margin=dict(l=10, r=10, t=10, b=10)
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )
    st.subheader("Stations in the prototype" if not ar else "المحطات في النموذج الأولي")
    station_summary = (
        alerts.groupby(["station_name", "station_id"], as_index=False)
        .agg(Alerts=("timestamp", "size"), **{"Latest alert": ("timestamp", "max")})
        .rename(columns={"station_name": "Station", "station_id": "Station ID"})
        .sort_values("Alerts", ascending=False)
    )
    st.dataframe(station_summary, use_container_width=True, hide_index=True)

with explorer:
    st.subheader("Investigate and export alerts" if not ar else "استعراض التنبيهات وتصديرها")
    x1, x2, x3 = st.columns(3)
    stations = x1.multiselect("Stations" if not ar else "المحطات",
                              sorted(alerts.station_name.unique()), placeholder="All stations")
    variables = x2.multiselect("Variables" if not ar else "المتغيرات",
                               sorted(alerts.variable.unique()), format_func=lambda x: VAR.get(x, x),
                               placeholder="All variables")
    reasons = x3.multiselect("Alert reasons" if not ar else "أسباب التنبيه",
                             sorted(alerts.reason.unique()), placeholder="All reasons")
    x4, x5 = st.columns([1, 2])
    statuses = x4.multiselect("Review status" if not ar else "حالة المراجعة",
                              sorted(alerts.status.unique()), format_func=lambda x: STATUS.get(x, x),
                              placeholder="All statuses")
    min_prob = x5.slider("Minimum alert probability" if not ar else "الحد الأدنى لاحتمال التنبيه",
                         0.0, 1.0, 0.0, 0.05)

    filtered = alerts.copy()
    if stations: filtered = filtered[filtered.station_name.isin(stations)]
    if variables: filtered = filtered[filtered.variable.isin(variables)]
    if reasons: filtered = filtered[filtered.reason.isin(reasons)]
    if statuses: filtered = filtered[filtered.status.isin(statuses)]
    filtered = filtered[filtered.prob_fusion >= min_prob].copy()
    filtered["variable"] = filtered.variable.map(VAR).fillna(filtered.variable)
    filtered["status"] = filtered.status.map(STATUS).fillna(filtered.status)
    filtered = filtered.rename(columns={
        "timestamp": "Timestamp (UTC)", "station_name": "Station", "variable": "Variable",
        "observed_value": "Observed value", "corrected_v3": "Proposed value",
        "selected_correction_method": "Proposed method",
        "correction_confidence": "Proposal confidence", "prob_fusion": "Alert probability",
        "reason": "Reason", "status": "Review status",
    })
    st.caption(f"{len(filtered):,} matching alerts")
    visible = ["Timestamp (UTC)", "Station", "Variable", "Observed value", "Proposed value",
               "Alert probability", "Reason", "Review status"]
    st.dataframe(
        filtered[visible].sort_values("Timestamp (UTC)", ascending=False),
        use_container_width=True, hide_index=True,
        column_config={"Alert probability": st.column_config.ProgressColumn(
            format="%.2f", min_value=0, max_value=1)}
    )
    st.download_button(
        "Download filtered alerts (CSV)" if not ar else "تنزيل التنبيهات المفلترة (CSV)",
        filtered.to_csv(index=False).encode("utf-8-sig"),
        "meteoguard_filtered_alerts.csv", "text/csv", use_container_width=True
    )
    st.info(
        "Proposed values support decisions; they are not automatically applied and require domain review."
        if not ar else
        "القيم المقترحة مخصصة لدعم القرار، ولا يتم تطبيقها تلقائياً وتتطلب مراجعة مختص."
    )

with evaluation:
    st.subheader("Detection performance" if not ar else "أداء اكتشاف الأعطال")
    m = metrics[metrics.method == "MeteoGuard V3"].copy()
    m["Variable"] = m.variable.map(VAR)
    m["Validation setting"] = m.split.map(SPLIT)
    fig = px.bar(m, x="Variable", y="f1", color="Validation setting", barmode="group",
                 range_y=[0, 1], labels={"f1": "F1 score"},
                 color_discrete_sequence=["#0f6cbd", "#6bb7e9"], text_auto=".2f")
    fig.update_layout(legend_title_text="Validation setting", margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "F1 balances fault-detection precision and recall; higher values indicate more reliable detection."
        if not ar else
        "توازن درجة F1 بين دقة الكشف والاستدعاء؛ وتشير القيم الأعلى إلى كشف أكثر موثوقية."
    )
    q1, q2, q3 = st.columns(3)
    q1.metric("Mean F1 — observed stations", f"{m.loc[m.split == 'seen_time_holdout', 'f1'].mean():.3f}")
    q2.metric("Mean F1 — unseen stations", f"{m.loc[m.split == 'unseen_station', 'f1'].mean():.3f}")
    q3.metric("Maximum false-positive rate", f"{m.false_positive_rate.max():.1%}")

    st.subheader("Preservation of legitimate extremes" if not ar else "الحفاظ على الظواهر المتطرفة الحقيقية")
    e = extremes.copy()
    e["Variable"] = e.variable.map(VAR)
    e["Validation setting"] = e.split.map(SPLIT)
    fig2 = px.bar(e, x="Variable", y="preservation_rate", color="Validation setting",
                  barmode="group", range_y=[0, 1],
                  labels={"preservation_rate": "Preservation rate"},
                  color_discrete_sequence=["#198754", "#7bcf9b"], text_auto=".1%")
    fig2.update_layout(legend_title_text="Validation setting", margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig2, use_container_width=True)
    st.warning(
        "Generalization differs by variable: pressure and wind transfer strongly to unseen stations, "
        "while dew-point detection remains an improvement area."
        if not ar else
        "يختلف التعميم حسب المتغير؛ ينتقل أداء الضغط والرياح جيداً إلى المحطات الجديدة، بينما يظل كشف نقطة الندى مجالاً للتحسين."
    )

with about:
    st.subheader("How MeteoGuard AI works" if not ar else "كيف يعمل MeteoGuard AI")
    if not ar:
        st.markdown("""
1. **Ingest:** Load timestamped observations from multiple stations.
2. **Inspect:** Combine physical rules, temporal behavior, spatial context, and anomaly-model evidence.
3. **Protect extremes:** Reduce the risk of treating legitimate severe weather as a sensor fault.
4. **Triage:** Assign an alert reason and route uncertain cases for human review.
5. **Support decisions:** Display proposed values without modifying source records automatically.

### Prototype scope
- Public NOAA observations and controlled sensor-fault scenarios
- Nine stations and five meteorological variables
- Time-held-out and entirely unseen-station evaluation
- Research and hackathon testing prototype; not an operational NCM system
""")
    else:
        st.markdown("""
1. **الإدخال:** تحميل الرصدات الزمنية من عدة محطات.
2. **الفحص:** دمج القواعد الفيزيائية والسلوك الزمني والسياق المكاني وأدلة نموذج الشذوذ.
3. **حماية الظواهر المتطرفة:** تقليل اعتبار الطقس الشديد الحقيقي عطلاً في المستشعر.
4. **الفرز:** تحديد سبب التنبيه وإرسال الحالات غير المؤكدة للمراجعة البشرية.
5. **دعم القرار:** عرض القيم المقترحة دون تعديل السجلات تلقائياً.

### نطاق النموذج الأولي
- رصدات NOAA عامة وسيناريوهات أعطال مضبوطة
- تسع محطات وخمسة متغيرات جوية
- تقييم زمني وتقييم على محطات غير مستخدمة في التدريب
- نموذج بحثي واختباري للهاكاثون وليس نظاماً تشغيلياً
""")
    st.info(
        "MeteoGuard AI supports quality-control decisions. Operational corrections require domain "
        "validation, audit logging, and authorization by the data owner."
        if not ar else
        "يدعم MeteoGuard AI قرارات مراقبة الجودة، وتتطلب التصحيحات التشغيلية تحقق المختص وسجل تدقيق وموافقة مالك البيانات."
    )

st.markdown('<p class="small-note">MeteoGuard AI V3.1 · Research and hackathon prototype · Public NOAA-derived experimental data</p>',
            unsafe_allow_html=True)
