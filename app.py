"""Local dashboard: python -m streamlit run app.py"""
import pandas as pd
import streamlit as st
from analysis import ROOT, clean_data, metrics, summary

st.set_page_config(page_title='Customer Retention Analysis', layout='wide')
st.title('Customer Retention Analysis')
st.caption('Telecom customer segments and observed churn patterns')
upload = st.sidebar.file_uploader('Upload a Telco-format CSV (optional)', type='csv')
try:
    df, quality = clean_data(pd.read_csv(upload if upload is not None else ROOT/'data/telco.csv'))
except (ValueError, OSError) as exc:
    st.error(str(exc))
    st.stop()
contracts = st.sidebar.multiselect('Contract', sorted(df.Contract.unique()), default=sorted(df.Contract.unique()))
services = st.sidebar.multiselect('Internet service', sorted(df.InternetService.unique()), default=sorted(df.InternetService.unique()))
max_tenure = max(1, int(df.tenure.max()))
low, high = st.sidebar.slider('Tenure (months)', 0, max_tenure, (0, max_tenure))
view = df[df.Contract.isin(contracts) & df.InternetService.isin(services) & df.tenure.between(low, high)]
if view.empty:
    st.info('No customers match these filters.')
    st.stop()
k = metrics(view)
for col, label, value in zip(st.columns(4), ['Customers', 'Churned', 'Churn rate', 'Average monthly charge'],
                            [f"{k['customers']:,}", f"{k['churned_customers']:,}", f"{k['churn_rate_pct']:.1f}%", f"{k['average_monthly_charge']:.2f}"]):
    col.metric(label, value)
st.caption('Every metric uses the filtered population. Charge values retain the source dataset’s currency units.')
dimension = st.selectbox('Compare segments', ['TenureGroup', 'Contract', 'PaymentMethod', 'InternetService', 'TechSupport', 'gender', 'SeniorCitizen'])
table = summary(view, dimension)
st.bar_chart(table.set_index(dimension)['churn_rate_pct'], y_label='Churn rate (%)')
st.dataframe(table, hide_index=True, use_container_width=True)
st.download_button('Download segment summary', table.to_csv(index=False), 'segment_summary.csv', 'text/csv')
with st.expander('Data quality and interpretation'):
    st.json(quality)
    st.write('Missing TotalCharges are preserved. Segment rates describe this sample; small groups may be unstable. Differences do not establish causation. No predictive model is used.')
