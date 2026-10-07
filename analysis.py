"""Reproducible, descriptive telecom customer segmentation analysis."""
from pathlib import Path
import argparse
import json
import sqlite3
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
DIMENSIONS = ['TenureGroup', 'Contract', 'PaymentMethod', 'InternetService',
              'TechSupport', 'gender', 'SeniorCitizen']

def clean_data(raw):
    df = raw.copy()
    df.columns = df.columns.str.strip()
    required = ['customerID', 'tenure', 'MonthlyCharges', 'TotalCharges', 'Churn',
                'Contract', 'PaymentMethod', 'InternetService', 'TechSupport', 'gender', 'SeniorCitizen']
    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(f'Missing columns: {sorted(missing)}')
    for col in df.select_dtypes(include=['object', 'string']):
        df[col] = df[col].astype('string').str.strip()
    before = len(df)
    df = df.drop_duplicates().copy()
    if df.empty:
        raise ValueError('The dataset is empty.')
    if df.customerID.isna().any() or df.customerID.eq('').any() or df.customerID.duplicated().any():
        raise ValueError('Customer IDs must be nonempty and unique after exact duplicate removal.')
    for col in ['tenure', 'MonthlyCharges', 'TotalCharges']:
        original = df[col].astype('string')
        converted = pd.to_numeric(df[col], errors='coerce')
        invalid = converted.isna() & original.notna() & original.ne('')
        if invalid.any():
            raise ValueError(f'{col} contains invalid numeric values.')
        df[col] = converted
    for col in ['tenure', 'MonthlyCharges']:
        if df[col].isna().any() or not np.isfinite(df[col]).all() or df[col].lt(0).any():
            raise ValueError(f'{col} must contain finite, nonnegative numbers.')
    if df.tenure.mod(1).ne(0).any():
        raise ValueError('tenure must contain whole months.')
    totals = df.TotalCharges.dropna()
    if not np.isfinite(totals).all() or totals.lt(0).any():
        raise ValueError('TotalCharges must be nonnegative and finite when supplied.')
    if df.Churn.isna().any() or not df.Churn.isin(['Yes', 'No']).all():
        raise ValueError('Churn must contain only Yes or No.')
    for col in DIMENSIONS[1:]:
        df[col] = df[col].astype('string').fillna('Unknown').replace('', 'Unknown')
    df['ChurnFlag'] = df.Churn.eq('Yes').astype(int)
    df['TenureGroup'] = pd.cut(df.tenure, [-1, 12, 36, float('inf')],
                                labels=['0–12 months', '13–36 months', '37+ months'])
    quality = {'input_rows': before, 'clean_rows': len(df),
               'exact_duplicates_removed': before-len(df),
               'missing_total_charges_preserved': int(df.TotalCharges.isna().sum())}
    return df, quality

def summary(df, dimension):
    result = df.groupby(dimension, observed=True, dropna=False).agg(
        customers=('customerID', 'size'), churned=('ChurnFlag', 'sum'),
        average_monthly_charge=('MonthlyCharges', 'mean')).reset_index()
    result['churn_rate_pct'] = result.churned / result.customers * 100
    return result

def metrics(df):
    return {'customers': len(df), 'churned_customers': int(df.ChurnFlag.sum()),
            'churn_rate_pct': float(df.ChurnFlag.mean()*100),
            'average_monthly_charge': float(df.MonthlyCharges.mean()),
            'monthly_charges_of_churned_customers': float(df.loc[df.ChurnFlag.eq(1), 'MonthlyCharges'].sum())}

def run(input_path, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    charts = output / 'charts'
    charts.mkdir(exist_ok=True)
    df, quality = clean_data(pd.read_csv(input_path, dtype={'customerID': 'string'}))
    df.to_csv(output/'customers_clean.csv', index=False)
    kpis = metrics(df)
    (output/'kpis.json').write_text(json.dumps(kpis, indent=2), encoding='utf-8')
    (output/'data_quality.json').write_text(json.dumps(quality, indent=2), encoding='utf-8')
    plt.rcParams.update({'figure.dpi': 130, 'axes.spines.top': False, 'axes.spines.right': False})
    for dimension in DIMENSIONS:
        table = summary(df, dimension)
        table.to_csv(output/f'by_{dimension}.csv', index=False)
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.barh(table[dimension].astype(str), table.churn_rate_pct, color='#247b91')
        for i, row in table.iterrows():
            ax.text(row.churn_rate_pct+0.5, i, f'{row.churn_rate_pct:.1f}% (n={row.customers:,})', va='center', fontsize=9)
        ax.set(xlabel='Observed churn rate (%)', title=f'Churn by {dimension}', xlim=(0, max(20, table.churn_rate_pct.max()*1.4)))
        fig.tight_layout()
        fig.savefig(charts/f'churn_by_{dimension}.png')
        plt.close(fig)
    for column in ['tenure', 'MonthlyCharges']:
        fig, ax = plt.subplots(figsize=(8, 4))
        for label, color in [('No', '#247b91'), ('Yes', '#e68a48')]:
            ax.hist(df.loc[df.Churn.eq(label), column], bins=20, alpha=.6, label=f'Churn: {label}', color=color)
        ax.set(xlabel=column, ylabel='Customers', title=f'{column} distribution')
        ax.legend()
        fig.tight_layout()
        fig.savefig(charts/f'{column}_distribution.png')
        plt.close(fig)
    segments = df.groupby(['TenureGroup', 'Contract'], observed=True).agg(
        customers=('customerID', 'size'), churned=('ChurnFlag', 'sum'),
        average_monthly_charge=('MonthlyCharges', 'mean')).reset_index()
    segments['churn_rate_pct'] = segments.churned/segments.customers*100
    segments['difference_from_overall_pp'] = segments.churn_rate_pct-kpis['churn_rate_pct']
    segments['eligible_for_review'] = segments.customers.ge(30)
    segments.sort_values('churn_rate_pct', ascending=False).to_csv(output/'segment_comparison.csv', index=False)
    with sqlite3.connect(output/'customers.sqlite') as conn:
        df.to_sql('customers', conn, if_exists='replace', index=False)
    top = segments.loc[segments.eligible_for_review].sort_values('churn_rate_pct', ascending=False).head(1)
    lines = ['# Analysis results', '', f"Analyzed {len(df):,} customers; observed churn rate: {kpis['churn_rate_pct']:.2f}%.", '']
    if not top.empty:
        row = top.iloc[0]
        lines += [f"Highest observed tenure/contract segment with at least 30 customers: {row.TenureGroup}, {row.Contract}; {row.churn_rate_pct:.2f}% churn (n={row.customers:,}).", '']
    lines += ['These are descriptive associations, not causal effects or predictions.',
              'Review onboarding, pricing and support feedback for the identified segments before designing a retention test.',
              'Use a randomized pilot and measure incremental retention, offer cost and customer complaints.', '',
              'Monthly charges associated with churned customers are a snapshot sum, not realized revenue loss or forecast savings.']
    (output/'findings.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(json.dumps(kpis, indent=2))
    print(f'Outputs: {output.resolve()}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT/'data/telco.csv')
    parser.add_argument('--output', type=Path, default=ROOT/'results')
    args = parser.parse_args()
    run(args.input, args.output)
