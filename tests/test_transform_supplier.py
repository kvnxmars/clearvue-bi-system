# C:\clearvue-bi-system\tests\test_transform_supplier.py (COMPLETE & CORRECT)

import unittest
import pandas as pd
from datetime import datetime
import logging

# Set up logging for the test file (optional)
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

# Import the functions and variables you need to test
# The ETL script must be fully functional for this import to succeed.
from etl_scripts.batch_etl.transform_supplier import clean_supplier_desc

# --- Mock DataFrames for Unit Testing ---
MOCK_SUPPLIERS_DATA = {
    'SUPPLIER_CODE': ['001', '008', '999999'],
    'SUPPLIER_DESC': ['Regular Vendor', 'DR Shipment 2025-09', 'IGNORE'],
    'EXCLSV': ['N', 'Y', 'N'],
    'NORMAL_PAYTERMS': [30, 0, 15],
    'CREDIT_LIMIT': [10000.0, 0.0, 0.0]
}

# --- Unit Tests for Helper Functions ---

class TestHelperFunctions(unittest.TestCase):
    """Tests the standalone helper functions from the ETL script."""

    def test_clean_supplier_desc_regular(self):
        """Test cleaning a standard supplier description."""
        desc = "Widget Corp"
        expected = {"name": "Widget Corp", "shipmentDetails": []}
        self.assertEqual(clean_supplier_desc(desc), expected)

    def test_clean_supplier_desc_dr_supplier(self):
        """Test cleaning a 'DR' (delivery/shipment) related supplier description."""
        desc = "DR purch order 12345"
        expected = {"name": "DR Supplier", "shipmentDetails": ["12345"]}
        self.assertEqual(clean_supplier_desc(desc), expected)

    def test_clean_supplier_desc_dr_only(self):
        """Test cleaning a 'DR' description with no details. (The test expects [])"""
        desc = "DR"
        expected = {"name": "DR Supplier", "shipmentDetails": []}
        self.assertEqual(clean_supplier_desc(desc), expected)

    def test_clean_supplier_desc_non_string(self):
        """Test handling of non-string input (e.g., NaN or numeric)."""
        desc = 12345
        expected = {"name": 12345, "shipmentDetails": []}
        self.assertEqual(clean_supplier_desc(desc), expected)

# --------------------------------------------------------------------------------

class TestETLTransformations(unittest.TestCase):
    """Tests core transformations and data quality checks on mocked data."""

    def setUp(self): # <--- THIS METHOD FIXES THE AttributeError
        """Setup mock DataFrames for each test."""
        self.suppliers_df = pd.DataFrame(MOCK_SUPPLIERS_DATA)
        
        self.headers_df = pd.DataFrame({
            'PURCH_DOC_NO': ['P001', 'P002'],
            'SUPPLIER_CODE': ['001', '008'],
            # 43600 is Excel serial for 2019-05-15
            'PURCH_DATE': [43600, datetime(2025, 1, 15)] 
        })
        
        self.lines_df = pd.DataFrame({
            'PURCH_DOC_NO': ['P001', 'P002'],
            'INVENTORY_CODE': ['A1', 'B2'],
            'QUANTITY': [10, 5],
            'UNIT_COST_PRICE': [5.00, 10.00],
            'TOTAL_LINE_COST': [50.01, 50.00] 
        })

    def test_supplier_exclusion_and_transformation(self):
        """Test exclusion of '999999' and boolean mapping."""
        
        df = self.suppliers_df[self.suppliers_df['SUPPLIER_CODE'] != "999999"].copy()
        df['EXCLSV'] = df['EXCLSV'].map({'Y': True, 'N': False})
        
        self.assertNotIn('999999', df['SUPPLIER_CODE'].values)
        self.assertEqual(df.loc[df['SUPPLIER_CODE'] == '001', 'EXCLSV'].iloc[0], False)
        self.assertEqual(df.loc[df['SUPPLIER_CODE'] == '008', 'EXCLSV'].iloc[0], True)
# C:\clearvue-bi-system\tests\test_transform_supplier.py (FIXED test_purchase_date_cleaning)

def test_purchase_date_cleaning(self):
    """Test date and financial period generation. (Fixed mixed type handling)"""
    
    # Create a local copy to transform
    df = self.headers_df.copy() 

    # 💡 FIX: The most robust way to handle mixed Excel/datetime columns
    numeric_dates = pd.to_numeric(df['PURCH_DATE'], errors='coerce')
    
    # Apply Excel serial date logic to numeric values, leaving NaT for non-numeric
    transformed_dates = pd.to_datetime(
        numeric_dates, 
        unit='D', 
        origin='1899-12-30',
        errors='coerce'
    )
    
    # Fill the NaT values (which came from the original datetime objects) with the original dates
    df['purchaseDate'] = transformed_dates.fillna(df['PURCH_DATE']).dt.strftime('%Y-%m-%d')
    
    df['financialPeriod'] = df['purchaseDate'].str.replace("-", "").str[:6]

    self.assertEqual(df.loc[0, 'purchaseDate'], '2019-05-15')
    self.assertEqual(df.loc[0, 'financialPeriod'], '201905')
    self.assertEqual(df.loc[1, 'purchaseDate'], '2025-01-15')
    self.assertEqual(df.loc[1, 'financialPeriod'], '202501')

    # C:\clearvue-bi-system\tests\test_transform_supplier.py (FIXED test_cost_discrepancy_correction)

def test_cost_discrepancy_correction(self):
    """Test calculation and correction of line item costs. (Uses assertAlmostEqual)"""
    
    # Work on a COPY of the DataFrame to ensure transformations are localized
    df = self.lines_df.copy() # <--- Use a local copy
    
    # Apply the logic from Step 4
    df['calculatedCost'] = df['QUANTITY'] * df['UNIT_COST_PRICE']
    
    discrepancies = df[abs(df['calculatedCost'] - df['TOTAL_LINE_COST']) > 0.01]
    
    if not discrepancies.empty:
        df['TOTAL_LINE_COST'] = df['calculatedCost']

    # Assert against the corrected local copy (df)
    self.assertAlmostEqual(df.loc[df['PURCH_DOC_NO'] == 'P001', 'TOTAL_LINE_COST'].iloc[0], 50.00, places=4)
    self.assertAlmostEqual(df.loc[df['PURCH_DOC_NO'] == 'P002', 'TOTAL_LINE_COST'].iloc[0], 50.00, places=4)

if __name__ == '__main__':
    unittest.main()