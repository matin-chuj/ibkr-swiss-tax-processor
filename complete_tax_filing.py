"""
Complete Tax Filing Script for Basel-Landschaft 2025
Main integration script that combines parser, calculator, and report generator
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

from parser import IBKRActivityParser
from tax_calculator_bl import BaselLandschaftTaxCalculator
from report_generator_bl import BaselLandschaftReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tax_filing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class CompleteTaxFiling:
    """Complete tax filing processor for Basel-Landschaft"""
    
    def __init__(self, csv_file: str, tax_year: int = 2025, output_dir: str = '.'):
        self.csv_file = csv_file
        self.tax_year = tax_year
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info("=" * 80)
        logger.info(f"IBKR Swiss Tax Processor - Basel-Landschaft {tax_year}")
        logger.info("=" * 80)
        logger.info(f"CSV File: {csv_file}")
        logger.info(f"Output Directory: {output_dir}")
        logger.info("=" * 80)
        
    def process(self) -> bool:
        """Run complete tax filing process"""
        try:
            # Step 1: Parse IBKR Activity Statement
            logger.info("\n" + "=" * 80)
            logger.info("STEP 1: Parsing IBKR Activity Statement (KROK A)")
            logger.info("=" * 80)
            
            parser = IBKRActivityParser(self.csv_file)
            if not parser.parse():
                logger.error("❌ Failed to parse CSV file")
                return False
            
            # Get parsed data
            parser_data = {
                'trades': parser.trades,
                'dividends': parser.dividends,
                'withholding_taxes': parser.withholding_taxes,
                'interest': parser.interest,
                'fees': parser.fees,
                'open_positions': parser.open_positions,
                'cash_balances': parser.cash_balances,
                'forex_transactions': parser.forex_transactions,
                'securities_lending': parser.securities_lending,
            }
            
            summary = parser.get_summary()
            logger.info("\n📊 Parsing Summary:")
            for key, value in summary.items():
                logger.info(f"   {key}: {value}")
            
            # Step 2: Calculate taxes
            logger.info("\n" + "=" * 80)
            logger.info("STEP 2: Calculating Taxes for Basel-Landschaft (KROK B)")
            logger.info("=" * 80)
            
            calculator = BaselLandschaftTaxCalculator(
                parser_data=parser_data,
                tax_year=self.tax_year
            )
            calculator.calculate_all()
            
            tax_results = calculator.get_results()
            
            # Display tax summary
            logger.info("\n📋 Tax Summary:")
            tax_summary = tax_results['tax_summary']
            logger.info(f"   Taxable Income: CHF {tax_summary['taxable_income']:,.2f}")
            logger.info(f"   Income Tax: CHF {tax_summary['income_tax']:,.2f}")
            logger.info(f"   Taxable Wealth: CHF {tax_summary['taxable_wealth']:,.2f}")
            logger.info(f"   Wealth Tax: CHF {tax_summary['wealth_tax']:,.2f}")
            logger.info(f"   Foreign Tax Credit: CHF -{tax_summary['foreign_tax_credit']:,.2f}")
            logger.info(f"   TOTAL TAX DUE: CHF {tax_summary['total_tax_due']:,.2f}")
            
            # Step 3: Generate reports
            logger.info("\n" + "=" * 80)
            logger.info("STEP 3: Generating Reports (KROK B)")
            logger.info("=" * 80)
            
            report_gen = BaselLandschaftReportGenerator(
                tax_results=tax_results,
                tax_year=self.tax_year
            )
            
            report_files = report_gen.generate_all_reports(str(self.output_dir))
            
            # Step 4: Generate summary documentation
            logger.info("\n" + "=" * 80)
            logger.info("STEP 4: Generating Summary Documentation")
            logger.info("=" * 80)
            
            self._generate_summary_doc(tax_results, report_files)
            
            # Final summary
            logger.info("\n" + "=" * 80)
            logger.info("✅ TAX FILING COMPLETE!")
            logger.info("=" * 80)
            logger.info("\n📄 Generated Files:")
            logger.info(f"   1. {report_files['excel']}")
            logger.info(f"   2. {report_files['pdf']}")
            logger.info(f"   3. {report_files['text']}")
            logger.info(f"   4. {self.output_dir / 'tax_filing_summary.md'}")
            logger.info(f"   5. tax_filing.log")
            
            logger.info("\n💡 Next Steps:")
            logger.info("   1. Review all generated reports")
            logger.info("   2. Verify calculations with your tax advisor")
            logger.info("   3. Prepare filing documents for Basel-Landschaft tax office")
            logger.info("   4. Submit before deadline")
            
            logger.info("\n" + "=" * 80)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error during tax filing: {e}", exc_info=True)
            return False
    
    def _generate_summary_doc(self, tax_results: dict, report_files: dict):
        """Generate tax_filing_summary.md documentation"""
        summary_file = self.output_dir / 'tax_filing_summary.md'
        
        logger.info(f"📝 Generating summary documentation: {summary_file}")
        
        assets = tax_results['assets']
        income = tax_results['income']
        cg = tax_results['capital_gains']
        exp = tax_results['expenses']
        summary = tax_results['tax_summary']
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"# Tax Filing Summary - Basel-Landschaft {self.tax_year}\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## 📊 Overview\n\n")
            f.write(f"This document summarizes the complete tax filing for Basel-Landschaft canton for the year {self.tax_year}.\n\n")
            
            f.write("## 📁 Generated Files\n\n")
            f.write(f"1. **Excel Report:** `{Path(report_files['excel']).name}`\n")
            f.write(f"2. **PDF Report:** `{Path(report_files['pdf']).name}`\n")
            f.write(f"3. **Detailed Breakdown:** `{Path(report_files['text']).name}`\n\n")
            
            f.write("## 💰 Financial Summary\n\n")
            f.write("### Assets (31.12.2025)\n\n")
            f.write(f"| Category | Value (CHF) |\n")
            f.write(f"|----------|------------:|\n")
            f.write(f"| Stocks | {assets['stocks_value']:,.2f} |\n")
            f.write(f"| Cash | {assets['cash_value']:,.2f} |\n")
            f.write(f"| **Total Assets** | **{assets['total_assets']:,.2f}** |\n\n")
            
            f.write("### Income\n\n")
            f.write(f"| Source | Amount (CHF) |\n")
            f.write(f"|--------|-------------:|\n")
            f.write(f"| Dividends | {income['dividends_total']:,.2f} |\n")
            f.write(f"| Interest | {income['interest_total']:,.2f} |\n")
            f.write(f"| Securities Lending | {income['securities_lending_total']:,.2f} |\n")
            f.write(f"| Withholding Taxes | -{income['withholding_tax_total']:,.2f} |\n")
            f.write(f"| **Gross Investment Income** | **{income['gross_investment_income']:,.2f}** |\n")
            f.write(f"| **Net Investment Income** | **{income['net_investment_income']:,.2f}** |\n\n")
            
            f.write("### Capital Gains (Not Taxed)\n\n")
            f.write(f"| Category | Amount (CHF) |\n")
            f.write(f"|----------|-------------:|\n")
            f.write(f"| Realized Gains (ST) | +{cg['realized_gains_st']:,.2f} |\n")
            f.write(f"| Realized Gains (LT) | +{cg['realized_gains_lt']:,.2f} |\n")
            f.write(f"| Realized Losses (ST) | -{cg['realized_losses_st']:,.2f} |\n")
            f.write(f"| Realized Losses (LT) | -{cg['realized_losses_lt']:,.2f} |\n")
            f.write(f"| **Net Realized** | **{cg['net_realized']:,.2f}** |\n")
            f.write(f"| Unrealized Gains (ST) | +{cg['unrealized_gains_st']:,.2f} |\n")
            f.write(f"| Unrealized Gains (LT) | +{cg['unrealized_gains_lt']:,.2f} |\n")
            f.write(f"| Forex P/L | {cg['forex_pl_total']:,.2f} |\n\n")
            
            f.write("### Expenses\n\n")
            f.write(f"| Category | Amount (CHF) |\n")
            f.write(f"|----------|-------------:|\n")
            f.write(f"| Commissions | -{exp['commissions_total']:,.2f} |\n")
            f.write(f"| Other Fees | -{exp['fees_total']:,.2f} |\n")
            f.write(f"| **Total Expenses** | **-{exp['total_expenses']:,.2f}** |\n\n")
            
            f.write("## 🧾 Tax Calculation\n\n")
            f.write("### Income Tax\n\n")
            f.write(f"| Item | Amount (CHF) |\n")
            f.write(f"|------|-------------:|\n")
            f.write(f"| Gross Investment Income | {summary['gross_investment_income']:,.2f} |\n")
            f.write(f"| Deductible Expenses | -{summary['deductible_expenses']:,.2f} |\n")
            f.write(f"| **Taxable Income** | **{summary['taxable_income']:,.2f}** |\n")
            f.write(f"| Tax Rate | {summary['income_tax_rate']*100:.2f}% |\n")
            f.write(f"| **Income Tax** | **{summary['income_tax']:,.2f}** |\n\n")
            
            f.write("### Wealth Tax\n\n")
            f.write(f"| Item | Amount (CHF) |\n")
            f.write(f"|------|-------------:|\n")
            f.write(f"| Total Assets | {summary['total_assets']:,.2f} |\n")
            f.write(f"| Exemption | -{summary['wealth_exemption']:,.2f} |\n")
            f.write(f"| **Taxable Wealth** | **{summary['taxable_wealth']:,.2f}** |\n")
            f.write(f"| Tax Rate | {summary['wealth_tax_rate']*100:.3f}% |\n")
            f.write(f"| **Wealth Tax** | **{summary['wealth_tax']:,.2f}** |\n\n")
            
            f.write("### Foreign Tax Credit\n\n")
            f.write(f"| Item | Amount (CHF) |\n")
            f.write(f"|------|-------------:|\n")
            f.write(f"| Foreign Taxes Paid | {summary['foreign_tax_paid']:,.2f} |\n")
            f.write(f"| **Foreign Tax Credit** | **{summary['foreign_tax_credit']:,.2f}** |\n\n")
            
            f.write("## 💵 Final Tax Due\n\n")
            f.write(f"| Item | Amount (CHF) |\n")
            f.write(f"|------|-------------:|\n")
            f.write(f"| Income Tax | {summary['income_tax']:,.2f} |\n")
            f.write(f"| Wealth Tax | {summary['wealth_tax']:,.2f} |\n")
            f.write(f"| Subtotal | {summary['total_tax_before_credit']:,.2f} |\n")
            f.write(f"| Foreign Tax Credit | -{summary['foreign_tax_credit']:,.2f} |\n")
            f.write(f"| **TOTAL TAX DUE** | **{summary['total_tax_due']:,.2f}** |\n\n")
            
            f.write("## ⚠️ Important Notes\n\n")
            f.write(f"- {summary['capital_gains_note']}\n")
            f.write("- This report is for informational purposes only\n")
            f.write("- Please verify all calculations with a certified tax advisor\n")
            f.write("- Ensure all amounts are reported correctly to Basel-Landschaft tax authorities\n\n")
            
            f.write("## 📞 Support\n\n")
            f.write("For questions or issues with this report, please contact your tax advisor.\n\n")
            
            f.write("---\n\n")
            f.write(f"*Generated by IBKR Swiss Tax Processor v2.0 - {datetime.now().strftime('%Y-%m-%d')}*\n")
        
        logger.info(f"✅ Summary documentation created: {summary_file}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Complete tax filing for Basel-Landschaft canton'
    )
    parser.add_argument(
        'csv_file',
        help='Path to IBKR Activity Statement CSV file'
    )
    parser.add_argument(
        '--year',
        type=int,
        default=2025,
        help='Tax year (default: 2025)'
    )
    parser.add_argument(
        '--output',
        default='.',
        help='Output directory (default: current directory)'
    )
    
    args = parser.parse_args()
    
    # Check if CSV file exists
    if not Path(args.csv_file).exists():
        logger.error(f"❌ CSV file not found: {args.csv_file}")
        sys.exit(1)
    
    # Run tax filing
    filing = CompleteTaxFiling(
        csv_file=args.csv_file,
        tax_year=args.year,
        output_dir=args.output
    )
    
    success = filing.process()
    
    if success:
        logger.info("\n✨ Tax filing completed successfully!")
        sys.exit(0)
    else:
        logger.error("\n❌ Tax filing failed. Check the log for details.")
        sys.exit(1)


if __name__ == '__main__':
    main()
