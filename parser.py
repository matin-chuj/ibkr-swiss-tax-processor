"""
KROK A: Parser for IBKR Activity Statement CSV
Parses IBKR CSV files and extracts structured data for tax processing
"""

import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class IBKRActivityParser:
    """Parser for IBKR Activity Statement CSV files"""
    
    def __init__(self, csv_file: str):
        self.csv_file = csv_file
        self.raw_df = None
        
        # Parsed data containers
        self.trades = []
        self.dividends = []
        self.withholding_taxes = []
        self.interest = []
        self.fees = []
        self.open_positions = []
        self.cash_balances = []
        self.forex_transactions = []
        self.securities_lending = []
        
    def parse(self) -> bool:
        """Main parsing method - reads CSV and extracts all sections"""
        try:
            logger.info(f"📂 Reading CSV file: {self.csv_file}")
            # Read all lines manually since pandas can't handle varying column counts well
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Parse into list of lists
            import csv
            reader = csv.reader(lines)
            rows = list(reader)
            
            # Convert to DataFrame with maximum columns
            max_cols = max(len(row) for row in rows)
            # Pad rows to have same number of columns
            padded_rows = [row + [''] * (max_cols - len(row)) for row in rows]
            self.raw_df = pd.DataFrame(padded_rows)
            
            logger.info(f"✅ Loaded {len(self.raw_df)} rows")
            
            # Parse each section
            self._parse_trades()
            self._parse_dividends()
            self._parse_withholding_taxes()
            self._parse_interest()
            self._parse_fees()
            self._parse_open_positions()
            self._parse_cash_report()
            self._parse_forex()
            self._parse_securities_lending()
            
            logger.info(f"✅ Parsing complete:")
            logger.info(f"   Trades: {len(self.trades)}")
            logger.info(f"   Dividends: {len(self.dividends)}")
            logger.info(f"   Withholding Taxes: {len(self.withholding_taxes)}")
            logger.info(f"   Interest: {len(self.interest)}")
            logger.info(f"   Fees: {len(self.fees)}")
            logger.info(f"   Open Positions: {len(self.open_positions)}")
            logger.info(f"   Cash Balances: {len(self.cash_balances)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error parsing CSV: {e}")
            return False
    
    def _find_section(self, section_name: str) -> Optional[int]:
        """Find the starting row index of a section"""
        for idx, row in self.raw_df.iterrows():
            first_col = str(row[0]).strip() if pd.notna(row[0]) else ""
            if first_col == section_name:
                return idx
        return None
    
    def _parse_trades(self):
        """Parse Trades section"""
        section_start = self._find_section('Trades')
        if section_start is None:
            logger.warning("⚠️ Trades section not found")
            return
            
        logger.info("📊 Parsing Trades section...")
        
        # Find header row (has "Header" in second column)
        header_idx = None
        for idx in range(section_start, min(section_start + 10, len(self.raw_df))):
            if pd.notna(self.raw_df.iloc[idx, 1]) and str(self.raw_df.iloc[idx, 1]).strip() == 'Header':
                header_idx = idx
                break
        
        if header_idx is None:
            logger.warning("⚠️ Trades header not found")
            return
        
        # Parse data rows (rows with "Data" in second column)
        for idx in range(header_idx + 1, len(self.raw_df)):
            row = self.raw_df.iloc[idx]
            first_col = str(row[0]).strip() if pd.notna(row[0]) else ""
            second_col = str(row[1]).strip() if pd.notna(row[1]) else ""
            
            # Stop at next section
            if first_col in ['Dividends', 'Withholding Tax', 'Fees', 'Open Positions', 
                            'Cash Report', 'Interest', 'Securities Lending', 'Forex P/L']:
                break
            
            # Only process data rows
            if second_col != 'Data':
                continue
            
            try:
                trade = {
                    'header': self._safe_str(row[0]),
                    'data_type': self._safe_str(row[1]),
                    'discriminator': self._safe_str(row[2]),
                    'asset_category': self._safe_str(row[3]),
                    'currency': self._safe_str(row[4]),
                    'symbol': self._safe_str(row[5]),
                    'date_time': self._safe_str(row[6]),
                    'quantity': self._safe_float(row[7]),
                    'price': self._safe_float(row[8]),
                    'proceeds': self._safe_float(row[9]),
                    'commission': abs(self._safe_float(row[10])),
                    'basis': self._safe_float(row[11]) if len(row) > 11 else 0.0,
                    'realized_pl': self._safe_float(row[12]) if len(row) > 12 else 0.0,
                    'code': self._safe_str(row[13]) if len(row) > 13 else '',
                }
                
                if trade['symbol'] and trade['quantity'] != 0:
                    self.trades.append(trade)
                    
            except Exception as e:
                logger.debug(f"Skipping trade row {idx}: {e}")
        
        logger.info(f"✅ Processed {len(self.trades)} trades")
    
    def _parse_dividends(self):
        """Parse Dividends section"""
        section_start = self._find_section('Dividends')
        if section_start is None:
            logger.warning("⚠️ Dividends section not found")
            return
            
        logger.info("💰 Parsing Dividends section...")
        
        header_idx = None
        for idx in range(section_start, min(section_start + 10, len(self.raw_df))):
            if pd.notna(self.raw_df.iloc[idx, 1]) and str(self.raw_df.iloc[idx, 1]).strip() == 'Header':
                header_idx = idx
                break
        
        if header_idx is None:
            logger.warning("⚠️ Dividends header not found")
            return
        
        for idx in range(header_idx + 1, len(self.raw_df)):
            row = self.raw_df.iloc[idx]
            first_col = str(row[0]).strip() if pd.notna(row[0]) else ""
            second_col = str(row[1]).strip() if pd.notna(row[1]) else ""
            
            if first_col in ['Trades', 'Withholding Tax', 'Fees', 'Open Positions', 
                            'Cash Report', 'Interest']:
                break
            
            if second_col != 'Data':
                continue
            
            try:
                dividend = {
                    'currency': self._safe_str(row[2]),
                    'date': self._safe_str(row[3]),
                    'description': self._safe_str(row[4]),
                    'amount': self._safe_float(row[5]),
                }
                
                if dividend['amount'] != 0:
                    self.dividends.append(dividend)
                    
            except Exception as e:
                logger.debug(f"Skipping dividend row {idx}: {e}")
        
        logger.info(f"✅ Processed {len(self.dividends)} dividends")
    
    def _parse_withholding_taxes(self):
        """Parse Withholding Tax section"""
        section_start = self._find_section('Withholding Tax')
        if section_start is None:
            logger.warning("⚠️ Withholding Tax section not found")
            return
            
        logger.info("🏛️ Parsing Withholding Tax section...")
        
        header_idx = None
        for idx in range(section_start, min(section_start + 10, len(self.raw_df))):
            if pd.notna(self.raw_df.iloc[idx, 1]) and str(self.raw_df.iloc[idx, 1]).strip() == 'Header':
                header_idx = idx
                break
        
        if header_idx is None:
            logger.warning("⚠️ Withholding Tax header not found")
            return
        
        for idx in range(header_idx + 1, len(self.raw_df)):
            row = self.raw_df.iloc[idx]
            first_col = str(row[0]).strip() if pd.notna(row[0]) else ""
            second_col = str(row[1]).strip() if pd.notna(row[1]) else ""
            
            if first_col in ['Trades', 'Dividends', 'Fees', 'Open Positions', 
                            'Cash Report', 'Interest']:
                break
            
            if second_col != 'Data':
                continue
            
            try:
                tax = {
                    'currency': self._safe_str(row[2]),
                    'date': self._safe_str(row[3]),
                    'description': self._safe_str(row[4]),
                    'amount': abs(self._safe_float(row[5])),
                }
                
                if tax['amount'] != 0:
                    self.withholding_taxes.append(tax)
                    
            except Exception as e:
                logger.debug(f"Skipping tax row {idx}: {e}")
        
        logger.info(f"✅ Processed {len(self.withholding_taxes)} withholding taxes")
    
    def _parse_interest(self):
        """Parse Interest section"""
        section_start = self._find_section('Interest')
        if section_start is None:
            logger.warning("⚠️ Interest section not found")
            return
            
        logger.info("📈 Parsing Interest section...")
        
        header_idx = None
        for idx in range(section_start, min(section_start + 10, len(self.raw_df))):
            if pd.notna(self.raw_df.iloc[idx, 1]) and str(self.raw_df.iloc[idx, 1]).strip() == 'Header':
                header_idx = idx
                break
        
        if header_idx is None:
            logger.warning("⚠️ Interest header not found")
            return
        
        for idx in range(header_idx + 1, len(self.raw_df)):
            row = self.raw_df.iloc[idx]
            first_col = str(row[0]).strip() if pd.notna(row[0]) else ""
            second_col = str(row[1]).strip() if pd.notna(row[1]) else ""
            
            if first_col in ['Trades', 'Dividends', 'Withholding Tax', 'Fees', 
                            'Open Positions', 'Cash Report']:
                break
            
            if second_col != 'Data':
                continue
            
            try:
                interest = {
                    'currency': self._safe_str(row[2]),
                    'date': self._safe_str(row[3]),
                    'description': self._safe_str(row[4]),
                    'amount': self._safe_float(row[5]),
                }
                
                if interest['amount'] != 0:
                    self.interest.append(interest)
                    
            except Exception as e:
                logger.debug(f"Skipping interest row {idx}: {e}")
        
        logger.info(f"✅ Processed {len(self.interest)} interest entries")
    
    def _parse_fees(self):
        """Parse Fees section"""
        section_start = self._find_section('Fees')
        if section_start is None:
            logger.warning("⚠️ Fees section not found")
            return
            
        logger.info("💸 Parsing Fees section...")
        
        header_idx = None
        for idx in range(section_start, min(section_start + 10, len(self.raw_df))):
            if pd.notna(self.raw_df.iloc[idx, 1]) and str(self.raw_df.iloc[idx, 1]).strip() == 'Header':
                header_idx = idx
                break
        
        if header_idx is None:
            logger.warning("⚠️ Fees header not found")
            return
        
        for idx in range(header_idx + 1, len(self.raw_df)):
            row = self.raw_df.iloc[idx]
            first_col = str(row[0]).strip() if pd.notna(row[0]) else ""
            second_col = str(row[1]).strip() if pd.notna(row[1]) else ""
            
            if first_col in ['Trades', 'Dividends', 'Withholding Tax', 'Open Positions', 
                            'Cash Report', 'Interest']:
                break
            
            if second_col != 'Data':
                continue
            
            try:
                fee = {
                    'subtitle': self._safe_str(row[2]),
                    'currency': self._safe_str(row[3]),
                    'date': self._safe_str(row[4]),
                    'description': self._safe_str(row[5]),
                    'amount': abs(self._safe_float(row[6])),
                }
                
                if fee['amount'] != 0:
                    self.fees.append(fee)
                    
            except Exception as e:
                logger.debug(f"Skipping fee row {idx}: {e}")
        
        logger.info(f"✅ Processed {len(self.fees)} fees")
    
    def _parse_open_positions(self):
        """Parse Open Positions section"""
        section_start = self._find_section('Open Positions')
        if section_start is None:
            logger.warning("⚠️ Open Positions section not found")
            return
            
        logger.info("📍 Parsing Open Positions section...")
        
        header_idx = None
        for idx in range(section_start, min(section_start + 10, len(self.raw_df))):
            if pd.notna(self.raw_df.iloc[idx, 1]) and str(self.raw_df.iloc[idx, 1]).strip() == 'Header':
                header_idx = idx
                break
        
        if header_idx is None:
            logger.warning("⚠️ Open Positions header not found")
            return
        
        for idx in range(header_idx + 1, len(self.raw_df)):
            row = self.raw_df.iloc[idx]
            first_col = str(row[0]).strip() if pd.notna(row[0]) else ""
            second_col = str(row[1]).strip() if pd.notna(row[1]) else ""
            
            if first_col in ['Trades', 'Dividends', 'Withholding Tax', 'Fees', 
                            'Cash Report', 'Interest']:
                break
            
            if second_col != 'Data':
                continue
            
            try:
                position = {
                    'discriminator': self._safe_str(row[2]),
                    'asset_category': self._safe_str(row[3]),
                    'currency': self._safe_str(row[4]),
                    'symbol': self._safe_str(row[5]),
                    'quantity': self._safe_float(row[6]),
                    'mult': self._safe_float(row[7]),
                    'cost_price': self._safe_float(row[8]),
                    'cost_basis': self._safe_float(row[9]),
                    'close_price': self._safe_float(row[10]),
                    'value': self._safe_float(row[11]),
                    'unrealized_pl': self._safe_float(row[12]),
                    'code': self._safe_str(row[13]) if len(row) > 13 else '',
                }
                
                if position['symbol'] and position['quantity'] != 0:
                    self.open_positions.append(position)
                    
            except Exception as e:
                logger.debug(f"Skipping position row {idx}: {e}")
        
        logger.info(f"✅ Processed {len(self.open_positions)} open positions")
    
    def _parse_cash_report(self):
        """Parse Cash Report section"""
        section_start = self._find_section('Cash Report')
        if section_start is None:
            logger.warning("⚠️ Cash Report section not found")
            return
            
        logger.info("💵 Parsing Cash Report section...")
        
        # Look for "Ending Cash" rows
        for idx in range(section_start, min(section_start + 50, len(self.raw_df))):
            row = self.raw_df.iloc[idx]
            first_col = str(row[0]).strip() if pd.notna(row[0]) else ""
            second_col = str(row[1]).strip() if pd.notna(row[1]) else ""
            third_col = str(row[2]).strip() if pd.notna(row[2]) else ""
            
            if first_col in ['Trades', 'Dividends', 'Withholding Tax', 'Fees', 
                            'Open Positions', 'Interest']:
                break
            
            # Look for "Ending Cash" with Data type
            if second_col == 'Data' and third_col == 'Ending Cash':
                try:
                    currency = self._safe_str(row[3])
                    amount = self._safe_float(row[4])
                    
                    if currency and currency != 'Total' and amount != 0:
                        self.cash_balances.append({
                            'currency': currency,
                            'amount': amount,
                        })
                except Exception as e:
                    logger.debug(f"Skipping cash row {idx}: {e}")
        
        logger.info(f"✅ Processed {len(self.cash_balances)} cash balances")
    
    def _parse_forex(self):
        """Parse Forex P/L section"""
        section_start = self._find_section('Forex P/L')
        if section_start is None:
            logger.debug("ℹ️ Forex P/L section not found")
            return
            
        logger.info("💱 Parsing Forex P/L section...")
        
        header_idx = None
        for idx in range(section_start, min(section_start + 10, len(self.raw_df))):
            if pd.notna(self.raw_df.iloc[idx, 1]) and str(self.raw_df.iloc[idx, 1]).strip() == 'Header':
                header_idx = idx
                break
        
        if header_idx is None:
            logger.warning("⚠️ Forex P/L header not found")
            return
        
        for idx in range(header_idx + 1, len(self.raw_df)):
            row = self.raw_df.iloc[idx]
            first_col = str(row[0]).strip() if pd.notna(row[0]) else ""
            second_col = str(row[1]).strip() if pd.notna(row[1]) else ""
            
            if first_col in ['Trades', 'Dividends', 'Withholding Tax', 'Fees', 
                            'Open Positions', 'Cash Report', 'Interest']:
                break
            
            if second_col != 'Data':
                continue
            
            try:
                forex = {
                    'discriminator': self._safe_str(row[2]),
                    'asset_category': self._safe_str(row[3]),
                    'currency': self._safe_str(row[4]),
                    'symbol': self._safe_str(row[5]),
                    'date_time': self._safe_str(row[6]),
                    'quantity': self._safe_float(row[7]),
                    'proceeds': self._safe_float(row[8]),
                    'cost_basis': self._safe_float(row[9]),
                    'realized_pl': self._safe_float(row[10]),
                    'code': self._safe_str(row[11]) if len(row) > 11 else '',
                }
                
                if forex['symbol']:
                    self.forex_transactions.append(forex)
                    
            except Exception as e:
                logger.debug(f"Skipping forex row {idx}: {e}")
        
        logger.info(f"✅ Processed {len(self.forex_transactions)} forex transactions")
    
    def _parse_securities_lending(self):
        """Parse Securities Lending section"""
        section_start = self._find_section('Securities Lending')
        if section_start is None:
            logger.debug("ℹ️ Securities Lending section not found")
            return
            
        logger.info("🔄 Parsing Securities Lending section...")
        
        header_idx = None
        for idx in range(section_start, min(section_start + 10, len(self.raw_df))):
            if pd.notna(self.raw_df.iloc[idx, 1]) and str(self.raw_df.iloc[idx, 1]).strip() == 'Header':
                header_idx = idx
                break
        
        if header_idx is None:
            logger.warning("⚠️ Securities Lending header not found")
            return
        
        for idx in range(header_idx + 1, len(self.raw_df)):
            row = self.raw_df.iloc[idx]
            first_col = str(row[0]).strip() if pd.notna(row[0]) else ""
            second_col = str(row[1]).strip() if pd.notna(row[1]) else ""
            
            if first_col in ['Trades', 'Dividends', 'Withholding Tax', 'Fees', 
                            'Open Positions', 'Cash Report', 'Interest']:
                break
            
            if second_col != 'Data':
                continue
            
            try:
                lending = {
                    'currency': self._safe_str(row[2]),
                    'date': self._safe_str(row[3]),
                    'description': self._safe_str(row[4]),
                    'amount': self._safe_float(row[5]),
                }
                
                if lending['amount'] != 0:
                    self.securities_lending.append(lending)
                    
            except Exception as e:
                logger.debug(f"Skipping lending row {idx}: {e}")
        
        logger.info(f"✅ Processed {len(self.securities_lending)} securities lending entries")
    
    def _safe_float(self, value) -> float:
        """Safely convert to float"""
        if pd.isna(value) or value == '':
            return 0.0
        try:
            return float(str(value).replace(',', '').replace(' ', '').strip())
        except (ValueError, AttributeError):
            return 0.0
    
    def _safe_str(self, value) -> str:
        """Safely convert to string"""
        if pd.isna(value) or value == '':
            return ''
        return str(value).strip()
    
    def get_summary(self) -> Dict:
        """Get summary statistics"""
        return {
            'trades_count': len(self.trades),
            'dividends_count': len(self.dividends),
            'withholding_taxes_count': len(self.withholding_taxes),
            'interest_count': len(self.interest),
            'fees_count': len(self.fees),
            'open_positions_count': len(self.open_positions),
            'cash_balances_count': len(self.cash_balances),
            'forex_transactions_count': len(self.forex_transactions),
            'securities_lending_count': len(self.securities_lending),
        }
