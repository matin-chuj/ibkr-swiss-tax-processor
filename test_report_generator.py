"""
Unit tests for Basel-Landschaft Tax Report Generator
"""

import unittest
import json
import os
from pathlib import Path
from tax_calculator_bl import TaxCalculatorBL
from report_generator_bl import ReportGeneratorBL


class TestTaxCalculatorBL(unittest.TestCase):
    """Test cases for TaxCalculatorBL"""

    def setUp(self):
        """Set up test fixtures"""
        self.calculator = TaxCalculatorBL()
        
        self.sample_data = {
            'transactions': [
                {'type': 'Stocks', 'symbol': 'AAPL', 'proceeds_chf': 1000, 'commission_chf': 5},
                {'type': 'Forex', 'symbol': 'EUR.USD', 'proceeds_chf': 50, 'commission_chf': 0},
                {'type': 'Stocks', 'symbol': 'MSFT', 'proceeds_chf': -500, 'commission_chf': 3}
            ],
            'dividends': [
                {'symbol': 'AAPL', 'amount_chf': 100, 'type': 'Dividend'},
                {'symbol': 'MSFT', 'amount_chf': 50, 'type': 'Dividend'},
                {'amount_chf': 10, 'type': 'Interest'}
            ],
            'taxes': [
                {'amount_chf': 15, 'country': 'US'}
            ],
            'fees': [
                {'amount_chf': 10, 'type': 'Account fee'}
            ],
            'open_positions': [
                {'symbol': 'AAPL', 'value_chf': 5000, 'currency': 'USD', 'quantity': 10},
                {'symbol': 'MSFT', 'value_chf': 3000, 'currency': 'USD', 'quantity': 5}
            ]
        }

    def test_wealth_tax_calculation(self):
        """Test wealth tax calculation"""
        # Test normal wealth
        result = self.calculator.calculate_wealth_tax(10000)
        self.assertEqual(result['taxable_wealth'], 10000)
        self.assertEqual(result['wealth_tax'], 10000 * 0.0008)
        self.assertFalse(result['exemption_applied'])
        
        # Test below threshold
        result = self.calculator.calculate_wealth_tax(40)
        self.assertEqual(result['taxable_wealth'], 0)
        self.assertEqual(result['wealth_tax'], 0)
        self.assertTrue(result['exemption_applied'])

    def test_income_tax_calculation(self):
        """Test income tax calculation"""
        # Test normal income
        result = self.calculator.calculate_income_tax(1000, 100)
        self.assertEqual(result['gross_income'], 1000)
        self.assertEqual(result['deductible_costs'], 100)
        self.assertEqual(result['taxable_income'], 900)
        self.assertEqual(result['income_tax'], 900 * 0.1055)
        
        # Test below threshold
        result = self.calculator.calculate_income_tax(40, 0)
        self.assertEqual(result['income_tax'], 0)
        self.assertTrue(result['exemption_applied'])

    def test_foreign_tax_credit(self):
        """Test foreign tax credit calculation"""
        foreign_taxes = {
            'US': 100,
            'UK': 50
        }
        
        result = self.calculator.calculate_foreign_tax_credit(foreign_taxes)
        self.assertEqual(result['total_foreign_tax'], 150)
        self.assertEqual(result['us_withholding_tax'], 100)
        self.assertEqual(result['other_foreign_tax'], 50)
        # 100% of US + 80% of others
        self.assertEqual(result['creditable_amount'], 100 + 50 * 0.8)

    def test_capital_gains_calculation(self):
        """Test capital gains/losses calculation"""
        result = self.calculator.calculate_capital_gains_summary(self.sample_data['transactions'])
        
        self.assertEqual(result['realized_gains'], 1050)  # 1000 + 50
        self.assertEqual(result['realized_losses'], 500)
        self.assertEqual(result['net_capital_gain_loss'], 550)

    def test_income_categorization(self):
        """Test income categorization by source"""
        dividends = self.sample_data['dividends']
        interests = [d for d in dividends if d.get('type') == 'Interest']
        div_only = [d for d in dividends if d.get('type') != 'Interest']
        
        result = self.calculator.categorize_income_by_source(div_only, interests)
        
        self.assertIn('swiss', result)
        self.assertIn('foreign', result)
        self.assertIn('interest', result)
        self.assertEqual(result['interest']['total'], 10)

    def test_fx_gains_losses(self):
        """Test FX gains/losses calculation"""
        forex_txns = [t for t in self.sample_data['transactions'] if t.get('type') == 'Forex']
        
        result = self.calculator.calculate_fx_gains_losses(forex_txns)
        
        self.assertEqual(result['fx_gains'], 50)
        self.assertEqual(result['fx_losses'], 0)
        self.assertEqual(result['net_fx_result'], 50)

    def test_total_costs(self):
        """Test total costs calculation"""
        result = self.calculator.calculate_total_costs(
            self.sample_data['transactions'],
            self.sample_data['fees']
        )
        
        self.assertEqual(result['transaction_fees'], 8)  # 5 + 3
        self.assertEqual(result['account_fees'], 10)
        self.assertEqual(result['total_deductible_costs'], 18)

    def test_complete_tax_summary(self):
        """Test complete tax summary generation"""
        summary = self.calculator.generate_tax_summary(self.sample_data)
        
        # Check structure
        self.assertIn('wealth', summary)
        self.assertIn('income', summary)
        self.assertIn('capital_gains', summary)
        self.assertIn('fx_result', summary)
        self.assertIn('costs', summary)
        self.assertIn('foreign_tax', summary)
        self.assertIn('tax_liability', summary)
        
        # Check wealth
        self.assertEqual(summary['wealth']['total_assets_chf'], 8000)
        
        # Check income
        self.assertEqual(summary['income']['total_income_chf'], 160)
        
        # Check tax liability
        self.assertIn('net_tax_liability', summary['tax_liability'])


class TestReportGeneratorBL(unittest.TestCase):
    """Test cases for ReportGeneratorBL"""

    def setUp(self):
        """Set up test fixtures"""
        self.sample_data = {
            'transactions': [
                {'type': 'Stocks', 'symbol': 'AAPL', 'proceeds_chf': 1000, 'commission_chf': 5}
            ],
            'dividends': [
                {'symbol': 'AAPL', 'amount_chf': 100, 'type': 'Dividend'}
            ],
            'taxes': [
                {'amount_chf': 15, 'country': 'US'}
            ],
            'fees': [
                {'amount_chf': 10, 'type': 'Account fee'}
            ],
            'open_positions': [
                {'symbol': 'AAPL', 'value_chf': 5000, 'currency': 'USD', 'quantity': 10}
            ]
        }
        
        self.generator = ReportGeneratorBL(self.sample_data)
        self.output_dir = Path('test_output')
        self.output_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up test files"""
        if self.output_dir.exists():
            for file in self.output_dir.glob('*'):
                file.unlink()
            self.output_dir.rmdir()

    def test_generator_initialization(self):
        """Test report generator initialization"""
        self.assertIsNotNone(self.generator.tax_calculator)
        self.assertIsNotNone(self.generator.tax_summary)
        self.assertEqual(self.generator.tax_summary['canton'], 'Basel-Landschaft')

    def test_excel_report_generation(self):
        """Test Excel report generation"""
        output_file = self.output_dir / 'test_report.xlsx'
        self.generator.generate_excel_report(str(output_file))
        
        self.assertTrue(output_file.exists())
        self.assertGreater(output_file.stat().st_size, 0)

    def test_pdf_report_generation(self):
        """Test PDF report generation"""
        output_file = self.output_dir / 'test_report.pdf'
        self.generator.generate_pdf_report(str(output_file))
        
        self.assertTrue(output_file.exists())
        self.assertGreater(output_file.stat().st_size, 0)

    def test_json_report_generation(self):
        """Test JSON report generation"""
        output_file = self.output_dir / 'test_report.json'
        self.generator.generate_json_report(str(output_file))
        
        self.assertTrue(output_file.exists())
        
        # Validate JSON structure
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        self.assertIn('metadata', data)
        self.assertIn('sections', data)
        self.assertIn('tax_summary', data)
        self.assertEqual(data['metadata']['canton'], 'Basel-Landschaft')

    def test_all_reports_generation(self):
        """Test generation of all report formats"""
        reports = self.generator.generate_all_reports(str(self.output_dir))
        
        self.assertIn('excel', reports)
        self.assertIn('pdf', reports)
        self.assertIn('json', reports)
        
        # Check all files exist
        for format_type, path in reports.items():
            self.assertTrue(Path(path).exists())


class TestConfigurationLoading(unittest.TestCase):
    """Test configuration loading"""

    def test_config_file_loading(self):
        """Test loading from config file"""
        calculator = TaxCalculatorBL('basellandschaft_config.json')
        
        self.assertEqual(calculator.canton, 'Basel-Landschaft')
        self.assertEqual(calculator.tax_year, 2025)
        self.assertEqual(calculator.income_tax_rate, 0.1055)
        self.assertEqual(calculator.wealth_tax_rate, 0.0008)

    def test_default_config_fallback(self):
        """Test fallback to default config"""
        calculator = TaxCalculatorBL('nonexistent_config.json')
        
        # Should still work with defaults
        self.assertEqual(calculator.canton, 'Basel-Landschaft')
        self.assertIsNotNone(calculator.income_tax_rate)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases"""

    def setUp(self):
        self.calculator = TaxCalculatorBL()

    def test_empty_data(self):
        """Test with empty data"""
        empty_data = {
            'transactions': [],
            'dividends': [],
            'taxes': [],
            'fees': [],
            'open_positions': []
        }
        
        summary = self.calculator.generate_tax_summary(empty_data)
        
        self.assertEqual(summary['wealth']['total_assets_chf'], 0)
        self.assertEqual(summary['income']['total_income_chf'], 0)

    def test_zero_income(self):
        """Test with zero income"""
        result = self.calculator.calculate_income_tax(0, 0)
        
        self.assertEqual(result['income_tax'], 0)

    def test_negative_costs(self):
        """Test handling of edge cases in costs"""
        result = self.calculator.calculate_income_tax(100, 200)
        
        # Taxable income should not be negative
        self.assertEqual(result['taxable_income'], 0)
        self.assertEqual(result['income_tax'], 0)


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTaxCalculatorBL))
    suite.addTests(loader.loadTestsFromTestCase(TestReportGeneratorBL))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigurationLoading))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    result = run_tests()
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)
