"""
Example usage of Basel-Landschaft Tax Report Generator

This script demonstrates how to use the report generator with IBKR statement data.
"""

import logging
from pathlib import Path
from ibkr_processor import IBKRTaxProcessor
from report_generator_bl import ReportGeneratorBL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_with_ibkr_csv(csv_file: str, output_dir: str = 'output'):
    """
    Complete example: Parse IBKR CSV and generate BL tax reports
    
    Args:
        csv_file: Path to IBKR Activity Statement CSV file
        output_dir: Directory for output reports
    """
    logger.info("=" * 80)
    logger.info("BASEL-LANDSCHAFT TAX REPORT GENERATOR - Example Usage")
    logger.info("=" * 80)
    
    # Step 1: Parse IBKR statement
    logger.info("\n📂 Step 1: Parsing IBKR Activity Statement...")
    processor = IBKRTaxProcessor(csv_file, tax_year=2025)
    processor.parse_ibkr_statement()
    
    logger.info(f"✅ Parsed:")
    logger.info(f"   - {len(processor.transactions)} transactions")
    logger.info(f"   - {len(processor.dividends)} dividend/interest entries")
    logger.info(f"   - {len(processor.taxes)} withholding tax entries")
    logger.info(f"   - {len(processor.open_positions)} open positions")
    
    # Step 2: Prepare data for report generator
    logger.info("\n🔄 Step 2: Preparing data for tax calculator...")
    parsed_data = {
        'transactions': processor.transactions,
        'dividends': processor.dividends,
        'taxes': processor.taxes,
        'fees': processor.fees,
        'open_positions': processor.open_positions
    }
    
    # Step 3: Generate reports
    logger.info("\n📊 Step 3: Generating Basel-Landschaft tax reports...")
    generator = ReportGeneratorBL(parsed_data)
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    # Generate all formats
    reports = generator.generate_all_reports(output_dir)
    
    # Step 4: Display summary
    logger.info("\n" + "=" * 80)
    logger.info("TAX SUMMARY - BASEL-LANDSCHAFT 2025")
    logger.info("=" * 80)
    
    summary = generator.tax_summary
    
    logger.info("\n💰 WEALTH POSITION:")
    logger.info(f"   Total Assets (CHF):        {summary['wealth']['total_assets_chf']:>15,.2f}")
    logger.info(f"   Wealth Tax Rate:           {summary['wealth']['tax_rate']*100:>15,.2f}%")
    logger.info(f"   Wealth Tax (CHF):          {summary['wealth']['wealth_tax']:>15,.2f}")
    
    logger.info("\n📈 INCOME:")
    logger.info(f"   Swiss Dividends (CHF):     {summary['income']['by_source']['swiss']['dividends']:>15,.2f}")
    logger.info(f"   Foreign Dividends (CHF):   {summary['income']['by_source']['foreign']['dividends']:>15,.2f}")
    logger.info(f"   Interest (CHF):            {summary['income']['by_source']['interest']['total']:>15,.2f}")
    logger.info(f"   Total Income (CHF):        {summary['income']['total_income_chf']:>15,.2f}")
    logger.info(f"   Income Tax Rate:           {summary['income']['tax_rate']*100:>15,.2f}%")
    logger.info(f"   Income Tax (CHF):          {summary['income']['income_tax']:>15,.2f}")
    
    logger.info("\n📊 CAPITAL GAINS:")
    logger.info(f"   Realized Gains (CHF):      {summary['capital_gains']['realized_gains']:>15,.2f}")
    logger.info(f"   Realized Losses (CHF):     {summary['capital_gains']['realized_losses']:>15,.2f}")
    logger.info(f"   Net Gain/Loss (CHF):       {summary['capital_gains']['net_capital_gain_loss']:>15,.2f}")
    logger.info(f"   (Note: Private capital gains are tax-free in BL)")
    
    logger.info("\n💱 FOREX:")
    logger.info(f"   FX Gains (CHF):            {summary['fx_result']['fx_gains']:>15,.2f}")
    logger.info(f"   FX Losses (CHF):           {summary['fx_result']['fx_losses']:>15,.2f}")
    logger.info(f"   Net FX Result (CHF):       {summary['fx_result']['net_fx_result']:>15,.2f}")
    
    logger.info("\n💸 COSTS:")
    logger.info(f"   Transaction Fees (CHF):    {summary['costs']['transaction_fees']:>15,.2f}")
    logger.info(f"   Account Fees (CHF):        {summary['costs']['account_fees']:>15,.2f}")
    logger.info(f"   Total Costs (CHF):         {summary['costs']['total_deductible_costs']:>15,.2f}")
    
    logger.info("\n🏛️ FOREIGN TAX:")
    logger.info(f"   US Withholding Tax (CHF):  {summary['foreign_tax']['us_withholding_tax']:>15,.2f}")
    logger.info(f"   Other Foreign Tax (CHF):   {summary['foreign_tax']['other_foreign_tax']:>15,.2f}")
    logger.info(f"   Creditable Amount (CHF):   {summary['foreign_tax']['creditable_amount']:>15,.2f}")
    
    logger.info("\n🎯 TAX LIABILITY:")
    logger.info(f"   Wealth Tax (CHF):          {summary['tax_liability']['wealth_tax']:>15,.2f}")
    logger.info(f"   Income Tax (CHF):          {summary['tax_liability']['income_tax']:>15,.2f}")
    logger.info(f"   Gross Tax (CHF):           {summary['tax_liability']['gross_tax_liability']:>15,.2f}")
    logger.info(f"   Foreign Tax Credit (CHF):  {summary['tax_liability']['foreign_tax_credit']:>15,.2f}")
    logger.info(f"   NET TAX TO PAY (CHF):      {summary['tax_liability']['net_tax_liability']:>15,.2f}")
    
    # Step 5: Report generated files
    logger.info("\n" + "=" * 80)
    logger.info("GENERATED REPORTS:")
    logger.info("=" * 80)
    
    for format_type, path in reports.items():
        file_size = Path(path).stat().st_size
        logger.info(f"   {format_type.upper():6s}: {path} ({file_size:,} bytes)")
    
    logger.info("\n✨ Report generation complete!")
    logger.info("\nNext steps:")
    logger.info("   1. Review the Excel report (Wertschriftenverzeichnis_BL_2025.xlsx)")
    logger.info("   2. Check the PDF report (Tax_Report_BL_2025.pdf)")
    logger.info("   3. Verify calculations with your tax advisor")
    logger.info("   4. Submit to Basel-Landschaft tax authorities")
    logger.info("\n⚠️  Disclaimer: This tool is for informational purposes only.")
    logger.info("   Always verify with a qualified tax professional.\n")


def example_with_sample_data():
    """
    Example with sample data (no CSV required)
    """
    logger.info("=" * 80)
    logger.info("EXAMPLE WITH SAMPLE DATA")
    logger.info("=" * 80)
    
    # Create sample data
    sample_data = {
        'transactions': [
            {
                'type': 'Stocks',
                'symbol': 'AAPL',
                'date': '2025-03-15',
                'quantity': 10,
                'price': 150.00,
                'proceeds_chf': 1195.14,
                'commission_chf': 4.86,
                'currency': 'USD'
            },
            {
                'type': 'Stocks',
                'symbol': 'MSFT',
                'date': '2025-06-20',
                'quantity': -5,
                'price': 380.00,
                'proceeds_chf': -1518.90,
                'commission_chf': 3.10,
                'currency': 'USD'
            },
            {
                'type': 'Forex',
                'symbol': 'EUR.USD',
                'date': '2025-09-10',
                'quantity': 1000,
                'price': 1.10,
                'proceeds_chf': 42.50,
                'commission_chf': 0,
                'currency': 'EUR'
            }
        ],
        'dividends': [
            {
                'symbol': 'AAPL',
                'date': '2025-02-15',
                'currency': 'USD',
                'amount': 24.00,
                'amount_chf': 19.19,
                'type': 'Dividend'
            },
            {
                'symbol': 'MSFT',
                'date': '2025-05-15',
                'currency': 'USD',
                'amount': 18.00,
                'amount_chf': 14.39,
                'type': 'Dividend'
            },
            {
                'date': '2025-08-30',
                'currency': 'USD',
                'amount': 5.50,
                'amount_chf': 4.40,
                'type': 'Interest'
            }
        ],
        'taxes': [
            {
                'symbol': 'AAPL',
                'date': '2025-02-15',
                'currency': 'USD',
                'amount': 3.60,
                'amount_chf': 2.88,
                'country': 'US'
            },
            {
                'symbol': 'MSFT',
                'date': '2025-05-15',
                'currency': 'USD',
                'amount': 2.70,
                'amount_chf': 2.16,
                'country': 'US'
            }
        ],
        'fees': [
            {
                'type': 'Monthly Activity Fee',
                'date': '2025-12-01',
                'currency': 'USD',
                'amount': 10.00,
                'amount_chf': 8.00
            }
        ],
        'open_positions': [
            {
                'symbol': 'AAPL',
                'currency': 'USD',
                'quantity': 15,
                'price': 195.00,
                'value_chf': 2338.92,
                'unrealized_pl': 143.78
            },
            {
                'symbol': 'NVDA',
                'currency': 'USD',
                'quantity': 8,
                'price': 485.00,
                'value_chf': 3102.63,
                'unrealized_pl': 302.63
            },
            {
                'symbol': 'GOOGL',
                'currency': 'USD',
                'quantity': 12,
                'price': 140.00,
                'value_chf': 1342.59,
                'unrealized_pl': -57.41
            }
        ]
    }
    
    # Generate reports
    logger.info("\n📊 Generating reports from sample data...")
    generator = ReportGeneratorBL(sample_data)
    
    output_dir = 'sample_output'
    Path(output_dir).mkdir(exist_ok=True)
    
    reports = generator.generate_all_reports(output_dir)
    
    logger.info("\n✅ Sample reports generated:")
    for format_type, path in reports.items():
        logger.info(f"   {format_type.upper()}: {path}")
    
    # Display quick summary
    summary = generator.tax_summary
    logger.info(f"\n💰 Total Assets: CHF {summary['wealth']['total_assets_chf']:,.2f}")
    logger.info(f"📈 Total Income: CHF {summary['income']['total_income_chf']:,.2f}")
    logger.info(f"🎯 Net Tax Liability: CHF {summary['tax_liability']['net_tax_liability']:,.2f}")


def main():
    """Main example runner"""
    import sys
    
    # Check if CSV file provided
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        if Path(csv_file).exists():
            logger.info(f"Using IBKR CSV file: {csv_file}\n")
            example_with_ibkr_csv(csv_file)
        else:
            logger.error(f"CSV file not found: {csv_file}")
            logger.info("Running with sample data instead...\n")
            example_with_sample_data()
    else:
        logger.info("No CSV file provided. Running with sample data...\n")
        example_with_sample_data()
        logger.info("\n" + "=" * 80)
        logger.info("To use with your IBKR CSV file:")
        logger.info(f"   python {sys.argv[0]} path/to/your/statement.csv")
        logger.info("=" * 80)


if __name__ == "__main__":
    main()
