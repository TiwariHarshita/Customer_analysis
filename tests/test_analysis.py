import unittest
import pandas as pd
from analysis import ROOT, clean_data, metrics, summary

class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.raw = pd.read_csv(ROOT/'data/telco.csv').head(4).copy()
    def test_boundaries_and_rates(self):
        self.raw['tenure'] = [12, 13, 36, 37]
        self.raw['Churn'] = ['Yes', 'No', 'Yes', 'No']
        df, _ = clean_data(self.raw)
        self.assertEqual(df.TenureGroup.astype(str).tolist(), ['0–12 months', '13–36 months', '13–36 months', '37+ months'])
        self.assertEqual(metrics(df)['churn_rate_pct'], 50)
        self.assertEqual(summary(df, 'TenureGroup').customers.sum(), 4)
    def test_conflicting_ids_rejected(self):
        self.raw.loc[1, 'customerID'] = self.raw.loc[0, 'customerID']
        with self.assertRaises(ValueError): clean_data(self.raw)
    def test_missing_totals_preserved(self):
        self.raw['TotalCharges'] = self.raw['TotalCharges'].astype(str)
        self.raw.loc[0, 'TotalCharges'] = ' '
        df, audit = clean_data(self.raw)
        self.assertTrue(pd.isna(df.loc[0, 'TotalCharges']))
        self.assertEqual(audit['missing_total_charges_preserved'], 1)
    def test_invalid_churn_rejected(self):
        self.raw.loc[0, 'Churn'] = 'Maybe'
        with self.assertRaises(ValueError): clean_data(self.raw)

if __name__ == '__main__': unittest.main()
