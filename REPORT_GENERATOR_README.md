# Basel-Landschaft Tax Report Generator - Documentation

## 📋 Overview

This comprehensive tax report generator creates **Wertschriftenverzeichnis** (securities register) and tax reports for the Canton of Basel-Landschaft (BL), Switzerland. It processes IBKR (Interactive Brokers) Activity Statements and generates reports in three formats: **Excel**, **PDF**, and **JSON**.

## 🎯 Features

### Tax Calculations
- ✅ **Vermögenssteuer** (Wealth tax) - 0.08%
- ✅ **Einkommenssteuer** (Income tax) - 10.55%
- ✅ Foreign tax credit (US withholding tax)
- ✅ Minimum taxable threshold (CHF 50)
- ✅ Multi-currency support with automatic CHF conversion

### Report Sections
1. **Vermögensaufstellung** (Asset Position as of December 31, 2025)
   - Swiss stocks
   - Foreign stocks
   - Bonds and securities
   - Funds
   - Cash (CHF)
   - Foreign currencies
   
2. **Einkünfte aus Vermögen** (Income from Assets)
   - Swiss dividends
   - Foreign dividends
   - Withholding taxes by country
   - Interest income
   - Securities lending income
   
3. **Kapitalgewinne/Verluste** (Capital Gains/Losses)
   - Realized gains
   - Realized losses
   - Net position
   - *Note: Private capital gains are tax-free in BL*
   
4. **Kosten und Abzüge** (Costs and Deductions)
   - Transaction fees
   - Account fees
   - Other deductible costs
   
5. **Devisenverluste** (Foreign Exchange Gains/Losses)
   - FX gains
   - FX losses
   - Net FX result

### Output Formats

#### 1. Excel (.xlsx) - `Wertschriftenverzeichnis_BL_2025.xlsx`
- Multiple sheets for each section
- Professional formatting with Basel-Landschaft colors
- Currency formatting (CHF, USD, EUR, etc.)
- Summary sheet with tax calculations
- Auto-adjusted column widths

#### 2. PDF (.pdf) - `Tax_Report_BL_2025.pdf`
- Professional layout on A4 paper
- Personal data placeholder section
- All tax report sections
- Tax summary with calculations
- Signature placeholder
- Print-ready format

#### 3. JSON (.json) - `Tax_Summary_BL_2025.json`
- Structured data for further processing
- Complete metadata
- All sections in machine-readable format
- Detailed transaction summaries

## 📦 Installation

### Requirements
```bash
Python 3.8+
pandas >= 2.0.0
openpyxl >= 3.1.0
numpy >= 1.24.0
requests >= 2.31.0
reportlab >= 4.0.0
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

## 🚀 Quick Start

### Option 1: With IBKR CSV File

```python
from ibkr_processor import IBKRTaxProcessor
from report_generator_bl import ReportGeneratorBL

# Parse IBKR statement
processor = IBKRTaxProcessor('your_statement.csv', tax_year=2025)
processor.parse_ibkr_statement()

# Prepare data
parsed_data = {
    'transactions': processor.transactions,
    'dividends': processor.dividends,
    'taxes': processor.taxes,
    'fees': processor.fees,
    'open_positions': processor.open_positions
}

# Generate all reports
generator = ReportGeneratorBL(parsed_data)
reports = generator.generate_all_reports('output')

print(f"Reports generated:")
for format_type, path in reports.items():
    print(f"  {format_type}: {path}")
```

### Option 2: With Pre-parsed Data

```python
from report_generator_bl import ReportGeneratorBL

# Your parsed data
data = {
    'transactions': [...],
    'dividends': [...],
    'taxes': [...],
    'fees': [...],
    'open_positions': [...]
}

# Generate reports
generator = ReportGeneratorBL(data)
reports = generator.generate_all_reports()
```

### Option 3: Run Example Script

```bash
# With sample data
python example_bl_report.py

# With your CSV file
python example_bl_report.py path/to/your/statement.csv
```

## 📊 Data Structure

### Input Data Format

```python
{
    'transactions': [
        {
            'type': 'Stocks',        # or 'Forex'
            'symbol': 'AAPL',
            'date': '2025-03-15',
            'quantity': 10,
            'price': 150.00,
            'proceeds_chf': 1195.14,
            'commission_chf': 4.86,
            'currency': 'USD'
        }
    ],
    'dividends': [
        {
            'symbol': 'AAPL',
            'date': '2025-02-15',
            'currency': 'USD',
            'amount': 24.00,
            'amount_chf': 19.19,
            'type': 'Dividend'  # or 'Interest'
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
        }
    ]
}
```

## ⚙️ Configuration

### Basel-Landschaft Tax Configuration

Edit `basellandschaft_config.json` to customize:

```json
{
  "tax_rates": {
    "income_tax_rate": 0.1055,     # 10.55%
    "wealth_tax_rate": 0.0008,     # 0.08%
    "minimum_taxable_threshold": 50.0
  },
  "currency_rates": {
    "reference_date": "2025-12-31",
    "rates": {
      "EUR": 0.93324,
      "USD": 0.79959,
      "JPY": 0.0051507,
      ...
    }
  }
}
```

### Currency Rates

Update exchange rates for the reference date (December 31, 2025):
- Rates can be obtained from Swiss National Bank (SNB)
- ECB or other reliable sources
- Or use the rates embedded in your IBKR statement

## 🧮 Tax Calculations

### Wealth Tax (Vermögenssteuer)
```
Wealth Tax = Total Assets (CHF) × 0.0008
Exemption: Assets < CHF 50
```

### Income Tax (Einkommenssteuer)
```
Taxable Income = Gross Income - Deductible Costs
Income Tax = Taxable Income × 0.1055
Exemption: Income < CHF 50
```

### Foreign Tax Credit
```
Creditable Amount = (US Taxes × 100%) + (Other Taxes × 80%)
```

### Net Tax Liability
```
Net Tax = (Wealth Tax + Income Tax) - Foreign Tax Credit
```

## 📝 Usage Examples

### Example 1: Complete Workflow

```python
from ibkr_processor import IBKRTaxProcessor
from report_generator_bl import ReportGeneratorBL
from pathlib import Path

# Step 1: Parse IBKR CSV
processor = IBKRTaxProcessor('statement_2025.csv', tax_year=2025)
processor.parse_ibkr_statement()

# Step 2: Create report generator
parsed_data = {
    'transactions': processor.transactions,
    'dividends': processor.dividends,
    'taxes': processor.taxes,
    'fees': processor.fees,
    'open_positions': processor.open_positions
}

generator = ReportGeneratorBL(parsed_data)

# Step 3: Generate all reports
output_dir = Path('tax_reports_2025')
output_dir.mkdir(exist_ok=True)

reports = generator.generate_all_reports(str(output_dir))

# Step 4: Access tax summary
summary = generator.tax_summary
print(f"Net Tax Liability: CHF {summary['tax_liability']['net_tax_liability']:.2f}")
```

### Example 2: Generate Individual Reports

```python
from report_generator_bl import ReportGeneratorBL

# Initialize with data
generator = ReportGeneratorBL(your_data)

# Generate only Excel
generator.generate_excel_report('my_report.xlsx')

# Generate only PDF
generator.generate_pdf_report('my_report.pdf')

# Generate only JSON
generator.generate_json_report('my_report.json')
```

### Example 3: Access Tax Calculator Directly

```python
from tax_calculator_bl import TaxCalculatorBL

calculator = TaxCalculatorBL()

# Calculate wealth tax
wealth_tax = calculator.calculate_wealth_tax(10000)
print(f"Wealth tax: CHF {wealth_tax['wealth_tax']:.2f}")

# Calculate income tax
income_tax = calculator.calculate_income_tax(5000, 500)
print(f"Income tax: CHF {income_tax['income_tax']:.2f}")

# Calculate foreign tax credit
credit = calculator.calculate_foreign_tax_credit({'US': 100, 'UK': 50})
print(f"Creditable: CHF {credit['creditable_amount']:.2f}")
```

## 🧪 Testing

### Run All Tests
```bash
python test_report_generator.py
```

### Test Coverage
- Tax calculator functions
- Report generation (Excel, PDF, JSON)
- Configuration loading
- Edge cases (empty data, zero values, etc.)

### Example Test Output
```
test_wealth_tax_calculation ... ok
test_income_tax_calculation ... ok
test_foreign_tax_credit ... ok
test_excel_report_generation ... ok
test_pdf_report_generation ... ok
test_json_report_generation ... ok
...
Ran 18 tests in 0.050s
OK
```

## 📂 Project Structure

```
ibkr-swiss-tax-processor/
├── basellandschaft_config.json      # BL tax configuration
├── tax_calculator_bl.py             # Tax calculator for BL
├── report_generator_bl.py           # Report generator (Excel/PDF/JSON)
├── test_report_generator.py         # Unit tests
├── example_bl_report.py             # Example usage script
├── ibkr_processor.py                # IBKR CSV parser
├── requirements.txt                 # Python dependencies
├── README.md                        # Main documentation
└── REPORT_GENERATOR_README.md       # This file
```

## ⚠️ Important Notes

### Tax Treatment in Basel-Landschaft
1. **Capital Gains**: Private capital gains from securities are **TAX-FREE** in BL
2. **Dividends**: Subject to income tax (10.55%)
3. **Interest**: Subject to income tax (10.55%)
4. **Wealth**: All securities subject to wealth tax (0.08%)
5. **Foreign Taxes**: US withholding tax is fully creditable

### Disclaimers
⚠️ **This tool is for informational purposes only**
- Always verify calculations with a qualified tax advisor
- Tax laws may change
- Individual circumstances may require special treatment
- The tool does not constitute tax advice

### Data Privacy
- All processing is done locally
- No data is sent to external servers
- Reports contain sensitive financial information - handle securely

## 🔧 Troubleshooting

### Common Issues

**Problem**: Missing dependencies
```bash
# Solution
pip install -r requirements.txt
```

**Problem**: Currency conversion errors
```bash
# Solution: Update exchange rates in basellandschaft_config.json
```

**Problem**: PDF generation fails
```bash
# Solution: Ensure reportlab is installed
pip install reportlab
```

**Problem**: Excel file won't open
```bash
# Solution: Check that openpyxl is installed correctly
pip install --upgrade openpyxl
```

## 🚀 Advanced Usage

### Custom Tax Rates

```python
from tax_calculator_bl import TaxCalculatorBL

# Override config
calculator = TaxCalculatorBL('custom_config.json')

# Or modify rates programmatically
calculator.income_tax_rate = 0.12  # 12%
calculator.wealth_tax_rate = 0.001  # 0.1%
```

### Custom Currency Rates

```python
# Update rates in generator
generator = ReportGeneratorBL(data)
generator.tax_calculator.fx_rates['GBP'] = 1.10  # Add GBP rate
```

### Filter Data Before Reporting

```python
# Only report specific symbols
filtered_data = {
    'transactions': [t for t in data['transactions'] if t['symbol'] in ['AAPL', 'MSFT']],
    'dividends': data['dividends'],
    # ... other fields
}

generator = ReportGeneratorBL(filtered_data)
```

## 📞 Support & Contributing

### Getting Help
- Review this documentation
- Check `example_bl_report.py` for usage examples
- Run tests to verify installation
- Create an issue on GitHub

### Contributing
Contributions welcome! Areas for improvement:
- Additional canton support
- Enhanced currency conversion (API integration)
- More sophisticated asset categorization
- Additional export formats
- Improved UI/visualization

## 📄 License

MIT License - Use at your own risk

## 🏛️ Legal & Compliance

**Tax Year**: 2025  
**Canton**: Basel-Landschaft (BL)  
**Country**: Switzerland  

**Compliance Notes**:
- Reports follow Basel-Landschaft Wertschriftenverzeichnis format
- Tax rates current as of 2025
- Exchange rates as of December 31, 2025
- Always consult with Steueramt Basel-Landschaft for official requirements

---

**Version**: 1.0.0  
**Last Updated**: December 2025  
**Compatibility**: Python 3.8+

For the main project documentation, see [README.md](README.md)
