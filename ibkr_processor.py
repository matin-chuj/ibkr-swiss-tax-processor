"""
IBKR Activity Statement Tax Processor for Basel-Landschaft Canton
Processes IBKR CSV statements and generates Swiss tax reports
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, List, Tuple
import requests
from io import StringIO

class IBKRTaxProcessor:
    """Main processor for IBKR statements"""
    
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
        
        current_section = None
        section_data = {}
        
        for idx, row in df.iterrows():
            if pd.isna(row[0]):
                continue
                
            # Identify section
            if row[0] in ['Trades', 'Dividends', 'Withholding Tax', 'Fees', 
                         'Open Positions', 'Cash Report', 'Interest']:
                current_section = row[0]
                if current_section not in section_data:
                    section_data[current_section] = []
            
            if current_section:
                section_data[current_section].append(row. tolist())
        
        # Process each section
        if 'Trades' in section_data:
            self._process_trades(section_data['Trades'])
        if 'Dividends' in section_data:
            self._process_dividends(section_data['Dividends'])
        if 'Withholding Tax' in section_data:
            self._process_withholding_tax(section_data['Withholding Tax'])
        if 'Fees' in section_data:
            self._process_fees(section_data['Fees'])
        if 'Open Positions' in section_data:
            self._process_open_positions(section_data['Open Positions'])
        if 'Interest' in section_data:
            self._process_interest(section_data['Interest'])
    
    def _process_trades(self, trades_section: List):
        """Process trade transactions"""
        for row in trades_section:
            if len(row) < 7:
                continue
            
            # Skip headers
            if row[0] == 'Trades' and row[1] == 'Header':
                continue
            
            if row[0] == 'Trades' and row[1] == 'Data':
                try:
                    asset_type = row[2]  # Stocks, Forex, Warrants
                    currency = row[3]
                    symbol = row[4]
                    date_str = row[5]
                    quantity = self._safe_float(row[6])
                    price = self._safe_float(row[7])
                    proceeds = self._safe_float(row[8])
                    commission = self._safe_float(row[9])
                    
                    if asset_type in ['Stocks', 'Forex', 'Warrants']:
                        self.transactions.append({
                            'type': asset_type,
                            'currency': currency,
                            'symbol': symbol,
                            'date': date_str,
                            'quantity': quantity,
                            'price': price,
                            'proceeds': proceeds,
                            'commission': commission,
                            'proceeds_chf': self._convert_to_chf(proceeds, currency),
                            'commission_chf': self._convert_to_chf(commission, currency)
                        })
                except (ValueError, IndexError):
                    continue
    
    def _process_dividends(self, dividends_section: List):
        """Process dividend income"""
        for row in dividends_section:
            if len(row) < 4:
                continue
            
            if row[0] == 'Dividends' and row[1] == 'Data':
                try:
                    currency = row[2]
                    date_str = row[3]
                    amount = self._safe_float(row[-1])
                    
                    self.dividends.append({
                        'currency': currency,
                        'date': date_str,
                        'amount': amount,
                        'amount_chf': self._convert_to_chf(amount, currency)
                    })
                except (ValueError, IndexError):
                    continue
    
    def _process_withholding_tax(self, tax_section: List):
        """Process withholding taxes"""
        for row in tax_section:
            if len(row) < 5:
                continue
            
            if row[0] == 'Withholding Tax' and row[1] == 'Data':
                try:
                    currency = row[2]
                    date_str = row[3]
                    amount = self._safe_float(row[-1])
                    
                    self.taxes.append({
                        'currency': currency,
                        'date': date_str,
                        'amount': abs(amount),  # Make positive
                        'amount_chf': abs(self._convert_to_chf(amount, currency))
                    })
                except (ValueError, IndexError):
                    continue
    
    def _process_fees(self, fees_section: List):
        """Process fees"""
        for row in fees_section:
            if len(row) < 4:
                continue
            
            if row[0] == 'Fees' and row[1] == 'Data':
                try:
                    currency = row[2]
                    date_str = row[3]
                    amount = abs(self._safe_float(row[-1]))
                    
                    self.fees.append({
                        'currency': currency,
                        'date': date_str,
                        'amount': amount,
                        'amount_chf': self._convert_to_chf(amount, currency)
                    })
                except (ValueError, IndexError):
                    continue
    
    def _process_interest(self, interest_section: List):
        """Process interest income"""
        for row in interest_section:
            if len(row) < 4:
                continue
            
            if row[0] == 'Interest' and row[1] == 'Data':
                try:
                    currency = row[2]
                    date_str = row[3]
                    amount = self._safe_float(row[-1])
                    
                    self.dividends.append({
                        'currency': currency,
                        'date': date_str,
                        'amount': amount,
                        'type': 'Interest',
                        'amount_chf': self._convert_to_chf(amount, currency)
                    })
                except (ValueError, IndexError):
                    continue
    
    def _process_open_positions(self, positions_section: List):
        """Process open positions"""
        for row in positions_section:
            if len(row) < 10:
                continue
            
            if row[0] == 'Open Positions' and row[1] == 'Data' and row[2] == 'Summary':
                try:
                    symbol = row[4]
                    quantity = self._safe_float(row[5])
                    value = self._safe_float(row[-2])
                    unrealized_pl = self._safe_float(row[-3])
                    
                    self.open_positions.append({
                        'symbol': symbol,
                        'quantity': quantity,
                        'value_chf': value,
                        'unrealized_pl': unrealized_pl
                    })
                except (ValueError, IndexError):
                    continue
    
    def _convert_to_chf(self, amount: float, currency: str) -> float:
        """Convert amount to CHF"""
        if currency == 'CHF' or pd.isna(currency):
            return amount
        
        rate = self.fx_rates.get(currency, 1. 0)
        return amount * rate
    
    def _safe_float(self, value) -> float:
        """Safely convert to float"""
        if pd.isna(value) or value == '':
            return 0.0
        try:
            return float(str(value).replace(',', '.'))
        except:
            return 0.0
    
    def calculate_summary(self):
        """Calculate tax summary"""
        # Capital gains
        total_proceeds = sum([t['proceeds_chf'] for t in self. transactions if t['type'] == 'Stocks'])
        total_commissions = sum([t['commission_chf'] for t in self. transactions])
        
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
    
    def generate_excel_report(self, output_file: str = 'tax_report_2025.xlsx'):
        """Generate comprehensive Excel report"""
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
        
        print(f"✅ Excel report generated: {output_file}")
    
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
            trades_df.columns = ['Data', 'Typ', 'Symbol', 'Ilość', 'Cena', 'Wartość CHF', 'Komisja CHF']
            trades_df.to_excel(writer, sheet_name='TRANSAKCJE_SZCZEGÓŁOWE', index=False)
    
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
        for t in self. transactions:
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
                'type': 'Opłata',
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
        html = f"""
<! DOCTYPE html>
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
        
        .summary-grid {{
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
        
        .summary-card h3 {{
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
        
        . positive {{
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
            <p>Raport wygenerowany: {self.summary['report_date']} | IBKR Tax Processor v1.0</p>
            <p>Basel-Landschaft | Szwajcaria</p>
        </div>
    </div>
</body>
</html>
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ HTML report generated: {output_file}")
    
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
                <td>{d['currency']}</td>
                <td class="positive">{d['amount_chf']:.2f}</td>
            </tr>
            """
        
        return f"""
        <table>
            <thead>
                <tr>
                    <th>Data</th>
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
        print(f"🔄 Przetwarzanie raportu IBKR dla {self.canton}...")
        print(f"📂 Plik: {self.csv_file}")
        
        self.parse_ibkr_statement()
        print(f"✅ Sparsowano {len(self.transactions)} transakcji")
        print(f"✅ Sparsowano {len(self.dividends)} dywidend/odsetek")
        print(f"✅ Sparsowano {len(self.taxes)} pozycji podatków")
        
        self.calculate_summary()
        print(f"✅ Obliczono podsumowanie")
        
        self.generate_excel_report()
        self.generate_html_report()
        
        print(f"\n✨ Raport został wygenerowany!")
        print(f"   📊 Excel: tax_report_2025.xlsx")
        print(f"   🌐 HTML: tax_report_2025.html")


if __name__ == "__main__":
    # Usage
    processor = IBKRTaxProcessor('U11673931_20250101_20251203. csv', tax_year=2025)
    processor.process()
