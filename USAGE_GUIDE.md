# Complete Tax Filing Guide - Basel-Landschaft 2025

This guide explains how to use the IBKR Swiss Tax Processor to generate complete tax filing reports for Basel-Landschaft canton.

## 📋 Overview

The system processes IBKR Activity Statement CSV files and generates three comprehensive tax reports:

1. **Wertschriftenverzeichnis_BL_2025.xlsx** - Excel report with 7 detailed sections
2. **Tax_Report_BL_2025.pdf** - Professional PDF report in A4 format
3. **detailed_breakdown.txt** - Complete transaction-by-transaction breakdown
4. **tax_filing_summary.md** - Summary documentation in Markdown

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.8 or higher required
python3 --version

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Process your IBKR Activity Statement
python3 complete_tax_filing.py YOUR_ACTIVITY_STATEMENT.csv

# Specify tax year and output directory
python3 complete_tax_filing.py YOUR_ACTIVITY_STATEMENT.csv --year 2025 --output ./tax_reports_2025
```

### Example with Sample Data

```bash
# Test with included sample data
python3 complete_tax_filing.py sample_activity_statement.csv --year 2025 --output ./output
```

## 📊 Generated Reports

### 1. Excel Report (Wertschriftenverzeichnis_BL_2025.xlsx)

Contains 7 detailed sheets:

#### Sheet 1: Vermögensaufstellung (Assets)
- Stock positions with values in CHF
- Cash balances in all currencies
- Total assets calculation

#### Sheet 2: Einkünfte (Income)
- Dividends with tax withholding
- Interest income
- Securities lending income
- Withholding taxes by country

#### Sheet 3: Kapitalgewinne (Capital Gains)
- Short-term realized gains
- Long-term realized gains
- Short-term realized losses
- Long-term realized losses
- Net capital gains (not taxed in BL)

#### Sheet 4: Niezrealizowane (Unrealized Gains)
- Short-term unrealized gains
- Long-term unrealized gains

#### Sheet 5: Koszty (Expenses)
- Trading commissions
- Market data fees
- Other fees

#### Sheet 6: Forex P/L
- Foreign exchange gains and losses
- Currency conversion transactions

#### Sheet 7: Podsumowanie (Tax Summary)
- Complete tax calculation
- Income tax breakdown
- Wealth tax breakdown
- Foreign tax credit
- **Total tax due**

### 2. PDF Report (Tax_Report_BL_2025.pdf)

Professional A4 format report with:
- Tax summary tables
- Assets overview
- Income breakdown
- Important notes and disclaimers

### 3. Detailed Breakdown (detailed_breakdown.txt)

Complete transaction listing:
- All stock positions with quantities
- All cash balances
- Every dividend payment
- Every interest payment
- All withholding taxes
- Complete expense listing
- Step-by-step tax calculations

### 4. Summary Documentation (tax_filing_summary.md)

Markdown summary perfect for:
- Quick reference
- Sharing with tax advisor
- Documentation purposes

## 🧮 Tax Calculations for Basel-Landschaft

### Income Tax

```
Taxable Income = (Dividends + Interest + Securities Lending) - Deductible Expenses
Income Tax = Taxable Income × 10.55%
```

### Wealth Tax

```
Taxable Wealth = Total Assets - CHF 50,000 (exemption)
Wealth Tax = Taxable Wealth × 0.08%
```

### Foreign Tax Credit

```
Foreign Tax Credit = min(Foreign Taxes Paid, Income Tax × Foreign Income Ratio)
```

### Total Tax Due

```
Total Tax Due = (Income Tax + Wealth Tax) - Foreign Tax Credit
```

### Important Notes

- ✅ **Capital gains are TAX-FREE for private investors in Basel-Landschaft**
- Dividends and interest are fully taxable
- Deductible expenses include trading commissions and fees
- Foreign tax credit applies to income taxes paid abroad

## 📁 File Structure

```
ibkr-swiss-tax-processor/
├── complete_tax_filing.py       # Main integration script
├── parser.py                    # IBKR CSV parser (KROK A)
├── tax_calculator_bl.py         # Basel-Landschaft tax calculator (KROK B)
├── report_generator_bl.py       # Report generator (KROK B)
├── requirements.txt             # Python dependencies
├── sample_activity_statement.csv # Sample IBKR data for testing
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

## 🔧 Advanced Usage

### Custom FX Rates

The system uses default FX rates from the IBKR statement. To override:

```python
from complete_tax_filing import CompleteTaxFiling
from tax_calculator_bl import BaselLandschaftTaxCalculator

# Custom FX rates
custom_fx = {
    'CHF': 1.0,
    'EUR': 0.93500,  # Your custom rate
    'USD': 0.80000,  # Your custom rate
    # ... other currencies
}

# Use in calculator
calculator = BaselLandschaftTaxCalculator(
    parser_data=data,
    fx_rates=custom_fx,
    tax_year=2025
)
```

### Processing Multiple Years

```bash
# Process different years
python3 complete_tax_filing.py statement_2023.csv --year 2023 --output ./tax_2023
python3 complete_tax_filing.py statement_2024.csv --year 2024 --output ./tax_2024
python3 complete_tax_filing.py statement_2025.csv --year 2025 --output ./tax_2025
```

## 📝 Logging

All operations are logged to `tax_filing.log`:

```bash
# View the log
cat tax_filing.log

# Monitor in real-time
tail -f tax_filing.log
```

## ✅ Verification Checklist

Before submitting to tax authorities:

- [ ] Review all generated reports for accuracy
- [ ] Verify stock positions match your broker statement
- [ ] Confirm cash balances are correct
- [ ] Check all dividend amounts
- [ ] Verify withholding tax amounts
- [ ] Confirm total tax calculation
- [ ] Consult with certified tax advisor
- [ ] Keep copies of all reports

## 🎯 Basel-Landschaft Specific Rules

### What is Taxed

✅ **Investment Income** (Fully Taxed)
- Dividends
- Interest
- Securities lending income

✅ **Wealth** (0.08% tax)
- Total assets minus CHF 50,000 exemption

### What is NOT Taxed

❌ **Capital Gains** (Tax-Free for Private Investors)
- Realized gains from stock sales
- Unrealized gains on holdings
- Short-term vs long-term doesn't matter

### Deductions

✅ **Allowed Deductions**
- Trading commissions
- Market data fees
- Account management fees

❌ **Not Deductible**
- Forex losses (informational only)

## 🆘 Troubleshooting

### CSV Parsing Errors

**Problem:** Parser fails to read CSV
**Solution:** Ensure CSV is directly from IBKR without modifications

### Missing Transactions

**Problem:** Some transactions not appearing in reports
**Solution:** Check that CSV contains complete year data (January 1 - December 31)

### Incorrect Calculations

**Problem:** Tax amounts seem wrong
**Solution:** 
1. Verify FX rates are correct
2. Check that tax year matches statement period
3. Consult with tax advisor

### File Generation Issues

**Problem:** Reports not generated
**Solution:**
1. Check write permissions in output directory
2. Ensure all dependencies are installed
3. Review tax_filing.log for errors

## 📞 Support

For issues or questions:

1. Check the log file: `tax_filing.log`
2. Review this documentation
3. Verify with your tax advisor
4. Create an issue on GitHub

## ⚖️ Legal Disclaimer

⚠️ **IMPORTANT**: This tool is provided for informational purposes only and does not constitute tax advice.

- Always verify calculations with a certified tax advisor
- Basel-Landschaft tax rules may change
- Individual circumstances may require different treatment
- Use at your own risk

## 📚 Additional Resources

- [Basel-Landschaft Tax Authority](https://www.baselland.ch/politik-und-behorden/direktionen/finanz-und-kirchendirektion/steuerverwaltung)
- [Swiss Tax System Overview](https://www.ch.ch/en/taxes/)
- [IBKR Activity Statement Guide](https://www.interactivebrokers.com/)

## 📄 License

MIT License - Use at your own risk

## 🎖️ Version History

- **v2.0** (December 2025) - Complete tax filing system for Basel-Landschaft
  - Modular architecture (parser, calculator, reporter)
  - Three comprehensive output formats
  - Basel-Landschaft specific calculations
  - Foreign tax credit support

---

**Generated with ❤️ for Swiss Tax Filers**

*Last Updated: December 2025*
