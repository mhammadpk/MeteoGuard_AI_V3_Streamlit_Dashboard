import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
st.set_page_config(page_title="MeteoGuard AI",page_icon="🌦️",layout="wide")
P=Path(__file__).parent
alerts=pd.read_csv(P/'alerts.csv',parse_dates=['timestamp']); metrics=pd.read_csv(P/'metrics.csv'); extremes=pd.read_csv(P/'extremes.csv')
lang=st.sidebar.selectbox('Language / اللغة',['English','العربية'])
AR=lang=='العربية'
T={'title':'MeteoGuard AI — جودة الرصد الجوي' if AR else 'MeteoGuard AI — Meteorological Data Quality',
   'alerts':'التنبيهات' if AR else 'Alerts','stations':'المحطات' if AR else 'Stations',
   'confidence':'متوسط الثقة' if AR else 'Mean confidence','map':'خريطة المحطات' if AR else 'Station map',
   'table':'مراجعة التنبيهات' if AR else 'Alert review'}
st.title(T['title']); a,b,c=st.columns(3)
a.metric(T['alerts'],f"{len(alerts):,}"); b.metric(T['stations'],alerts.station_id.nunique()); c.metric(T['confidence'],f"{alerts.correction_confidence.mean():.1%}")
st.subheader(T['map']); latest=alerts.sort_values('timestamp').groupby('station_id').tail(1)
st.map(latest,latitude='latitude',longitude='longitude')
st.subheader(T['table']); variable=st.selectbox('Variable',sorted(alerts.variable.unique()))
st.dataframe(alerts[alerts.variable==variable].sort_values('timestamp',ascending=False),use_container_width=True)
st.subheader('Evaluation / التقييم'); fig=px.bar(metrics[metrics.method=='MeteoGuard V3'],x='variable',y='f1',color='split',barmode='group',range_y=[0,1]); st.plotly_chart(fig,use_container_width=True)
st.caption('Research prototype using public NOAA observations and controlled sensor-fault scenarios; not an operational NCM system.')
