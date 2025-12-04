"""
KROK B: Report Generator for Basel-Landschaft
Generates Excel, PDF, and text reports for tax filing
"""

import pandas as pd
import logging
from typing import Dict
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph,
                                 Spacer, PageBreak, Image)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

logger = logging.getLogger(__name__)


class BaselLandschaftReportGenerator:
    """Generate tax reports for Basel-Landschaft"""
    
    def __init__(self, tax_results: Dict, tax_year: int = 2025):
        self.tax_results = tax_results
        self.tax_year = tax_year
        
    def generate_all_reports(self, output_dir: str = '.'):
        """Generate all three required reports"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        logger.info("📊 Generating all reports...")
        
        # Generate Excel report (Wertschriftenverzeichnis - Assets Register)
        excel_file = output_path / f'Wertschriftenverzeichnis_BL_{self.tax_year}.xlsx'
        self.generate_excel_report(str(excel_file))
        
        # Generate PDF report (Tax Report)
        pdf_file = output_path / f'Tax_Report_BL_{self.tax_year}.pdf'
        self.generate_pdf_report(str(pdf_file))
        
        # Generate detailed breakdown
        txt_file = output_path / 'detailed_breakdown.txt'
        self.generate_detailed_breakdown(str(txt_file))
        
        logger.info("✅ All reports generated successfully")
        
        return {
            'excel': str(excel_file),
            'pdf': str(pdf_file),
            'text': str(txt_file),
        }
    
    def generate_excel_report(self, filename: str):
        """Generate comprehensive Excel report (Wertschriftenverzeichnis)"""
        logger.info(f"📊 Generating Excel report: {filename}")
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Section 1: Assets overview (Vermögensaufstellung)
            self._write_assets_sheet(writer)
            
            # Section 2: Income details (Einkünfte)
            self._write_income_sheet(writer)
            
            # Section 3: Realized capital gains (Kapitalgewinne)
            self._write_capital_gains_sheet(writer)
            
            # Section 4: Unrealized gains (Niezrealizowane zyski)
            self._write_unrealized_gains_sheet(writer)
            
            # Section 5: Deductible expenses (Koszty)
            self._write_expenses_sheet(writer)
            
            # Section 6: Foreign exchange P/L (Forex)
            self._write_forex_sheet(writer)
            
            # Section 7: Tax summary (Podsumowanie podatkowe)
            self._write_tax_summary_sheet(writer)
        
        logger.info(f"✅ Excel report created: {filename}")
    
    def _write_assets_sheet(self, writer):
        """Write Vermögensaufstellung sheet"""
        assets = self.tax_results['assets']
        
        data = [
            ['VERMÖGENSAUFSTELLUNG (Majątek na 31.12.2025)', ''],
            ['', ''],
            ['AKCJE', f"CHF {assets['stocks_value']:,.2f}"],
        ]
        
        # Add stock positions
        for stock in assets['stocks_detail']:
            data.append([
                f"  {stock['symbol']} ({stock['quantity']:.0f} shares)",
                f"CHF {stock['value_chf']:,.2f}"
            ])
        
        data.append(['', ''])
        data.append(['GOTÓWKA', f"CHF {assets['cash_value']:,.2f}"])
        
        # Add cash balances
        for cash in assets['cash_detail']:
            data.append([
                f"  {cash['currency']} {cash['amount']:,.2f}",
                f"CHF {cash['value_chf']:,.2f}"
            ])
        
        data.append(['', ''])
        data.append(['SUMA AKTYWÓW', f"CHF {assets['total_assets']:,.2f}"])
        
        df = pd.DataFrame(data, columns=['Pozycja', 'Wartość'])
        df.to_excel(writer, sheet_name='1_Vermögensaufstellung', index=False)
    
    def _write_income_sheet(self, writer):
        """Write Einkünfte (Income) sheet"""
        income = self.tax_results['income']
        
        data = [
            ['EINKÜNFTE (Dochody)', ''],
            ['', ''],
            ['DYWIDENDY', f"CHF {income['dividends_total']:,.2f}"],
        ]
        
        for div in income['dividends_detail'][:50]:  # Limit to 50 for Excel
            data.append([
                f"  {div['date']} - {div['description'][:50]}",
                f"CHF {div['amount_chf']:,.2f}"
            ])
        
        data.append(['', ''])
        data.append(['ODSETKI', f"CHF {income['interest_total']:,.2f}"])
        
        for int_item in income['interest_detail']:
            data.append([
                f"  {int_item['date']} - {int_item['description'][:50]}",
                f"CHF {int_item['amount_chf']:,.2f}"
            ])
        
        data.append(['', ''])
        data.append(['SECURITIES LENDING', f"CHF {income['securities_lending_total']:,.2f}"])
        
        for lending in income['securities_lending_detail']:
            data.append([
                f"  {lending['date']} - {lending['description'][:50]}",
                f"CHF {lending['amount_chf']:,.2f}"
            ])
        
        data.append(['', ''])
        data.append(['PODATKI POTRĄCONE U ŹRÓDŁA', f"CHF -{income['withholding_tax_total']:,.2f}"])
        
        for tax in income['withholding_tax_detail']:
            data.append([
                f"  {tax['date']} - {tax['country']} - {tax['description'][:40]}",
                f"CHF -{tax['amount_chf']:,.2f}"
            ])
        
        data.append(['', ''])
        data.append(['DOCHÓD BRUTTO', f"CHF {income['gross_investment_income']:,.2f}"])
        data.append(['DOCHÓD NETTO (po podatkach u źródła)', f"CHF {income['net_investment_income']:,.2f}"])
        
        df = pd.DataFrame(data, columns=['Pozycja', 'Kwota'])
        df.to_excel(writer, sheet_name='2_Einkünfte', index=False)
    
    def _write_capital_gains_sheet(self, writer):
        """Write Kapitalgewinne (Capital Gains) sheet"""
        cg = self.tax_results['capital_gains']
        
        data = [
            ['KAPITALGEWINNE (Zrealizowane)', ''],
            ['', ''],
            ['ZYSKI KRÓTKOTERMINOWE', f"CHF +{cg['realized_gains_st']:,.2f}"],
        ]
        
        st_gains = [g for g in cg['gains_detail'] if g['term'] == 'short']
        for gain in st_gains[:50]:
            data.append([
                f"  {gain['date']} - {gain['symbol']} ({gain['quantity']:.2f})",
                f"CHF +{gain['gain_chf']:,.2f}"
            ])
        
        data.append(['', ''])
        data.append(['ZYSKI DŁUGOTERMINOWE', f"CHF +{cg['realized_gains_lt']:,.2f}"])
        
        lt_gains = [g for g in cg['gains_detail'] if g['term'] == 'long']
        for gain in lt_gains[:50]:
            data.append([
                f"  {gain['date']} - {gain['symbol']} ({gain['quantity']:.2f})",
                f"CHF +{gain['gain_chf']:,.2f}"
            ])
        
        data.append(['', ''])
        data.append(['STRATY KRÓTKOTERMINOWE', f"CHF -{cg['realized_losses_st']:,.2f}"])
        
        st_losses = [l for l in cg['losses_detail'] if l['term'] == 'short']
        for loss in st_losses[:50]:
            data.append([
                f"  {loss['date']} - {loss['symbol']} ({loss['quantity']:.2f})",
                f"CHF -{loss['loss_chf']:,.2f}"
            ])
        
        data.append(['', ''])
        data.append(['STRATY DŁUGOTERMINOWE', f"CHF -{cg['realized_losses_lt']:,.2f}"])
        
        lt_losses = [l for l in cg['losses_detail'] if l['term'] == 'long']
        for loss in lt_losses[:50]:
            data.append([
                f"  {loss['date']} - {loss['symbol']} ({loss['quantity']:.2f})",
                f"CHF -{loss['loss_chf']:,.2f}"
            ])
        
        data.append(['', ''])
        data.append(['NETTO ZREALIZOWANE', f"CHF {cg['net_realized']:,.2f}"])
        data.append(['', ''])
        data.append(['UWAGA:', 'Zyski kapitałowe nie są opodatkowane dla inwestorów prywatnych w BL'])
        
        df = pd.DataFrame(data, columns=['Transakcja', 'Kwota'])
        df.to_excel(writer, sheet_name='3_Kapitalgewinne', index=False)
    
    def _write_unrealized_gains_sheet(self, writer):
        """Write Unrealized Gains sheet"""
        cg = self.tax_results['capital_gains']
        
        data = [
            ['NIEZREALIZOWANE ZYSKI', ''],
            ['', ''],
            ['KRÓTKOTERMINOWE', f"CHF +{cg['unrealized_gains_st']:,.2f}"],
        ]
        
        for unreal in cg['unrealized_detail']:
            data.append([
                f"  {unreal['symbol']} ({unreal['quantity']:.2f})",
                f"CHF +{unreal['unrealized_pl_chf']:,.2f}"
            ])
        
        data.append(['', ''])
        data.append(['DŁUGOTERMINOWE', f"CHF +{cg['unrealized_gains_lt']:,.2f}"])
        
        df = pd.DataFrame(data, columns=['Pozycja', 'Kwota'])
        df.to_excel(writer, sheet_name='4_Niezrealizowane', index=False)
    
    def _write_expenses_sheet(self, writer):
        """Write Expenses sheet"""
        exp = self.tax_results['expenses']
        
        data = [
            ['KOSZTY (Wydatki)', ''],
            ['', ''],
            ['PROWIZJE HANDLOWE', f"CHF -{exp['commissions_total']:,.2f}"],
        ]
        
        for comm in exp['commissions_detail'][:100]:
            data.append([
                f"  {comm['date']} - {comm['symbol']}",
                f"CHF -{comm['commission_chf']:,.2f}"
            ])
        
        data.append(['', ''])
        data.append(['INNE OPŁATY', f"CHF -{exp['fees_total']:,.2f}"])
        
        for fee in exp['fees_detail']:
            data.append([
                f"  {fee['date']} - {fee['subtitle']} - {fee['description'][:40]}",
                f"CHF -{fee['amount_chf']:,.2f}"
            ])
        
        data.append(['', ''])
        data.append(['SUMA KOSZTÓW', f"CHF -{exp['total_expenses']:,.2f}"])
        
        df = pd.DataFrame(data, columns=['Koszt', 'Kwota'])
        df.to_excel(writer, sheet_name='5_Koszty', index=False)
    
    def _write_forex_sheet(self, writer):
        """Write Forex P/L sheet"""
        cg = self.tax_results['capital_gains']
        
        data = [
            ['FOREX P/L (Zyski/Straty walutowe)', ''],
            ['', ''],
        ]
        
        for forex in cg['forex_detail']:
            sign = '+' if forex['realized_pl_chf'] >= 0 else ''
            data.append([
                f"  {forex['date']} - {forex['symbol']} ({forex['quantity']:.2f})",
                f"CHF {sign}{forex['realized_pl_chf']:,.2f}"
            ])
        
        data.append(['', ''])
        data.append(['SUMA FOREX', f"CHF {cg['forex_pl_total']:,.2f}"])
        
        df = pd.DataFrame(data, columns=['Transakcja', 'P/L'])
        df.to_excel(writer, sheet_name='6_Forex', index=False)
    
    def _write_tax_summary_sheet(self, writer):
        """Write Tax Summary sheet"""
        summary = self.tax_results['tax_summary']
        
        data = [
            ['PODSUMOWANIE PODATKOWE - BASEL-LANDSCHAFT', ''],
            ['Rok podatkowy:', self.tax_year],
            ['Kanton:', summary['canton']],
            ['', ''],
            ['═══ DOCHÓD ═══', ''],
            ['Dochód brutto z inwestycji:', f"CHF {summary['gross_investment_income']:,.2f}"],
            ['Koszty do odliczenia:', f"CHF -{summary['deductible_expenses']:,.2f}"],
            ['Dochód opodatkowany:', f"CHF {summary['taxable_income']:,.2f}"],
            ['', ''],
            ['═══ MAJĄTEK ═══', ''],
            ['Suma aktywów:', f"CHF {summary['total_assets']:,.2f}"],
            ['Zwolnienie z podatku majątkowego:', f"CHF -{summary['wealth_exemption']:,.2f}"],
            ['Majątek opodatkowany:', f"CHF {summary['taxable_wealth']:,.2f}"],
            ['', ''],
            ['═══ PODATKI ═══', ''],
            [f"Podatek dochodowy ({summary['income_tax_rate']*100:.2f}%):", f"CHF {summary['income_tax']:,.2f}"],
            [f"Podatek majątkowy ({summary['wealth_tax_rate']*100:.3f}%):", f"CHF {summary['wealth_tax']:,.2f}"],
            ['Podatek przed odliczeniem:', f"CHF {summary['total_tax_before_credit']:,.2f}"],
            ['', ''],
            ['Podatki zagraniczne zapłacone:', f"CHF -{summary['foreign_tax_paid']:,.2f}"],
            ['Odliczenie podatku zagranicznego:', f"CHF -{summary['foreign_tax_credit']:,.2f}"],
            ['', ''],
            ['═══ DO ZAPŁATY ═══', ''],
            ['SUMA PODATKU DO ZAPŁATY:', f"CHF {summary['total_tax_due']:,.2f}"],
            ['', ''],
            ['UWAGA:', summary['capital_gains_note']],
        ]
        
        df = pd.DataFrame(data, columns=['Pozycja', 'Wartość'])
        df.to_excel(writer, sheet_name='7_Podsumowanie', index=False)
    
    def generate_pdf_report(self, filename: str):
        """Generate professional PDF report"""
        logger.info(f"📄 Generating PDF report: {filename}")
        
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
            alignment=TA_CENTER,
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=12,
            spaceBefore=20,
        )
        
        # Title
        story.append(Paragraph(f"Tax Report {self.tax_year}", title_style))
        story.append(Paragraph("Basel-Landschaft Canton", styles['Normal']))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%d.%m.%Y')}", styles['Normal']))
        story.append(Spacer(1, 1*cm))
        
        # Tax Summary
        story.append(Paragraph("Tax Summary", heading_style))
        summary = self.tax_results['tax_summary']
        
        summary_data = [
            ['Item', 'Amount (CHF)'],
            ['Taxable Income', f"{summary['taxable_income']:,.2f}"],
            ['Income Tax (10.55%)', f"{summary['income_tax']:,.2f}"],
            ['Taxable Wealth', f"{summary['taxable_wealth']:,.2f}"],
            ['Wealth Tax (0.08%)', f"{summary['wealth_tax']:,.2f}"],
            ['Foreign Tax Credit', f"-{summary['foreign_tax_credit']:,.2f}"],
            ['', ''],
            ['Total Tax Due', f"{summary['total_tax_due']:,.2f}"],
        ]
        
        summary_table = Table(summary_data, colWidths=[12*cm, 5*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8F8F5')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 14),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Assets Overview
        story.append(Paragraph("Assets Overview", heading_style))
        assets = self.tax_results['assets']
        
        assets_data = [
            ['Category', 'Value (CHF)'],
            ['Stocks', f"{assets['stocks_value']:,.2f}"],
            ['Cash', f"{assets['cash_value']:,.2f}"],
            ['Total Assets', f"{assets['total_assets']:,.2f}"],
        ]
        
        assets_table = Table(assets_data, colWidths=[12*cm, 5*cm])
        assets_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ECC71')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(assets_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Income Overview
        story.append(Paragraph("Income Overview", heading_style))
        income = self.tax_results['income']
        
        income_data = [
            ['Source', 'Amount (CHF)'],
            ['Dividends', f"{income['dividends_total']:,.2f}"],
            ['Interest', f"{income['interest_total']:,.2f}"],
            ['Securities Lending', f"{income['securities_lending_total']:,.2f}"],
            ['Withholding Tax', f"-{income['withholding_tax_total']:,.2f}"],
            ['Net Investment Income', f"{income['net_investment_income']:,.2f}"],
        ]
        
        income_table = Table(income_data, colWidths=[12*cm, 5*cm])
        income_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F39C12')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(income_table)
        story.append(Spacer(1, 1*cm))
        
        # Important Notes
        story.append(Paragraph("Important Notes", heading_style))
        story.append(Paragraph(
            "• Capital gains are tax-free for private investors in Basel-Landschaft",
            styles['Normal']
        ))
        story.append(Paragraph(
            "• This report is for informational purposes only",
            styles['Normal']
        ))
        story.append(Paragraph(
            "• Please consult with a tax advisor before filing",
            styles['Normal']
        ))
        
        # Build PDF
        doc.build(story)
        logger.info(f"✅ PDF report created: {filename}")
    
    def generate_detailed_breakdown(self, filename: str):
        """Generate detailed text breakdown"""
        logger.info(f"📝 Generating detailed breakdown: {filename}")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"DETAILED TAX BREAKDOWN - BASEL-LANDSCHAFT {self.tax_year}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            # Assets
            f.write("═══ ASSETS (Vermögensaufstellung) ═══\n\n")
            assets = self.tax_results['assets']
            
            f.write(f"Stocks: CHF {assets['stocks_value']:,.2f}\n")
            for stock in assets['stocks_detail']:
                f.write(f"  {stock['symbol']:10s} {stock['quantity']:>10.2f} shares  CHF {stock['value_chf']:>12,.2f}\n")
            
            f.write(f"\nCash: CHF {assets['cash_value']:,.2f}\n")
            for cash in assets['cash_detail']:
                f.write(f"  {cash['currency']:5s} {cash['amount']:>15,.2f}  CHF {cash['value_chf']:>12,.2f}\n")
            
            f.write(f"\nTotal Assets: CHF {assets['total_assets']:,.2f}\n\n")
            
            # Income
            f.write("═══ INCOME (Einkünfte) ═══\n\n")
            income = self.tax_results['income']
            
            f.write(f"Dividends: CHF {income['dividends_total']:,.2f}\n")
            for div in income['dividends_detail']:
                f.write(f"  {div['date']} {div['description'][:60]:60s} CHF {div['amount_chf']:>10,.2f}\n")
            
            f.write(f"\nInterest: CHF {income['interest_total']:,.2f}\n")
            for int_item in income['interest_detail']:
                f.write(f"  {int_item['date']} {int_item['description'][:60]:60s} CHF {int_item['amount_chf']:>10,.2f}\n")
            
            f.write(f"\nSecurities Lending: CHF {income['securities_lending_total']:,.2f}\n")
            for lending in income['securities_lending_detail']:
                f.write(f"  {lending['date']} {lending['description'][:60]:60s} CHF {lending['amount_chf']:>10,.2f}\n")
            
            f.write(f"\nWithholding Taxes: CHF -{income['withholding_tax_total']:,.2f}\n")
            for tax in income['withholding_tax_detail']:
                f.write(f"  {tax['date']} {tax['country']:3s} {tax['description'][:50]:50s} CHF -{tax['amount_chf']:>10,.2f}\n")
            
            f.write(f"\nGross Investment Income: CHF {income['gross_investment_income']:,.2f}\n")
            f.write(f"Net Investment Income: CHF {income['net_investment_income']:,.2f}\n\n")
            
            # Capital Gains
            f.write("═══ CAPITAL GAINS (Kapitalgewinne) ═══\n\n")
            cg = self.tax_results['capital_gains']
            
            f.write(f"Realized Gains (Short-term): CHF +{cg['realized_gains_st']:,.2f}\n")
            f.write(f"Realized Gains (Long-term): CHF +{cg['realized_gains_lt']:,.2f}\n")
            f.write(f"Realized Losses (Short-term): CHF -{cg['realized_losses_st']:,.2f}\n")
            f.write(f"Realized Losses (Long-term): CHF -{cg['realized_losses_lt']:,.2f}\n")
            f.write(f"Net Realized: CHF {cg['net_realized']:,.2f}\n\n")
            
            f.write(f"Unrealized Gains (Short-term): CHF +{cg['unrealized_gains_st']:,.2f}\n")
            f.write(f"Unrealized Gains (Long-term): CHF +{cg['unrealized_gains_lt']:,.2f}\n\n")
            
            f.write(f"Forex P/L: CHF {cg['forex_pl_total']:,.2f}\n\n")
            
            # Expenses
            f.write("═══ EXPENSES (Koszty) ═══\n\n")
            exp = self.tax_results['expenses']
            
            f.write(f"Commissions: CHF -{exp['commissions_total']:,.2f}\n")
            f.write(f"Other Fees: CHF -{exp['fees_total']:,.2f}\n")
            f.write(f"Total Expenses: CHF -{exp['total_expenses']:,.2f}\n\n")
            
            # Tax Summary
            f.write("═══ TAX SUMMARY ═══\n\n")
            summary = self.tax_results['tax_summary']
            
            f.write(f"Taxable Income: CHF {summary['taxable_income']:,.2f}\n")
            f.write(f"Income Tax ({summary['income_tax_rate']*100:.2f}%): CHF {summary['income_tax']:,.2f}\n\n")
            
            f.write(f"Taxable Wealth: CHF {summary['taxable_wealth']:,.2f}\n")
            f.write(f"Wealth Tax ({summary['wealth_tax_rate']*100:.3f}%): CHF {summary['wealth_tax']:,.2f}\n\n")
            
            f.write(f"Total Tax Before Credit: CHF {summary['total_tax_before_credit']:,.2f}\n")
            f.write(f"Foreign Tax Credit: CHF -{summary['foreign_tax_credit']:,.2f}\n\n")
            
            f.write(f"TOTAL TAX DUE: CHF {summary['total_tax_due']:,.2f}\n\n")
            
            f.write("=" * 80 + "\n")
            f.write(f"NOTE: {summary['capital_gains_note']}\n")
            f.write("=" * 80 + "\n")
        
        logger.info(f"✅ Detailed breakdown created: {filename}")
