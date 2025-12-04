# IBKR Swiss Tax Processor - Basel-Landschaft

🇨🇭 **Complete Tax Filing Solution for Basel-Landschaft Canton**

Automated processing of IBKR Activity Statements with comprehensive tax report generation for Swiss tax filing.

## ✨ Features

✅ **Complete Tax Filing System**
- Parse IBKR Activity Statement CSV files
- Calculate taxes according to Basel-Landschaft rules
- Generate professional tax reports (Excel, PDF, Text)
- Automatic currency conversion to CHF
- Foreign tax credit calculation

✅ **Three Output Formats**
1. **Excel** (`Wertschriftenverzeichnis_BL_2025.xlsx`) - 7 detailed sheets
2. **PDF** (`Tax_Report_BL_2025.pdf`) - Professional A4 format
3. **Text** (`detailed_breakdown.txt`) - Complete transaction listing

✅ **Basel-Landschaft Compliance**
- Capital gains: Tax-free for private investors ✓
- Investment income: Fully taxable (10.55% rate)
- Wealth tax: 0.08% on assets > CHF 50,000
- Foreign tax credit support

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/matin-chuj/ibkr-swiss-tax-processor.git
cd ibkr-swiss-tax-processor

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Process your IBKR Activity Statement
python3 complete_tax_filing.py YOUR_IBKR_STATEMENT.csv

# With custom output directory
python3 complete_tax_filing.py YOUR_IBKR_STATEMENT.csv --year 2025 --output ./tax_reports
```

### Test with Sample Data

```bash
# Run with included sample data
python3 complete_tax_filing.py sample_activity_statement.csv --output ./output
```

## 📊 Generated Reports

### Excel Report (7 Sheets)
1. **Vermögensaufstellung** - Assets (stocks + cash)
2. **Einkünfte** - Income (dividends, interest, lending)
3. **Kapitalgewinne** - Capital gains (realized)
4. **Niezrealizowane** - Unrealized gains
5. **Koszty** - Expenses (commissions, fees)
6. **Forex** - Foreign exchange P/L
7. **Podsumowanie** - Tax summary

### PDF Report
- Professional A4 format
- Tax summary tables
- Assets and income breakdown
- Legal disclaimers

### Detailed Breakdown
- Transaction-by-transaction listing
- Step-by-step calculations
- Verification checksums

## 🧮 Tax Calculation

```
Taxable Income = Dividends + Interest + Lending - Expenses
Income Tax = Taxable Income × 10.55%

Taxable Wealth = Total Assets - CHF 50,000
Wealth Tax = Taxable Wealth × 0.08%

Total Tax = (Income Tax + Wealth Tax) - Foreign Tax Credit
```

## 📁 Project Structure

```
ibkr-swiss-tax-processor/
├── complete_tax_filing.py       # Main script
├── parser.py                    # CSV parser
├── tax_calculator_bl.py         # Tax calculator
├── report_generator_bl.py       # Report generator  
├── requirements.txt             # Dependencies
├── sample_activity_statement.csv # Test data
├── USAGE_GUIDE.md              # Detailed guide
└── README.md                    # This file
```

## 📖 Documentation

- **[USAGE_GUIDE.md](USAGE_GUIDE.md)** - Complete usage guide
- **[requirements.txt](requirements.txt)** - Python dependencies

## 🎯 Supported Features

### IBKR Data Sections
- ✅ Trades (stocks, options)
- ✅ Dividends (all currencies)
- ✅ Withholding taxes
- ✅ Interest income
- ✅ Fees and commissions
- ✅ Open positions
- ✅ Cash balances
- ✅ Forex transactions
- ✅ Securities lending

### Currencies
- CHF (Swiss Franc)
- EUR (Euro)
- USD (US Dollar)
- JPY (Japanese Yen)
- NOK (Norwegian Krone)
- PLN (Polish Złoty)
- SEK (Swedish Krona)

## ⚠️ Important Notes

### Tax-Free in Basel-Landschaft
✅ Capital gains (realized and unrealized)
✅ Forex gains/losses

### Fully Taxable
💰 Dividends
💰 Interest
💰 Securities lending income

### Deductible
✅ Trading commissions
✅ Market data fees
✅ Account fees

## 🔧 Requirements

- Python 3.8+
- pandas >= 2.0.0
- openpyxl >= 3.1.0
- reportlab >= 4.0.0
- numpy >= 1.24.0

## 🆘 Support & Troubleshooting

1. **Check the log file**: `tax_filing.log`
2. **Review documentation**: [USAGE_GUIDE.md](USAGE_GUIDE.md)
3. **Test with sample data**: `sample_activity_statement.csv`
4. **Consult tax advisor**: Always verify with professional

## ⚖️ Legal Disclaimer

⚠️ **This tool is for informational purposes only and does NOT constitute tax advice.**

- Always verify calculations with a certified tax advisor
- Basel-Landschaft tax rules may change
- Individual circumstances may require different treatment
- Use at your own risk

## 📞 Contact & Issues

- Create an issue on GitHub
- Review [USAGE_GUIDE.md](USAGE_GUIDE.md) for detailed help

## 📄 License

MIT License - See LICENSE file for details

## 🎖️ Version

**Version 2.0** - Complete Tax Filing System (December 2025)

---

**Made with ❤️ for Swiss Tax Filers in Basel-Landschaft**

*For tax year 2025 and beyond*
