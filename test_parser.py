"""
Unit tests for IBKR Activity Statement Parser
"""

import unittest
import os
import tempfile
from datetime import datetime
from parser import IBKRActivityStatementParser, parse_ibkr_activity_statement


class TestIBKRActivityStatementParser(unittest.TestCase):
    """Test cases for IBKRActivityStatementParser"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_csv_content = """Statement,Header,Field Name,Field Value
Statement,Data,BrokerName,Interactive Brokers (U.K.) Limited
Statement,Data,Account,U11673931
Statement,Data,Period,January 1 2025 - December 3 2025
Statement,Data,Base Currency,CHF
Statement,Data,Account Type,Individual
---,---,---,---
Net Asset Value,Header,Total,CHF
Net Asset Value,Data,Starting Value,100000.00
Net Asset Value,Data,Ending Value,125000.50
---,---,---,---
Trades,Header,Currency,Symbol,Date/Time,Quantity,T. Price,Proceeds,Comm/Fee,Basis,Realized P/L
Trades,Data,USD,AAPL,2025-11-15,100,150.00,-15000.00,1.50,14500.00,498.50
Trades,Data,EUR,BMW,2025-11-20,-50,85.50,4275.00,2.00,4000.00,273.00
---,---,---,---
Dividends,Header,Currency,Symbol,Date,Amount
Dividends,Data,USD,AAPL,2025-11-01,25.50
Dividends,Data,EUR,BMW,2025-11-15,15.75
Dividends,Data,CHF,NESN,2025-10-30,50.00
---,---,---,---
Withholding Tax,Header,Currency,Symbol,Date,Amount,Country
Withholding Tax,Data,USD,AAPL,2025-11-01,-7.65,United States
Withholding Tax,Data,EUR,BMW,2025-11-15,-3.94,Germany
---,---,---,---
Interest,Header,Currency,Date,Description,Amount
Interest,Data,USD,2025-11-30,USD Credit Interest,5.25
Interest,Data,EUR,2025-11-30,EUR Credit Interest,3.10
---,---,---,---
Fees,Header,Subtitle,Currency,Date,Amount
Fees,Data,Activity Fee,USD,2025-11-01,-10.00
Fees,Data,Market Data,CHF,2025-11-15,-25.00
---,---,---,---
Open Positions,Header,Symbol,Currency,Quantity,Close Price,Mkt Value,Unrealized P/L
Open Positions,Data,AAPL,USD,100,155.00,15500.00,500.00
Open Positions,Data,BMW,EUR,50,88.00,4400.00,125.00
---,---,---,---
Cash Report,Header,Currency,Starting Cash,Ending Cash
Cash Report,Data,CHF,50000.00,55000.00
Cash Report,Data,USD,30000.00,25000.00
Cash Report,Data,EUR,10000.00,12000.00
"""
        
        # Create temporary CSV file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        self.temp_file.write(self.test_csv_content)
        self.temp_file.close()
        
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_parser_initialization(self):
        """Test parser initialization"""
        parser = IBKRActivityStatementParser(self.temp_file.name)
        self.assertEqual(parser.csv_file_path, self.temp_file.name)
        self.assertEqual(parser.raw_data, [])
        self.assertEqual(parser.sections, {})
    
    def test_read_csv(self):
        """Test CSV reading"""
        parser = IBKRActivityStatementParser(self.temp_file.name)
        parser._read_csv()
        self.assertGreater(len(parser.raw_data), 0)
        self.assertEqual(parser.raw_data[0][0], 'Statement')
    
    def test_identify_sections(self):
        """Test section identification"""
        parser = IBKRActivityStatementParser(self.temp_file.name)
        parser._read_csv()
        parser._identify_sections()
        
        # Check that sections were found
        self.assertIn('Statement', parser.sections)
        self.assertIn('Trades', parser.sections)
        self.assertIn('Dividends', parser.sections)
        self.assertIn('Withholding Tax', parser.sections)
    
    def test_extract_account_info(self):
        """Test account information extraction"""
        parser = IBKRActivityStatementParser(self.temp_file.name)
        parser._read_csv()
        parser._identify_sections()
        parser._extract_account_info()
        
        # Check extracted data
        self.assertIn('base_currency', parser.account_info)
        self.assertEqual(parser.account_info['base_currency'], 'CHF')
        self.assertIn('account_type', parser.account_info)
        self.assertEqual(parser.account_info['account_type'], 'Individual')
    
    def test_extract_nav(self):
        """Test NAV extraction"""
        parser = IBKRActivityStatementParser(self.temp_file.name)
        parser._read_csv()
        parser._identify_sections()
        parser._extract_nav()
        
        # Check NAV data
        self.assertIn('beginning', parser.nav)
        self.assertIn('ending', parser.nav)
    
    def test_extract_transactions(self):
        """Test transaction extraction"""
        parser = IBKRActivityStatementParser(self.temp_file.name)
        parser._read_csv()
        parser._identify_sections()
        parser._extract_transactions()
        
        # Check transactions
        self.assertGreater(len(parser.transactions), 0)
        
        # Check first transaction
        if parser.transactions:
            tx = parser.transactions[0]
            self.assertIn('symbol', tx)
            self.assertIn('date', tx)
            self.assertIn('quantity', tx)
    
    def test_extract_dividends(self):
        """Test dividend extraction"""
        parser = IBKRActivityStatementParser(self.temp_file.name)
        parser._read_csv()
        parser._identify_sections()
        parser._extract_dividends()
        
        # Check dividends
        self.assertGreater(len(parser.dividends), 0)
        
        # Check first dividend
        if parser.dividends:
            div = parser.dividends[0]
            self.assertIn('symbol', div)
            self.assertIn('date', div)
            self.assertIn('amount', div)
    
    def test_extract_taxes(self):
        """Test tax extraction"""
        parser = IBKRActivityStatementParser(self.temp_file.name)
        parser._read_csv()
        parser._identify_sections()
        parser._extract_taxes()
        
        # Check taxes
        self.assertGreater(len(parser.taxes), 0)
        
        # Check first tax
        if parser.taxes:
            tax = parser.taxes[0]
            self.assertIn('symbol', tax)
            self.assertIn('date', tax)
            self.assertIn('amount', tax)
            self.assertGreater(tax['amount'], 0)  # Should be absolute value
    
    def test_extract_fees(self):
        """Test fee extraction"""
        parser = IBKRActivityStatementParser(self.temp_file.name)
        parser._read_csv()
        parser._identify_sections()
        parser._extract_fees()
        
        # Check fees
        self.assertGreater(len(parser.fees), 0)
    
    def test_extract_interest(self):
        """Test interest extraction"""
        parser = IBKRActivityStatementParser(self.temp_file.name)
        parser._read_csv()
        parser._identify_sections()
        parser._extract_interest()
        
        # Check interest
        self.assertGreater(len(parser.interest), 0)
    
    def test_extract_open_positions(self):
        """Test open positions extraction"""
        parser = IBKRActivityStatementParser(self.temp_file.name)
        parser._read_csv()
        parser._identify_sections()
        parser._extract_open_positions()
        
        # Check open positions
        self.assertGreater(len(parser.open_positions), 0)
        
        # Check first position
        if parser.open_positions:
            pos = parser.open_positions[0]
            self.assertIn('symbol', pos)
            self.assertIn('quantity', pos)
    
    def test_extract_forex_balances(self):
        """Test forex balance extraction"""
        parser = IBKRActivityStatementParser(self.temp_file.name)
        parser._read_csv()
        parser._identify_sections()
        parser._extract_forex_balances()
        
        # Check forex balances
        self.assertGreater(len(parser.forex_balances), 0)
        
        # Check first balance
        if parser.forex_balances:
            balance = parser.forex_balances[0]
            self.assertIn('currency', balance)
            self.assertIn('amount', balance)
    
    def test_parse_date_iso_format(self):
        """Test date parsing - ISO format"""
        parser = IBKRActivityStatementParser(self.temp_file.name)
        
        # Test ISO format
        date = parser._parse_date('2025-12-03')
        self.assertEqual(date, '2025-12-03')
    
    def test_parse_date_dot_format(self):
        """Test date parsing - dot format"""
        parser = IBKRActivityStatementParser(self.temp_file.name)
        
        # Test DD.MM.YYYY format
        date = parser._parse_date('03.12.2025')
        self.assertEqual(date, '2025-12-03')
    
    def test_parse_date_slash_format(self):
        """Test date parsing - slash format"""
        parser = IBKRActivityStatementParser(self.temp_file.name)
        
        # Test DD/MM/YYYY format
        date = parser._parse_date('03/12/2025')
        self.assertEqual(date, '2025-12-03')
    
    def test_parse_date_invalid(self):
        """Test date parsing - invalid date"""
        parser = IBKRActivityStatementParser(self.temp_file.name)
        
        # Test invalid date
        date = parser._parse_date('invalid')
        self.assertIsNone(date)
        
        # Test empty string
        date = parser._parse_date('')
        self.assertIsNone(date)
    
    def test_parse_amount_simple(self):
        """Test amount parsing - simple number"""
        parser = IBKRActivityStatementParser(self.temp_file.name)
        
        # Test simple number
        amount = parser._parse_amount('1000.50')
        self.assertEqual(amount, 1000.50)
    
    def test_parse_amount_with_comma_thousands(self):
        """Test amount parsing - with comma thousands separator"""
        parser = IBKRActivityStatementParser(self.temp_file.name)
        
        # Test American format (comma as thousands)
        amount = parser._parse_amount('1,000.50')
        self.assertEqual(amount, 1000.50)
        
        # Test multiple thousands
        amount = parser._parse_amount('1,234,567.89')
        self.assertEqual(amount, 1234567.89)
    
    def test_parse_amount_with_comma_decimal(self):
        """Test amount parsing - with comma as decimal separator"""
        parser = IBKRActivityStatementParser(self.temp_file.name)
        
        # Test European format (comma as decimal)
        amount = parser._parse_amount('1000,50')
        self.assertEqual(amount, 1000.50)
    
    def test_parse_amount_negative(self):
        """Test amount parsing - negative numbers"""
        parser = IBKRActivityStatementParser(self.temp_file.name)
        
        # Test negative with minus sign
        amount = parser._parse_amount('-1000.50')
        self.assertEqual(amount, -1000.50)
        
        # Test negative with parentheses
        amount = parser._parse_amount('(1000.50)')
        self.assertEqual(amount, -1000.50)
    
    def test_parse_amount_invalid(self):
        """Test amount parsing - invalid input"""
        parser = IBKRActivityStatementParser(self.temp_file.name)
        
        # Test invalid input
        amount = parser._parse_amount('invalid')
        self.assertEqual(amount, 0.0)
        
        # Test empty string
        amount = parser._parse_amount('')
        self.assertEqual(amount, 0.0)
    
    def test_full_parse(self):
        """Test full parsing workflow"""
        parser = IBKRActivityStatementParser(self.temp_file.name)
        result = parser.parse()
        
        # Check result structure
        self.assertIn('account_info', result)
        self.assertIn('nav', result)
        self.assertIn('transactions', result)
        self.assertIn('dividends', result)
        self.assertIn('taxes', result)
        self.assertIn('fees', result)
        self.assertIn('interest', result)
        self.assertIn('open_positions', result)
        self.assertIn('securities_lending', result)
        self.assertIn('forex_balances', result)
        self.assertIn('exchange_rates', result)
        
        # Check that data was extracted
        self.assertGreater(len(result['transactions']), 0)
        self.assertGreater(len(result['dividends']), 0)
        self.assertGreater(len(result['taxes']), 0)
    
    def test_convenience_function(self):
        """Test convenience function"""
        result = parse_ibkr_activity_statement(self.temp_file.name)
        
        # Check result
        self.assertIsInstance(result, dict)
        self.assertIn('account_info', result)
        self.assertIn('transactions', result)
    
    def test_to_json(self):
        """Test JSON export"""
        parser = IBKRActivityStatementParser(self.temp_file.name)
        parser.parse()
        json_str = parser.to_json()
        
        # Check JSON string
        self.assertIsInstance(json_str, str)
        self.assertIn('account_info', json_str)
        
        # Verify it's valid JSON
        import json
        data = json.loads(json_str)
        self.assertIsInstance(data, dict)
    
    def test_multi_currency_support(self):
        """Test multi-currency support"""
        parser = IBKRActivityStatementParser(self.temp_file.name)
        result = parser.parse()
        
        # Check that different currencies are handled
        currencies_in_dividends = set(d.get('currency', '') for d in result['dividends'])
        self.assertIn('USD', currencies_in_dividends)
        self.assertIn('EUR', currencies_in_dividends)
        self.assertIn('CHF', currencies_in_dividends)
    
    def test_error_handling_missing_file(self):
        """Test error handling for missing file"""
        parser = IBKRActivityStatementParser('/nonexistent/file.csv')
        
        with self.assertRaises(FileNotFoundError):
            parser._read_csv()
    
    def test_separator_rows_handling(self):
        """Test that separator rows (---) are skipped"""
        parser = IBKRActivityStatementParser(self.temp_file.name)
        result = parser.parse()
        
        # Check that no transaction has '---' in data
        for tx in result['transactions']:
            self.assertNotIn('---', str(tx.get('symbol', '')))
            self.assertNotIn('---', str(tx.get('currency', '')))


class TestDateValidation(unittest.TestCase):
    """Test date validation functionality"""
    
    def setUp(self):
        """Set up test parser"""
        self.parser = IBKRActivityStatementParser('dummy.csv')
    
    def test_valid_date_formats(self):
        """Test various valid date formats"""
        test_cases = [
            ('2025-12-03', '2025-12-03'),
            ('03.12.2025', '2025-12-03'),
            ('03/12/2025', '2025-12-03'),
            ('20251203', '2025-12-03'),
        ]
        
        for input_date, expected_date in test_cases:
            with self.subTest(input_date=input_date):
                result = self.parser._parse_date(input_date)
                self.assertEqual(result, expected_date)
    
    def test_date_with_time(self):
        """Test date extraction from datetime string"""
        result = self.parser._parse_date('2025-12-03, 14:30:00')
        self.assertEqual(result, '2025-12-03')


class TestAmountValidation(unittest.TestCase):
    """Test amount validation functionality"""
    
    def setUp(self):
        """Set up test parser"""
        self.parser = IBKRActivityStatementParser('dummy.csv')
    
    def test_various_number_formats(self):
        """Test various number formats"""
        test_cases = [
            ('1000', 1000.0),
            ('1000.50', 1000.50),
            ('1,000.50', 1000.50),
            ('1,234,567.89', 1234567.89),
            ('-1000.50', -1000.50),
            ('(1000.50)', -1000.50),
            ('1000,50', 1000.50),
            ('+500.25', 500.25),
        ]
        
        for input_amount, expected_amount in test_cases:
            with self.subTest(input_amount=input_amount):
                result = self.parser._parse_amount(input_amount)
                self.assertAlmostEqual(result, expected_amount, places=2)
    
    def test_amount_with_currency_symbols(self):
        """Test amount parsing with currency symbols"""
        test_cases = [
            ('$1,000.50', 1000.50),
            ('€500.25', 500.25),
            ('CHF 1000', 1000.0),
        ]
        
        for input_amount, expected_amount in test_cases:
            with self.subTest(input_amount=input_amount):
                result = self.parser._parse_amount(input_amount)
                self.assertAlmostEqual(result, expected_amount, places=2)


if __name__ == '__main__':
    unittest.main()
