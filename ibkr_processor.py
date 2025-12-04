"""
IBKR Activity Statement Tax Processor for Basel-Landschaft Canton
Processes IBKR CSV statements and generates Swiss tax reports
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, List, Tuple, Optional
import logging
from io import StringIO

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging. getLogger(__name__)


class IBKRTaxProcessor:
    """Main processor for IBKR statements with improved CSV parsing"""

    def __init__(self, csv_file: str, tax_year: int = 2025):
        self.csv_file = csv_file
        self.tax_year = tax_year
        self.canton = "Basel-Landschaft"

        # Exchange rates (fallback - can be updated with APIs)
        self.fx_rates = {
            'EUR': 0.93324,  # EUR/CHF from your statement
            'USD': 0.79959,  # USD/CHF
            'JPY': 0.0051507,  # JPY/CHF
            'NOK': 0.07952,  # NOK/CHF
            'PLN': 0.22084,  # PLN/CHF
            'SEK': 0.085358,  # SEK/CHF
            'CHF': 1.0
        }

        # Data containers
        self.transactions = []
        self.dividends = []
        self.forex = []
        self.fees = []
        self.taxes = []
        self.open_positions = []

        # Summary data
        self.summary = {}

    def read_csv(self) -> pd. DataFrame:
        """Read and parse IBKR CSV"""
        df = pd.read_csv(self.csv_file, header=None)
        return df

    def parse_ibkr_statement(self):
        """Parse IBKR statement into organized sections"""
        df = self.read_csv()
        logger.info(f"📂 Read CSV with {len(df)} rows")

        # Find section markers
        sections = {}
        current_section = None
        section_start = None

        for idx, row in df.iterrows():
            first_col = str(row[0]). strip() if pd.notna(row[0]) else ""

            # Detect section headers
            if first_col in ['Trades', 'Dividends', 'Withholding Tax', 'Fees',
                            'Open Positions', 'Cash Report', 'Interest', 'Securities Lending']:
                current_section = first_col
                section_start = idx
                sections[current_section] = {'start': idx, 'data': []}
                logger.debug(f"Found section: {current_section} at row {idx}")

            elif current_section and section_start is not None:
                # Check if we hit next section
                if first_col in ['Trades', 'Dividends', 'Withholding Tax', 'Fees',
                                'Open Positions', 'Cash Report', 'Interest', 'Securities Lending']:
                    current_section = first_col
                    section_start = idx
                    sections[current_section] = {'start': idx, 'data': []}
                else:
                    sections[current_section]['data'].append(row)

        # Process each section
        logger.info("🔄 Processing sections...")
        if 'Trades' in sections:
            self._process_trades_section(sections['Trades']['data'], df)
        if 'Dividends' in sections:
            self._process_dividends_section(sections['Dividends']['data'], df)
        if 'Withholding Tax' in sections:
            self._process_withholding_tax_section(sections['Withholding Tax']['data'], df)
        if 'Fees' in sections:
            self._process_fees_section(sections['Fees']['data'], df)
        if 'Open Positions' in sections:
            self._process_open_positions_section(sections['Open Positions']['data'], df)
        if 'Interest' in sections:
            self._process_interest_section(sections['Interest']['data'], df)

    def _process_trades_section(self, section_data: List, df: pd.DataFrame):
        """Process Trades section"""
        logger.info("📊 Processing Trades...")

        # Find header row
        header_idx = None
        for idx, row in df.iterrows():
            first_col = str(row[0]).strip() if pd.notna(row[0]) else ""
            if first_col == 'Trades':
                # Look for header row (usually "Header")
                if idx + 1 < len(df):
                    next_row = df.iloc[idx + 1]
                    if pd.notna(next_row[0]) and 'Header' in str(next_row[0]):
                        header_idx = idx + 1
                        break

        if header_idx is None:
            logger.warning("⚠️ No Trades header found")
            return

        # Get header names
        header_row = df.iloc[header_idx]
        headers = [str(h).strip() for h in header_row if pd.notna(h)]
        logger.debug(f"Trades headers: {headers}")

        # Process data rows
        data_start = header_idx + 1
        count = 0

        for idx in range(data_start, len(df)):
            row = df. iloc[idx]
            first_col = str(row[0]).strip() if pd.notna(row[0]) else ""

            # Stop at next section
            if first_col in ['Dividends', 'Withholding Tax', 'Fees', 'Open Positions', 'Interest']:
                break

            # Skip empty rows
            if pd.isna(row[0]):
                continue

            try:
                # Map columns - adjust based on actual IBKR format
                asset_type = self._safe_str(row[1]) if len(row) > 1 else ''
                currency = self._safe_str(row[2]) if len(row) > 2 else 'CHF'
                symbol = self._safe_str(row[3]) if len(row) > 3 else ''
                date_str = self._safe_str(row[4]) if len(row) > 4 else ''
                quantity = self._safe_float(row[5]) if len(row) > 5 else 0.0
                price = self._safe_float(row[6]) if len(row) > 6 else 0.0
                amount = self._safe_float(row[7]) if len(row) > 7 else 0.0
                commission = self._safe_float(row[8]) if len(row) > 8 else 0.0

                if symbol and date_str and quantity != 0:
                    self.transactions.append({
                        'type': asset_type,
                        'currency': currency,
                        'symbol': symbol,
                        'date': date_str,
                        'quantity': quantity,
                        'price': price,
                        'proceeds': amount,
                        'commission': commission,
                        'proceeds_chf': self._convert_to_chf(amount, currency),
                        'commission_chf': self._convert_to_chf(commission, currency)
                    })
                    count += 1
            except (ValueError, IndexError) as e:
                logger.debug(f"Skipping row {idx}: {e}")
                continue

        logger.info(f"✅ Processed {count} trades")

    def _process_dividends_section(self, section_data: List, df: pd. DataFrame):
        """Process Dividends section"""
        logger.info("💰 Processing Dividends...")

        # Find header row
        header_idx = None
        for idx, row in df.iterrows():
            first_col = str(row[0]).strip() if pd.notna(row[0]) else ""
            if first_col == 'Dividends':
                if idx + 1 < len(df):
                    next_row = df.iloc[idx + 1]
                    if pd. notna(next_row[0]) and 'Header' in str(next_row[0]):
                        header_idx = idx + 1
                        break

        if header_idx is None:
            logger.warning("⚠️ No Dividends header found")
            return

        # Get header names
        header_row = df.iloc[header_idx]
        headers = [str(h).strip() for h in header_row if pd.notna(h)]
        logger.debug(f"Dividends headers: {headers}")

        # Process data rows
        data_start = header_idx + 1
        count = 0

        for idx in range(data_start, len(df)):
            row = df.iloc[idx]
            first_col = str(row[0]).strip() if pd.notna(row[0]) else ""

            # Stop at next section
            if first_col in ['Trades', 'Withholding Tax', 'Fees', 'Open Positions', 'Interest']:
                break

            if pd.isna(row[0]):
                continue

            try:
                # Map columns - adjust based on actual IBKR format
                symbol = self._safe_str(row[1]) if len(row) > 1 else ''
                date_str = self._safe_str(row[2]) if len(row) > 2 else ''
                currency = self._safe_str(row[3]) if len(row) > 3 else 'CHF'
                amount = self._safe_float(row[-1])  # Last column usually has amount

                if symbol and date_str and amount != 0:
                    self.dividends.append({
                        'currency': currency,
                        'date': date_str,
                        'symbol': symbol,
                        'amount': amount,
                        'amount_chf': self._convert_to_chf(amount, currency)
                    })
                    count += 1
            except (ValueError, IndexError) as e:
                logger.debug(f"Skipping row {idx}: {e}")
                continue

        logger.info(f"✅ Processed {count} dividends")

    def _process_withholding_tax_section(self, section_data: List, df: pd.DataFrame):
        """Process Withholding Tax section"""
        logger.info("🏛️ Processing Withholding Tax...")

        # Find header row
        header_idx = None
        for idx, row in df.iterrows():
            first_col = str(row[0]).strip() if pd.notna(row[0]) else ""
            if first_col == 'Withholding Tax':
                if idx + 1 < len(df):
                    next_row = df.iloc[idx + 1]
                    if pd.notna(next_row[0]) and 'Header' in str(next_row[0]):
                        header_idx = idx + 1
                        break

        if header_idx is None:
            logger.warning("⚠️ No Withholding Tax header found")
            return

        # Get header names
        header_row = df.iloc[header_idx]
        headers = [str(h).strip() for h in header_row if pd.notna(h)]
        logger.debug(f"Withholding Tax headers: {headers}")

        # Process data rows
        data_start = header_idx + 1
        count = 0

        for idx in range(data_start, len(df)):
            row = df. iloc[idx]
            first_col = str(row[0]). strip() if pd.notna(row[0]) else ""

            # Stop at next section
            if first_col in ['Trades', 'Dividends', 'Fees', 'Open Positions', 'Interest']:
                break

            if pd.isna(row[0]):
                continue

            try:
                # Map columns
                symbol = self._safe_str(row[1]) if len(row) > 1 else ''
                date_str = self._safe_str(row[2]) if len(row) > 2 else ''
                currency = self._safe_str(row[3]) if len(row) > 3 else 'CHF'
                amount = abs(self._safe_float(row[-1]))

                if symbol and date_str and amount != 0:
                    self.taxes.append({
                        'currency': currency,
                        'date': date_str,
                        'symbol': symbol,
                        'amount': amount,
                        'amount_chf': abs(self._convert_to_chf(amount, currency))
                    })
                    count += 1
            except (ValueError, IndexError) as e:
                logger.debug(f"Skipping row {idx}: {e}")
                continue

        logger.info(f"✅ Processed {count} withholding taxes")

    def _process_fees_section(self, section_data: List, df: pd.DataFrame):
        """Process Fees section"""
        logger.info("💸 Processing Fees...")

        # Find header row
        header_idx = None
        for idx, row in df.iterrows():
            first_col = str(row[0]).strip() if pd.notna(row[0]) else ""
            if first_col == 'Fees':
                if idx + 1 < len(df):
                    next_row = df.iloc[idx + 1]
                    if pd.notna(next_row[0]) and 'Header' in str(next_row[0]):
                        header_idx = idx + 1
                        break

        if header_idx is None:
            logger.warning("⚠️ No Fees header found")
            return

        # Get header names
        header_row = df. iloc[header_idx]
        headers = [str(h).strip() for h in header_row if pd.notna(h)]
        logger.debug(f"Fees headers: {headers}")

        # Process data rows
        data_start = header_idx + 1
        count = 0

        for idx in range(data_start, len(df)):
            row = df.iloc[idx]
            first_col = str(row[0]).strip() if pd. notna(row[0]) else ""

            # Stop at next section
            if first_col in ['Trades', 'Dividends', 'Withholding Tax', 'Open Positions', 'Interest']:
                break

            if pd.isna(row[0]):
                continue

            try:
                # Map columns
                fee_type = self._safe_str(row[1]) if len(row) > 1 else ''
                date_str = self._safe_str(row[2]) if len(row) > 2 else ''
                currency = self._safe_str(row[3]) if len(row) > 3 else 'CHF'
                amount = abs(self._safe_float(row[-1]))

                if date_str and amount != 0:
                    self.fees.append({
                        'type': fee_type,
                        'currency': currency,
                        'date': date_str,
                        'amount': amount,
                        'amount_chf': self._convert_to_chf(amount, currency)
                    })
                    count += 1
            except (ValueError, IndexError) as e:
                logger.debug(f"Skipping row {idx}: {e}")
                continue

        logger.info(f"✅ Processed {count} fees")

    def _process_interest_section(self, section_data: List, df: pd.DataFrame):
        """Process Interest section"""
        logger.info("📈 Processing Interest...")

        # Find header row
        header_idx = None
        for idx, row in df.iterrows():
            first_col = str(row[0]).strip() if pd.notna(row[0]) else ""
            if first_col == 'Interest':
                if idx + 1 < len(df):
                    next_row = df. iloc[idx + 1]
                    if pd.notna(next_row[0]) and 'Header' in str(next_row[0]):
                        header_idx = idx + 1
                        break

        if header_idx is None:
            logger. warning("⚠️ No Interest header found")
            return

        # Get header names
        header_row = df.iloc[header_idx]
        headers = [str(h).strip() for h in header_row if pd.notna(h)]
        logger. debug(f"Interest headers: {headers}")

        # Process data rows
        data_start = header_idx + 1
        count = 0

        for idx in range(data_start, len(df)):
            row = df.iloc[idx]
            first_col = str(row[0]).strip() if pd.notna(row[0]) else ""

            # Stop at next section
            if first_col in ['Trades', 'Dividends', 'Withholding Tax', 'Fees', 'Open Positions']:
                break

            if pd. isna(row[0]):
                continue

            try:
                # Map columns
                currency = self._safe_str(row[1]) if len(row) > 1 else 'CHF'
                date_str = self._safe_str(row[2]) if len(row) > 2 else ''
                amount = self._safe_float(row[-1])

                if date_str and amount != 0:
                    self.dividends.append({
                        'currency': currency,
                        'date': date_str,
                        'amount': amount,
                        'type': 'Interest',
                        'amount_chf': self._convert_to_chf(amount, currency)
                    })
                    count += 1
            except (ValueError, IndexError) as e:
                logger.debug(f"Skipping row {idx}: {e}")
                continue

        logger.info(f"✅ Processed {count} interest entries")

    def _process_open_positions_section(self, section_data: List, df: pd.DataFrame):
        """Process Open Positions section"""
        logger.info("📍 Processing Open Positions...")

        # Find header row
        header_idx = None
        for idx, row in df.iterrows():
            first_col = str(row[0]).strip() if pd. notna(row[0]) else ""
            if first_col == 'Open Positions':
                if idx + 1 < len(df):
                    next_row = df.iloc[idx + 1]
                    if pd.notna(next_row[0]) and 'Header' in str(next_row[0]):
                        header_idx = idx + 1
                        break

        if header_idx is None:
            logger.warning("⚠️ No Open Positions header found")
            return

        # Get header names
        header_row = df.iloc[header_idx]
        headers = [str(h).strip() for h in header_row if pd.notna(h)]
        logger.debug(f"Open Positions headers: {headers}")

        # Process data rows
        data_start = header_idx + 1
        count = 0

        for idx in range(data_start, len(df)):
            row = df.iloc[idx]
            first_col = str(row[0]).strip() if pd.notna(row[0]) else ""

            # Stop at next section
            if first_col in ['Trades', 'Dividends', 'Withholding Tax', 'Fees', 'Interest']:
                break

            if pd.isna(row[0]):
                continue

            try:
                # Map columns - adjust based on actual IBKR format
                symbol = self._safe_str(row[1]) if len(row) > 1 else ''
                currency = self._safe_str(row[2]) if len(row) > 2 else 'CHF'
                quantity = self._safe_float(row[3]) if len(row) > 3 else 0.0
                price = self._safe_float(row[4]) if len(row) > 4 else 0.0
                value = self._safe_float(row[5]) if len(row) > 5 else 0.0
                unrealized_pl = self._safe_float(row[6]) if len(row) > 6 else 0.0

                if symbol and quantity != 0:
                    self.open_positions.append({
                        'symbol': symbol,
                        'currency': currency,
                        'quantity': quantity,
                        'price': price,
                        'value_chf': self._convert_to_chf(value, currency),
                        'unrealized_pl': unrealized_pl
                    })
                    count += 1
            except (ValueError, IndexError) as e:
                logger.debug(f"Skipping row {idx}: {e}")
                continue

        logger.info(f"✅ Processed {count} open positions")

    def _convert_to_chf(self, amount: float, currency: str) -> float:
        """Convert amount to CHF"""
        if currency == 'CHF' or pd.isna(currency):
            return amount

        rate = self.fx_rates.get(currency, 1.0)
        return amount * rate

    def _safe_float(self, value) -> float:
        """Safely convert to float"""
        if pd.isna(value) or value == '':
            return 0.0
        try:
            return float(str(value).replace(',', '.'). strip())
        except (ValueError, AttributeError):
            return 0.0

    def _safe_str(self, value) -> str:
        """Safely convert to string"""
        if pd.isna(value) or value == '':
            return ''
        return str(value).strip()

    def calculate_summary(self):
        """Calculate tax summary"""
        logger.info("🧮 Calculating summary...")

        # Capital gains
        total_proceeds = sum([t['proceeds_chf'] for t in self. transactions if t['type'] == 'Stocks'])
        total_commissions = sum([t['commission_chf'] for t in self.transactions])

        # Dividend income
        total_dividends = sum([d['amount_chf'] for d in self.dividends if d. get('type') != 'Interest'])

        # Interest income
        total_interest = sum([d['amount_chf'] for d in self.dividends if d.get('type') == 'Interest'])

        # Withholding taxes
        total_taxes = sum([t['amount_chf'] for t in self.taxes])

        # Forex gains
        total_forex = sum([t['proceeds_chf'] for t in self.transactions if t['type'] == 'Forex'])

        # Open positions value
        total_open_value = sum([p['value_chf'] for p in self.open_positions])

        self.summary = {
            'tax_year': self.tax_year,
            'canton': self.canton,
            'total_proceeds': total_proceeds,
            'total_commissions': total_commissions,
            'total_dividends': total_dividends,
            'total_interest': total_interest,
            'total_withholding_taxes': total_taxes,
            'total_forex_gains': total_forex,
            'total_open_positions_value': total_open_value,
            'report_date': datetime.now().strftime('%Y-%m-%d')
        }

        logger.info("✅ Summary calculated")

    def generate_excel_report(self, output_file: str = 'tax_report_2025.xlsx'):
        """Generate comprehensive Excel report"""
        logger.info(f"📊 Generating Excel report: {output_file}")

        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Sheet 1: Summary
            self._write_summary_sheet(writer)

            # Sheet 2: Detailed Trades
            self._write_trades_sheet(writer)

            # Sheet 3: Forex
            self._write_forex_sheet(writer)

            # Sheet 4: Dividends & Taxes
            self._write_dividends_sheet(writer)

            # Sheet 5: Interest
            self._write_interest_sheet(writer)

            # Sheet 6: Open Positions
            self._write_positions_sheet(writer)

            # Sheet 7: Costs & Fees
            self._write_fees_sheet(writer)

        logger.info(f"✅ Excel report generated: {output_file}")

    def _write_summary_sheet(self, writer):
        """Write summary sheet"""
        summary_data = [
            ['RAPORT PODATKOWY - BASEL-LANDSCHAFT', ''],
            ['', ''],
            ['Rok podatkowy:', self.summary['tax_year']],
            ['Kanton:', self.summary['canton']],
            ['Data raportu:', self.summary['report_date']],
            ['', ''],
            ['PRZYCHODY', 'CHF'],
            ['Dywidendy (brutto):', f"{self.summary['total_dividends']:.2f}"],
            ['Odsetki:', f"{self.summary['total_interest']:.2f}"],
            ['Zyski z forex:', f"{self.summary['total_forex_gains']:.2f}"],
            ['', ''],
            ['KOSZTY', 'CHF'],
            ['Prowizje i opłaty:', f"{self.summary['total_commissions']:.2f}"],
            ['', ''],
            ['PODATKI U ŹRÓDŁA', 'CHF'],
            ['Całkowite podatki u źródła:', f"{self.summary['total_withholding_taxes']:.2f}"],
            ['', ''],
            ['POZYCJE OTWARTE', 'CHF'],
            ['Łączna wartość pozycji:', f"{self.summary['total_open_positions_value']:.2f}"],
        ]

        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name='PODSUMOWANIE', index=False, header=False)

    def _write_trades_sheet(self, writer):
        """Write trades sheet"""
        trades_df = pd.DataFrame(self.transactions)
        if len(trades_df) > 0:
            trades_df = trades_df[['date', 'type', 'symbol', 'quantity', 'price', 'proceeds_chf', 'commission_chf']]
            trades_df. columns = ['Data', 'Typ', 'Symbol', 'Ilość', 'Cena', 'Wartość CHF', 'Komisja CHF']
            trades_df. to_excel(writer, sheet_name='TRANSAKCJE_SZCZEGÓŁOWE', index=False)

    def _write_forex_sheet(self, writer):
        """Write forex sheet"""
        forex_df = pd.DataFrame(self.transactions)
        if len(forex_df) > 0:
            forex_df = forex_df[forex_df['type'] == 'Forex']
            if len(forex_df) > 0:
                forex_df = forex_df[['date', 'symbol', 'quantity', 'proceeds_chf']]
                forex_df.columns = ['Data', 'Para walut', 'Ilość', 'Wartość CHF']
                forex_df.to_excel(writer, sheet_name='FOREX', index=False)

    def _write_dividends_sheet(self, writer):
        """Write dividends sheet"""
        divs = [d for d in self.dividends if d.get('type') != 'Interest']
        if divs:
            div_df = pd.DataFrame(divs)
            div_df = div_df[['date', 'currency', 'amount', 'amount_chf']]
            div_df.columns = ['Data', 'Waluta', 'Kwota', 'CHF']
            div_df. to_excel(writer, sheet_name='DYWIDENDY', index=False)

    def _write_interest_sheet(self, writer):
        """Write interest sheet"""
        interests = [d for d in self. dividends if d.get('type') == 'Interest']
        if interests:
            int_df = pd.DataFrame(interests)
            int_df = int_df[['date', 'currency', 'amount', 'amount_chf']]
            int_df.columns = ['Data', 'Waluta', 'Kwota', 'CHF']
            int_df. to_excel(writer, sheet_name='ODSETKI', index=False)

    def _write_positions_sheet(self, writer):
        """Write open positions sheet"""
        if self.open_positions:
            pos_df = pd.DataFrame(self.open_positions)
            pos_df = pos_df[['symbol', 'quantity', 'value_chf', 'unrealized_pl']]
            pos_df.columns = ['Symbol', 'Ilość', 'Wartość CHF', 'P&L niezrealizowany']
            pos_df.to_excel(writer, sheet_name='POZYCJE_OTWARTE', index=False)

    def _write_fees_sheet(self, writer):
        """Write fees sheet"""
        all_fees = []

        # Add trading commissions
        for t in self.transactions:
            if t['commission_chf'] > 0:
                all_fees.append({
                    'date': t['date'],
                    'type': 'Komisja',
                    'symbol': t['symbol'],
                    'amount_chf': t['commission_chf']
                })

        # Add other fees
        for f in self. fees:
            all_fees. append({
                'date': f['date'],
                'type': f. get('type', 'Opłata'),
                'symbol': '',
                'amount_chf': f['amount_chf']
            })

        if all_fees:
            fees_df = pd.DataFrame(all_fees)
            fees_df = fees_df[['date', 'type', 'symbol', 'amount_chf']]
            fees_df.columns = ['Data', 'Typ', 'Symbol', 'CHF']
            fees_df. to_excel(writer, sheet_name='KOSZTY', index=False)

    def generate_html_report(self, output_file: str = 'tax_report_2025.html'):
        """Generate HTML preview report"""
        logger.info(f"🌐 Generating HTML report: {output_file}")

        html = f"""<! DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Raport Podatkowy IBKR - {self.tax_year}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .content {{
            padding: 40px;
        }}

        . summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .summary-card {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            border-radius: 5px;
        }}

        . summary-card h3 {{
            color: #667eea;
            font-size: 0.9em;
            text-transform: uppercase;
            margin-bottom: 10px;
        }}

        .summary-card . value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #333;
        }}

        .summary-card .unit {{
            color: #999;
            font-size: 0.9em;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}

        table thead {{
            background: #f8f9fa;
        }}

        table th {{
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #667eea;
            border-bottom: 2px solid #667eea;
        }}

        table td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
        }}

        table tbody tr:hover {{
            background: #f8f9fa;
        }}

        .section-title {{
            font-size: 1.5em;
            color: #667eea;
            margin-top: 40px;
            margin-bottom: 20px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}

        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #999;
            font-size: 0.9em;
            border-top: 1px solid #eee;
            margin-top: 40px;
        }}

        .positive {{
            color: #28a745;
        }}

        .negative {{
            color: #dc3545;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Raport Podatkowy IBKR</h1>
            <p>Canton Basel-Landschaft | Rok: {self.summary['tax_year']}</p>
        </div>

        <div class="content">
            <div class="summary-grid">
                <div class="summary-card">
                    <h3>Dywidendy (brutto)</h3>
                    <div class="value positive">{self.summary['total_dividends']:. 2f}</div>
                    <div class="unit">CHF</div>
                </div>

                <div class="summary-card">
                    <h3>Odsetki</h3>
                    <div class="value positive">{self.summary['total_interest']:.2f}</div>
                    <div class="unit">CHF</div>
                </div>

                <div class="summary-card">
                    <h3>Zyski z Forex</h3>
                    <div class="value">{self.summary['total_forex_gains']:.2f}</div>
                    <div class="unit">CHF</div>
                </div>

                <div class="summary-card">
                    <h3>Koszty (prowizje)</h3>
                    <div class="value negative">-{self.summary['total_commissions']:.2f}</div>
                    <div class="unit">CHF</div>
                </div>

                <div class="summary-card">
                    <h3>Podatki u źródła</h3>
                    <div class="value negative">-{self.summary['total_withholding_taxes']:.2f}</div>
                    <div class="unit">CHF</div>
                </div>

                <div class="summary-card">
                    <h3>Pozycje otwarte</h3>
                    <div class="value">{self.summary['total_open_positions_value']:.2f}</div>
                    <div class="unit">CHF</div>
                </div>
            </div>

            <div class="section-title">Transakcje akcji (Szczegóły)</div>
            {self._generate_trades_table()}

            <div class="section-title">Dywidendy</div>
            {self._generate_dividends_table()}

            <div class="section-title">Pozycje otwarte</div>
            {self._generate_positions_table()}
        </div>

        <div class="footer">
            <p>Raport wygenerowany: {self.summary['report_date']} | IBKR Tax Processor v2.0</p>
            <p>Basel-Landschaft | Szwajcaria</p>
        </div>
    </div>
</body>
</html>
"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        logger.info(f"✅ HTML report generated: {output_file}")

    def _generate_trades_table(self) -> str:
        """Generate trades HTML table"""
        if not self.transactions:
            return "<p>Brak transakcji</p>"

        rows = ""
        for t in self.transactions[:20]:  # Show first 20
            rows += f"""
            <tr>
                <td>{t['date']}</td>
                <td>{t['symbol']}</td>
                <td>{t['quantity']:. 2f}</td>
                <td>{t['price']:.2f}</td>
                <td>{t['proceeds_chf']:.2f}</td>
                <td>{t['commission_chf']:.2f}</td>
            </tr>
            """

        return f"""
        <table>
            <thead>
                <tr>
                    <th>Data</th>
                    <th>Symbol</th>
                    <th>Ilość</th>
                    <th>Cena</th>
                    <th>Wartość CHF</th>
                    <th>Komisja CHF</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        """

    def _generate_dividends_table(self) -> str:
        """Generate dividends HTML table"""
        divs = [d for d in self.dividends if d. get('type') != 'Interest']
        if not divs:
            return "<p>Brak dywidend</p>"

        rows = ""
        for d in divs[:20]:
            rows += f"""
            <tr>
                <td>{d['date']}</td>
                <td>{d. get('symbol', '')}</td>
                <td>{d['currency']}</td>
                <td class="positive">{d['amount_chf']:.2f}</td>
            </tr>
            """

        return f"""
        <table>
            <thead>
                <tr>
                    <th>Data</th>
                    <th>Instrument</th>
                    <th>Waluta</th>
                    <th>Kwota CHF</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        """

    def _generate_positions_table(self) -> str:
        """Generate positions HTML table"""
        if not self.open_positions:
            return "<p>Brak otwartych pozycji</p>"

        rows = ""
        for p in self.open_positions:
            rows += f"""
            <tr>
                <td>{p['symbol']}</td>
                <td>{p['quantity']:.2f}</td>
                <td>{p['value_chf']:.2f}</td>
                <td>{p['unrealized_pl']:.2f}</td>
            </tr>
            """

        return f"""
        <table>
            <thead>
                <tr>
                    <th>Symbol</th>
                    <th>Ilość</th>
                    <th>Wartość CHF</th>
                    <th>P&L niezrealizowany</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        """

    def process(self):
        """Main processing pipeline"""
        logger.info(f"🔄 Przetwarzanie raportu IBKR dla {self.canton}...")
        logger.info(f"📂 Plik: {self.csv_file}")

        self.parse_ibkr_statement()
        logger.info(f"✅ Sparsowano {len(self.transactions)} transakcji")
        logger.info(f"✅ Sparsowano {len(self.dividends)} dywidend/odsetek")
        logger.info(f"✅ Sparsowano {len(self.taxes)} pozycji podatków")

        self.calculate_summary()
        logger.info(f"✅ Obliczono podsumowanie")

        self.generate_excel_report()
        self.generate_html_report()

        logger.info(f"\n✨ Raport został wygenerowany!")
        logger.info(f"   📊 Excel: tax_report_2025.xlsx")
        logger.info(f"   🌐 HTML: tax_report_2025.html")


if __name__ == "__main__":
    # Usage
    processor = IBKRTaxProcessor('U11673931_20250101_20251203. csv', tax_year=2025)
    processor.process()
