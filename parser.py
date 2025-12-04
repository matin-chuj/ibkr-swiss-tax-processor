"""
IBKR Activity Statement CSV Parser
Parses Interactive Brokers Activity Statement CSV files and extracts structured data
"""

import csv
import re
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal, InvalidOperation

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class IBKRActivityStatementParser:
    """
    Parser for Interactive Brokers Activity Statement CSV files.
    
    Extracts and validates:
    - Account information (base currency, dates, account type)
    - Net Asset Value (NAV) - beginning and ending
    - Transactions (stocks, forex, forex conversions)
    - Dividends (multi-currency: USD, EUR, NOK, PLN, CHF, etc.)
    - Withholding taxes (by country)
    - Interest (multi-currency)
    - Fees and commissions
    - Open positions (stock positions)
    - Securities lending details
    - Exchange rates
    """
    
    # Supported currencies
    SUPPORTED_CURRENCIES = ['CHF', 'USD', 'EUR', 'NOK', 'PLN', 'SEK', 'JPY', 'GBP', 'CAD', 'AUD']
    
    # Section markers in IBKR CSV
    SECTION_MARKERS = [
        'Statement',
        'Account Information',
        'Net Asset Value',
        'Cash Report',
        'Trades',
        'Stocks',
        'Forex',
        'Dividends',
        'Withholding Tax',
        'Interest',
        'Fees',
        'Commission Details',
        'Open Positions',
        'Securities Lending',
        'Change in NAV',
        'Mark-to-Market Performance Summary',
        'Realized & Unrealized Performance Summary',
        'Cash Report'
    ]
    
    def __init__(self, csv_file_path: str):
        """
        Initialize parser with CSV file path.
        
        Args:
            csv_file_path: Path to IBKR Activity Statement CSV file
        """
        self.csv_file_path = csv_file_path
        self.raw_data = []
        self.sections = {}
        
        # Data containers
        self.account_info = {}
        self.nav = {}
        self.transactions = []
        self.dividends = []
        self.taxes = []
        self.fees = []
        self.interest = []
        self.open_positions = []
        self.securities_lending = []
        self.forex_balances = []
        self.exchange_rates = {}
        
    def parse(self) -> Dict[str, Any]:
        """
        Main parsing method - reads CSV and extracts all data.
        
        Returns:
            Dictionary with all extracted data in JSON-compatible format
        """
        logger.info(f"Starting to parse IBKR Activity Statement: {self.csv_file_path}")
        
        # Step 1: Read CSV file
        self._read_csv()
        
        # Step 2: Identify sections
        self._identify_sections()
        
        # Step 3: Extract data from each section
        self._extract_account_info()
        self._extract_nav()
        self._extract_transactions()
        self._extract_dividends()
        self._extract_taxes()
        self._extract_fees()
        self._extract_interest()
        self._extract_open_positions()
        self._extract_securities_lending()
        self._extract_forex_balances()
        self._extract_exchange_rates()
        
        # Step 4: Build result
        result = self._build_result()
        
        logger.info("Parsing completed successfully")
        return result
    
    def _read_csv(self):
        """Read CSV file and store raw data."""
        try:
            with open(self.csv_file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                self.raw_data = list(reader)
            logger.info(f"Read {len(self.raw_data)} rows from CSV")
        except FileNotFoundError:
            logger.error(f"File not found: {self.csv_file_path}")
            raise
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise
    
    def _identify_sections(self):
        """
        Identify and map sections in the CSV file.
        IBKR CSV structure: Statement, Header/Data, Field Name, Field Value, ...
        """
        current_section = None
        
        for idx, row in enumerate(self.raw_data):
            if not row or len(row) == 0:
                continue
            
            first_col = row[0].strip() if row[0] else ''
            
            # Check if this is a section marker
            if first_col in self.SECTION_MARKERS:
                current_section = first_col
                if current_section not in self.sections:
                    self.sections[current_section] = {
                        'start_idx': idx,
                        'rows': []
                    }
                logger.debug(f"Found section: {current_section} at row {idx}")
            
            # Add row to current section
            if current_section:
                self.sections[current_section]['rows'].append({'idx': idx, 'data': row})
        
        logger.info(f"Identified {len(self.sections)} sections")
    
    def _extract_account_info(self):
        """Extract account information (base currency, dates, account type)."""
        if 'Account Information' not in self.sections and 'Statement' not in self.sections:
            logger.warning("No Account Information or Statement section found")
            return
        
        # Try both section names
        section_name = 'Account Information' if 'Account Information' in self.sections else 'Statement'
        rows = self.sections[section_name]['rows']
        
        for row_info in rows:
            row = row_info['data']
            if len(row) < 2:
                continue
            
            # IBKR format: Statement, Data, FieldName, FieldValue
            if len(row) >= 4 and row[1] == 'Data':
                field_name = row[2].strip() if row[2] else ''
                field_value = row[3].strip() if row[3] else ''
                
                # Extract key fields
                if 'Account Type' in field_name:
                    self.account_info['account_type'] = field_value
                elif 'Account' in field_name and 'Type' not in field_name:
                    self.account_info['account_id'] = field_value
                elif 'Base' in field_name and 'Currency' in field_name:
                    self.account_info['base_currency'] = field_value
                elif 'Period' in field_name:
                    self.account_info['period'] = field_value
                    # Try to extract dates
                    dates = self._extract_dates_from_period(field_value)
                    if dates:
                        self.account_info['start_date'] = dates[0]
                        self.account_info['end_date'] = dates[1]
                elif 'Broker' in field_name or 'Name' in field_name:
                    self.account_info['broker_name'] = field_value
        
        logger.info(f"Extracted account info: {self.account_info}")
    
    def _extract_nav(self):
        """Extract Net Asset Value (beginning and ending)."""
        if 'Net Asset Value' not in self.sections:
            logger.warning("No Net Asset Value section found")
            return
        
        rows = self.sections['Net Asset Value']['rows']
        
        for row_info in rows:
            row = row_info['data']
            if len(row) < 3:
                continue
            
            # IBKR format: Net Asset Value, Header/Data, ...
            if row[1] == 'Data':
                if len(row) >= 4:
                    # Extract NAV data
                    nav_type = row[2].strip() if row[2] else ''
                    nav_value = self._parse_amount(row[3]) if len(row) > 3 else 0.0
                    
                    if 'Start' in nav_type or 'Beginning' in nav_type:
                        currency = row[2].strip() if len(row) > 2 else 'CHF'
                        self.nav['beginning'] = {
                            'amount': nav_value,
                            'currency': currency
                        }
                    elif 'End' in nav_type or 'Ending' in nav_type:
                        currency = row[2].strip() if len(row) > 2 else 'CHF'
                        self.nav['ending'] = {
                            'amount': nav_value,
                            'currency': currency
                        }
        
        logger.info(f"Extracted NAV: {self.nav}")
    
    def _extract_transactions(self):
        """Extract all transactions (stocks, forex, forex conversions)."""
        # Check multiple possible section names
        transaction_sections = ['Trades', 'Stocks', 'Forex']
        
        for section_name in transaction_sections:
            if section_name in self.sections:
                self._parse_transaction_section(section_name)
    
    def _parse_transaction_section(self, section_name: str):
        """Parse a specific transaction section."""
        rows = self.sections[section_name]['rows']
        
        # Find header row
        header_idx = None
        headers = []
        
        for i, row_info in enumerate(rows):
            row = row_info['data']
            if len(row) > 1 and row[1] == 'Header':
                header_idx = i
                headers = [col.strip() for col in row[2:] if col]
                logger.debug(f"{section_name} headers: {headers}")
                break
        
        if header_idx is None:
            logger.warning(f"No header found in {section_name} section")
            return
        
        # Parse data rows
        for row_info in rows[header_idx + 1:]:
            row = row_info['data']
            
            # Skip non-data rows
            if len(row) < 2 or row[1] != 'Data':
                continue
            
            # Skip separator rows (---)
            if any('---' in str(cell) for cell in row):
                continue
            
            try:
                transaction = self._parse_transaction_row(row, headers, section_name)
                if transaction:
                    self.transactions.append(transaction)
            except Exception as e:
                logger.debug(f"Failed to parse transaction row: {e}")
        
        logger.info(f"Extracted {len([t for t in self.transactions if t.get('type') == section_name])} transactions from {section_name}")
    
    def _parse_transaction_row(self, row: List[str], headers: List[str], section_type: str) -> Optional[Dict]:
        """Parse a single transaction row."""
        # Skip if row doesn't have enough data
        if len(row) < 3:
            return None
        
        transaction = {
            'type': section_type
        }
        
        # Map row data to headers (starting from column 2)
        data_start = 2
        for i, header in enumerate(headers):
            col_idx = data_start + i
            if col_idx < len(row):
                value = row[col_idx].strip()
                
                # Parse based on header name
                if 'Currency' in header:
                    transaction['currency'] = value
                elif 'Symbol' in header:
                    transaction['symbol'] = value
                elif 'Date' in header or 'Time' in header:
                    parsed_date = self._parse_date(value)
                    if parsed_date:
                        transaction['date'] = parsed_date
                elif 'Quantity' in header:
                    transaction['quantity'] = self._parse_amount(value)
                elif 'Price' in header or 'T. Price' in header:
                    transaction['price'] = self._parse_amount(value)
                elif 'Proceeds' in header or 'Amount' in header:
                    transaction['proceeds'] = self._parse_amount(value)
                elif 'Comm' in header or 'Commission' in header:
                    transaction['commission'] = self._parse_amount(value)
                elif 'Basis' in header:
                    transaction['basis'] = self._parse_amount(value)
                elif 'Realized P/L' in header or 'Realized PL' in header:
                    transaction['realized_pl'] = self._parse_amount(value)
                elif 'Code' in header:
                    transaction['code'] = value
        
        # Validate required fields
        if 'date' not in transaction or not transaction.get('symbol'):
            return None
        
        return transaction
    
    def _extract_dividends(self):
        """Extract dividends (multi-currency)."""
        if 'Dividends' not in self.sections:
            logger.warning("No Dividends section found")
            return
        
        rows = self.sections['Dividends']['rows']
        
        # Find header row
        header_idx = None
        headers = []
        
        for i, row_info in enumerate(rows):
            row = row_info['data']
            if len(row) > 1 and row[1] == 'Header':
                header_idx = i
                headers = [col.strip() for col in row[2:] if col]
                logger.debug(f"Dividend headers: {headers}")
                break
        
        if header_idx is None:
            logger.warning("No header found in Dividends section")
            return
        
        # Parse data rows
        for row_info in rows[header_idx + 1:]:
            row = row_info['data']
            
            if len(row) < 2 or row[1] != 'Data':
                continue
            
            # Skip separator rows
            if any('---' in str(cell) for cell in row):
                continue
            
            try:
                dividend = self._parse_dividend_row(row, headers)
                if dividend:
                    self.dividends.append(dividend)
            except Exception as e:
                logger.debug(f"Failed to parse dividend row: {e}")
        
        logger.info(f"Extracted {len(self.dividends)} dividends")
    
    def _parse_dividend_row(self, row: List[str], headers: List[str]) -> Optional[Dict]:
        """Parse a single dividend row."""
        if len(row) < 3:
            return None
        
        dividend = {}
        
        # Map row data to headers
        data_start = 2
        for i, header in enumerate(headers):
            col_idx = data_start + i
            if col_idx < len(row):
                value = row[col_idx].strip()
                
                if 'Currency' in header:
                    dividend['currency'] = value
                elif 'Symbol' in header or 'Description' in header:
                    dividend['symbol'] = value
                elif 'Date' in header:
                    parsed_date = self._parse_date(value)
                    if parsed_date:
                        dividend['date'] = parsed_date
                elif 'Amount' in header:
                    dividend['amount'] = self._parse_amount(value)
        
        # Validate required fields
        if 'date' not in dividend or 'amount' not in dividend:
            return None
        
        return dividend
    
    def _extract_taxes(self):
        """Extract withholding taxes (by country)."""
        if 'Withholding Tax' not in self.sections:
            logger.warning("No Withholding Tax section found")
            return
        
        rows = self.sections['Withholding Tax']['rows']
        
        # Find header row
        header_idx = None
        headers = []
        
        for i, row_info in enumerate(rows):
            row = row_info['data']
            if len(row) > 1 and row[1] == 'Header':
                header_idx = i
                headers = [col.strip() for col in row[2:] if col]
                logger.debug(f"Tax headers: {headers}")
                break
        
        if header_idx is None:
            logger.warning("No header found in Withholding Tax section")
            return
        
        # Parse data rows
        for row_info in rows[header_idx + 1:]:
            row = row_info['data']
            
            if len(row) < 2 or row[1] != 'Data':
                continue
            
            if any('---' in str(cell) for cell in row):
                continue
            
            try:
                tax = self._parse_tax_row(row, headers)
                if tax:
                    self.taxes.append(tax)
            except Exception as e:
                logger.debug(f"Failed to parse tax row: {e}")
        
        logger.info(f"Extracted {len(self.taxes)} tax entries")
    
    def _parse_tax_row(self, row: List[str], headers: List[str]) -> Optional[Dict]:
        """Parse a single tax row."""
        if len(row) < 3:
            return None
        
        tax = {}
        
        # Map row data to headers
        data_start = 2
        for i, header in enumerate(headers):
            col_idx = data_start + i
            if col_idx < len(row):
                value = row[col_idx].strip()
                
                if 'Currency' in header:
                    tax['currency'] = value
                elif 'Symbol' in header or 'Description' in header:
                    tax['symbol'] = value
                elif 'Date' in header:
                    parsed_date = self._parse_date(value)
                    if parsed_date:
                        tax['date'] = parsed_date
                elif 'Amount' in header:
                    tax['amount'] = abs(self._parse_amount(value))
                elif 'Country' in header:
                    tax['country'] = value
        
        # Validate required fields
        if 'date' not in tax or 'amount' not in tax:
            return None
        
        return tax
    
    def _extract_fees(self):
        """Extract fees and commissions."""
        fee_sections = ['Fees', 'Commission Details']
        
        for section_name in fee_sections:
            if section_name in self.sections:
                self._parse_fee_section(section_name)
    
    def _parse_fee_section(self, section_name: str):
        """Parse a fee section."""
        rows = self.sections[section_name]['rows']
        
        # Find header row
        header_idx = None
        headers = []
        
        for i, row_info in enumerate(rows):
            row = row_info['data']
            if len(row) > 1 and row[1] == 'Header':
                header_idx = i
                headers = [col.strip() for col in row[2:] if col]
                logger.debug(f"{section_name} headers: {headers}")
                break
        
        if header_idx is None:
            logger.warning(f"No header found in {section_name} section")
            return
        
        # Parse data rows
        for row_info in rows[header_idx + 1:]:
            row = row_info['data']
            
            if len(row) < 2 or row[1] != 'Data':
                continue
            
            if any('---' in str(cell) for cell in row):
                continue
            
            try:
                fee = self._parse_fee_row(row, headers)
                if fee:
                    self.fees.append(fee)
            except Exception as e:
                logger.debug(f"Failed to parse fee row: {e}")
        
        logger.info(f"Extracted {len(self.fees)} fees from {section_name}")
    
    def _parse_fee_row(self, row: List[str], headers: List[str]) -> Optional[Dict]:
        """Parse a single fee row."""
        if len(row) < 3:
            return None
        
        fee = {}
        
        # Map row data to headers
        data_start = 2
        for i, header in enumerate(headers):
            col_idx = data_start + i
            if col_idx < len(row):
                value = row[col_idx].strip()
                
                if 'Currency' in header:
                    fee['currency'] = value
                elif 'Description' in header or 'Subtitle' in header:
                    fee['description'] = value
                elif 'Date' in header:
                    parsed_date = self._parse_date(value)
                    if parsed_date:
                        fee['date'] = parsed_date
                elif 'Amount' in header:
                    fee['amount'] = abs(self._parse_amount(value))
        
        # Validate required fields
        if 'amount' not in fee:
            return None
        
        return fee
    
    def _extract_interest(self):
        """Extract interest (multi-currency)."""
        if 'Interest' not in self.sections:
            logger.warning("No Interest section found")
            return
        
        rows = self.sections['Interest']['rows']
        
        # Find header row
        header_idx = None
        headers = []
        
        for i, row_info in enumerate(rows):
            row = row_info['data']
            if len(row) > 1 and row[1] == 'Header':
                header_idx = i
                headers = [col.strip() for col in row[2:] if col]
                logger.debug(f"Interest headers: {headers}")
                break
        
        if header_idx is None:
            logger.warning("No header found in Interest section")
            return
        
        # Parse data rows
        for row_info in rows[header_idx + 1:]:
            row = row_info['data']
            
            if len(row) < 2 or row[1] != 'Data':
                continue
            
            if any('---' in str(cell) for cell in row):
                continue
            
            try:
                interest = self._parse_interest_row(row, headers)
                if interest:
                    self.interest.append(interest)
            except Exception as e:
                logger.debug(f"Failed to parse interest row: {e}")
        
        logger.info(f"Extracted {len(self.interest)} interest entries")
    
    def _parse_interest_row(self, row: List[str], headers: List[str]) -> Optional[Dict]:
        """Parse a single interest row."""
        if len(row) < 3:
            return None
        
        interest = {}
        
        # Map row data to headers
        data_start = 2
        for i, header in enumerate(headers):
            col_idx = data_start + i
            if col_idx < len(row):
                value = row[col_idx].strip()
                
                if 'Currency' in header:
                    interest['currency'] = value
                elif 'Date' in header:
                    parsed_date = self._parse_date(value)
                    if parsed_date:
                        interest['date'] = parsed_date
                elif 'Amount' in header:
                    interest['amount'] = self._parse_amount(value)
                elif 'Description' in header:
                    interest['description'] = value
        
        # Validate required fields
        if 'amount' not in interest:
            return None
        
        return interest
    
    def _extract_open_positions(self):
        """Extract open positions (stock positions)."""
        if 'Open Positions' not in self.sections:
            logger.warning("No Open Positions section found")
            return
        
        rows = self.sections['Open Positions']['rows']
        
        # Find header row
        header_idx = None
        headers = []
        
        for i, row_info in enumerate(rows):
            row = row_info['data']
            if len(row) > 1 and row[1] == 'Header':
                header_idx = i
                headers = [col.strip() for col in row[2:] if col]
                logger.debug(f"Open Positions headers: {headers}")
                break
        
        if header_idx is None:
            logger.warning("No header found in Open Positions section")
            return
        
        # Parse data rows
        for row_info in rows[header_idx + 1:]:
            row = row_info['data']
            
            if len(row) < 2 or row[1] != 'Data':
                continue
            
            if any('---' in str(cell) for cell in row):
                continue
            
            try:
                position = self._parse_position_row(row, headers)
                if position:
                    self.open_positions.append(position)
            except Exception as e:
                logger.debug(f"Failed to parse position row: {e}")
        
        logger.info(f"Extracted {len(self.open_positions)} open positions")
    
    def _parse_position_row(self, row: List[str], headers: List[str]) -> Optional[Dict]:
        """Parse a single open position row."""
        if len(row) < 3:
            return None
        
        position = {}
        
        # Map row data to headers
        data_start = 2
        for i, header in enumerate(headers):
            col_idx = data_start + i
            if col_idx < len(row):
                value = row[col_idx].strip()
                
                if 'Currency' in header:
                    position['currency'] = value
                elif 'Symbol' in header:
                    position['symbol'] = value
                elif 'Quantity' in header:
                    position['quantity'] = self._parse_amount(value)
                elif 'Price' in header or 'Close Price' in header:
                    position['price'] = self._parse_amount(value)
                elif 'Value' in header or 'Mkt Value' in header:
                    position['value'] = self._parse_amount(value)
                elif 'Unrealized' in header or 'P/L' in header:
                    position['unrealized_pl'] = self._parse_amount(value)
        
        # Validate required fields
        if 'symbol' not in position:
            return None
        
        return position
    
    def _extract_securities_lending(self):
        """Extract securities lending details."""
        if 'Securities Lending' not in self.sections:
            logger.debug("No Securities Lending section found")
            return
        
        rows = self.sections['Securities Lending']['rows']
        
        # Find header row
        header_idx = None
        headers = []
        
        for i, row_info in enumerate(rows):
            row = row_info['data']
            if len(row) > 1 and row[1] == 'Header':
                header_idx = i
                headers = [col.strip() for col in row[2:] if col]
                logger.debug(f"Securities Lending headers: {headers}")
                break
        
        if header_idx is None:
            logger.debug("No header found in Securities Lending section")
            return
        
        # Parse data rows
        for row_info in rows[header_idx + 1:]:
            row = row_info['data']
            
            if len(row) < 2 or row[1] != 'Data':
                continue
            
            if any('---' in str(cell) for cell in row):
                continue
            
            try:
                lending = self._parse_securities_lending_row(row, headers)
                if lending:
                    self.securities_lending.append(lending)
            except Exception as e:
                logger.debug(f"Failed to parse securities lending row: {e}")
        
        logger.info(f"Extracted {len(self.securities_lending)} securities lending entries")
    
    def _parse_securities_lending_row(self, row: List[str], headers: List[str]) -> Optional[Dict]:
        """Parse a single securities lending row."""
        if len(row) < 3:
            return None
        
        lending = {}
        
        # Map row data to headers
        data_start = 2
        for i, header in enumerate(headers):
            col_idx = data_start + i
            if col_idx < len(row):
                value = row[col_idx].strip()
                
                if 'Currency' in header:
                    lending['currency'] = value
                elif 'Symbol' in header:
                    lending['symbol'] = value
                elif 'Date' in header:
                    parsed_date = self._parse_date(value)
                    if parsed_date:
                        lending['date'] = parsed_date
                elif 'Quantity' in header:
                    lending['quantity'] = self._parse_amount(value)
                elif 'Fee' in header or 'Amount' in header:
                    lending['amount'] = self._parse_amount(value)
        
        return lending if lending else None
    
    def _extract_forex_balances(self):
        """Extract forex balances from Cash Report."""
        if 'Cash Report' not in self.sections:
            logger.debug("No Cash Report section found")
            return
        
        rows = self.sections['Cash Report']['rows']
        
        # Find header row
        header_idx = None
        headers = []
        
        for i, row_info in enumerate(rows):
            row = row_info['data']
            if len(row) > 1 and row[1] == 'Header':
                header_idx = i
                headers = [col.strip() for col in row[2:] if col]
                logger.debug(f"Cash Report headers: {headers}")
                break
        
        if header_idx is None:
            logger.debug("No header found in Cash Report section")
            return
        
        # Parse data rows
        for row_info in rows[header_idx + 1:]:
            row = row_info['data']
            
            if len(row) < 2 or row[1] != 'Data':
                continue
            
            if any('---' in str(cell) for cell in row):
                continue
            
            try:
                balance = self._parse_cash_balance_row(row, headers)
                if balance:
                    self.forex_balances.append(balance)
            except Exception as e:
                logger.debug(f"Failed to parse cash balance row: {e}")
        
        logger.info(f"Extracted {len(self.forex_balances)} forex balances")
    
    def _parse_cash_balance_row(self, row: List[str], headers: List[str]) -> Optional[Dict]:
        """Parse a single cash balance row."""
        if len(row) < 3:
            return None
        
        balance = {}
        
        # Map row data to headers
        data_start = 2
        for i, header in enumerate(headers):
            col_idx = data_start + i
            if col_idx < len(row):
                value = row[col_idx].strip()
                
                if 'Currency' in header:
                    balance['currency'] = value
                elif 'Ending Cash' in header or 'Total' in header:
                    balance['amount'] = self._parse_amount(value)
                elif 'Starting Cash' in header:
                    balance['starting_amount'] = self._parse_amount(value)
        
        # Validate required fields
        if 'currency' not in balance or 'amount' not in balance:
            return None
        
        return balance
    
    def _extract_exchange_rates(self):
        """Extract exchange rates if available in the statement."""
        # Exchange rates might be in various sections
        # For now, we'll create a default set
        for currency in self.SUPPORTED_CURRENCIES:
            if currency != 'CHF':
                # These will be populated from actual data if available
                self.exchange_rates[f"{currency}/CHF"] = None
        
        logger.debug(f"Exchange rates structure initialized: {self.exchange_rates}")
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """
        Parse and validate date string.
        Supports formats: DD.MM.YYYY, YYYY-MM-DD, DD/MM/YYYY
        
        Args:
            date_str: Date string to parse
            
        Returns:
            ISO format date string (YYYY-MM-DD) or None if invalid
        """
        if not date_str or date_str.strip() == '':
            return None
        
        date_str = date_str.strip()
        
        # List of formats to try
        formats = [
            '%Y-%m-%d',      # YYYY-MM-DD
            '%d.%m.%Y',      # DD.MM.YYYY
            '%d/%m/%Y',      # DD/MM/YYYY
            '%Y%m%d',        # YYYYMMDD
            '%m/%d/%Y',      # MM/DD/YYYY (US format)
        ]
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # Try to extract date with regex for formats like "2025-12-03, 14:30:00"
        date_match = re.match(r'(\d{4}-\d{2}-\d{2})', date_str)
        if date_match:
            return date_match.group(1)
        
        logger.debug(f"Could not parse date: {date_str}")
        return None
    
    def _parse_amount(self, amount_str: str) -> float:
        """
        Parse and validate amount string.
        Handles formats: 1,000.00, 1000.00, -1,000.00, (1,000.00)
        
        Args:
            amount_str: Amount string to parse
            
        Returns:
            Float value or 0.0 if invalid
        """
        if not amount_str or amount_str.strip() == '':
            return 0.0
        
        amount_str = amount_str.strip()
        
        # Handle parentheses (accounting notation for negative)
        is_negative = False
        if amount_str.startswith('(') and amount_str.endswith(')'):
            is_negative = True
            amount_str = amount_str[1:-1]
        
        # Remove currency symbols and spaces
        amount_str = re.sub(r'[^\d,.\-+]', '', amount_str)
        
        # Handle different number formats
        # European: 1.000,00 vs American: 1,000.00
        if ',' in amount_str and '.' in amount_str:
            # Determine which is thousands separator
            comma_pos = amount_str.rfind(',')
            dot_pos = amount_str.rfind('.')
            
            if dot_pos > comma_pos:
                # American format: 1,000.00
                amount_str = amount_str.replace(',', '')
            else:
                # European format: 1.000,00
                amount_str = amount_str.replace('.', '').replace(',', '.')
        elif ',' in amount_str:
            # Only comma - check if it's decimal separator
            parts = amount_str.split(',')
            if len(parts) == 2 and len(parts[1]) == 2:
                # Likely decimal: 1000,00
                amount_str = amount_str.replace(',', '.')
            else:
                # Likely thousands: 1,000
                amount_str = amount_str.replace(',', '')
        
        try:
            value = float(amount_str)
            return -value if is_negative else value
        except ValueError:
            logger.debug(f"Could not parse amount: {amount_str}")
            return 0.0
    
    def _extract_dates_from_period(self, period_str: str) -> Optional[Tuple[str, str]]:
        """
        Extract start and end dates from period string.
        
        Args:
            period_str: Period string like "January 1, 2025 - December 3, 2025"
            
        Returns:
            Tuple of (start_date, end_date) in ISO format or None
        """
        # Try to find two dates in the string
        date_pattern = r'\d{4}-\d{2}-\d{2}'
        dates = re.findall(date_pattern, period_str)
        
        if len(dates) >= 2:
            return (dates[0], dates[1])
        
        # Try other formats
        date_pattern2 = r'\d{2}\.\d{2}\.\d{4}'
        dates = re.findall(date_pattern2, period_str)
        
        if len(dates) >= 2:
            parsed_dates = [self._parse_date(d) for d in dates[:2]]
            if all(parsed_dates):
                return tuple(parsed_dates)
        
        return None
    
    def _build_result(self) -> Dict[str, Any]:
        """
        Build final result dictionary with all extracted data.
        
        Returns:
            JSON-compatible dictionary with all parsed data
        """
        return {
            'account_info': self.account_info,
            'nav': self.nav,
            'transactions': self.transactions,
            'dividends': self.dividends,
            'taxes': self.taxes,
            'fees': self.fees,
            'interest': self.interest,
            'open_positions': self.open_positions,
            'securities_lending': self.securities_lending,
            'forex_balances': self.forex_balances,
            'exchange_rates': self.exchange_rates
        }
    
    def to_json(self) -> str:
        """
        Convert parsed data to JSON string.
        
        Returns:
            JSON string representation of parsed data
        """
        import json
        result = self._build_result()
        return json.dumps(result, indent=2, ensure_ascii=False)


def parse_ibkr_activity_statement(csv_file_path: str) -> Dict[str, Any]:
    """
    Convenience function to parse IBKR Activity Statement.
    
    Args:
        csv_file_path: Path to IBKR Activity Statement CSV file
        
    Returns:
        Dictionary with all parsed data
    """
    parser = IBKRActivityStatementParser(csv_file_path)
    return parser.parse()
