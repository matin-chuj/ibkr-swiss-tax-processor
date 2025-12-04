# Changelog - IBKR CSV Parser Improvements

## Version 2.0 - December 2025

### 🔧 Major Fixes

#### Syntax Errors Corrected
Fixed all spacing errors in the codebase that caused Python syntax errors:
- `pd. DataFrame` → `pd.DataFrame`
- `row. tolist()` → `row.tolist()`
- `1. 0` → `1.0`
- `self. transactions` → `self.transactions`
- `d. get` → `d.get`
- And 15+ other similar corrections throughout the code

#### CSV Parser Completely Rewritten
**Problem**: The original parser used hardcoded column indices and couldn't handle the real IBKR CSV structure with multi-row headers and variable columns.

**Solution**: Implemented a dynamic parser that:
- Detects sections by name (Trades, Dividends, etc.)
- Extracts header rows (with "Header" marker)
- Maps columns dynamically by name
- Falls back to hardcoded indices if headers unavailable
- Handles variable column counts per row

**Before**:
```python
# Hardcoded positions - breaks if CSV format changes
symbol = row[4]
currency = row[3]
```

**After**:
```python
# Dynamic column mapping with fallback
col_map = {
    'symbol': self._get_column_index(headers, 'Symbol') or 4,
    'currency': self._get_column_index(headers, 'Currency') or 3,
}
symbol = row[col_map['symbol']]
```

### 🚀 New Features

#### Logging System
Added comprehensive logging throughout the parser:
- **INFO level**: Progress and summary information
- **DEBUG level**: Detailed parsing steps for troubleshooting
- **WARNING level**: Non-fatal issues (failed conversions, skipped rows)

```python
logging.info(f"Processing section 'Trades' with {len(rows)} data rows")
logging.debug(f"Added transaction: {symbol} on {date}")
logging.warning(f"Failed to convert value: {value}")
```

#### Enhanced Error Handling
Improved `_safe_float()` method:
- Handles NaN and Infinity values
- Supports both comma and dot as decimal separators
- Handles thousands separators
- Returns 0.0 with warning instead of crashing

```python
# Handles: "1,234.56", "1.234,56", "1 234.56", etc.
def _safe_float(self, value) -> float:
    # Remove whitespace, handle separators
    # Check for NaN/Inf
    # Log warnings for invalid values
    # Return 0.0 as safe default
```

#### Test Suite
Created comprehensive test script (`test_parser.py`):
- Generates mock IBKR CSV data
- Tests all parsing functions
- Validates data extraction and conversion
- Tests report generation
- Provides clear pass/fail output

### 📦 Dependencies

Updated `requirements.txt`:
- Changed from exact versions (`==`) to minimum versions (`>=`)
- Ensures compatibility with newer package versions
- Fixed `openpyxl` version issue

**Before**:
```
pandas==2.0.3
openpyxl==3.10.10  # This version doesn't exist!
```

**After**:
```
pandas>=2.0.3
openpyxl>=3.1.0
```

### 🔒 Security

Added `.gitignore` to protect sensitive data:
- Excludes CSV files (may contain personal financial data)
- Excludes generated reports
- Excludes Python cache and build artifacts

### 📊 Improved Sections Processing

#### Trades Section
- Supports Stocks, Forex, and Warrants
- Dynamic column detection for all fields
- Proper handling of commissions and fees
- Currency conversion to CHF

#### Dividends Section
- Separates dividends from interest
- Tracks withholding taxes
- Multi-currency support

#### Open Positions Section
- Extracts current holdings
- Includes unrealized P/L
- Values in CHF

### 🐛 Bug Fixes

1. **CSV Reading**: Fixed variable column count handling
   - Was: Crashed on rows with different column counts
   - Now: Pads rows to equal length, processes all rows

2. **Section Detection**: Fixed logic for Header/Data rows
   - Was: Skipped Data rows because continued after finding section
   - Now: Checks for both Header and Data in same conditional block

3. **Column Mapping**: Fixed fallback logic
   - Was: Failed silently when column not found
   - Now: Uses fallback index and logs warning

4. **Number Parsing**: Fixed decimal separator handling
   - Was: Only supported dot (.) as decimal
   - Now: Supports comma (,) and dot (.), handles thousands separators

### 📝 Documentation

Added comprehensive documentation:
- `PARSER_DOCUMENTATION.md`: Technical details of parser implementation
- `README.md`: Updated with correct version numbers
- Inline code comments explaining complex logic
- Docstrings for all methods

### 🧪 Testing Results

Test script validates:
- ✅ 3 transactions parsed correctly
- ✅ 3 dividend/interest entries
- ✅ 2 withholding tax entries
- ✅ 1 fee entry
- ✅ 1 open position
- ✅ Currency conversions accurate
- ✅ Excel report generation
- ✅ HTML report generation

### 🔄 Backward Compatibility

The improved parser maintains backward compatibility:
- All existing report methods work unchanged
- Excel and HTML output format unchanged
- Public API unchanged (process(), generate_excel_report(), etc.)
- Can still use old-style CSV if needed (fallback to hardcoded indices)

### 💡 Future Improvements

Potential enhancements for future versions:
- [ ] Add support for Options trading
- [ ] Implement cost basis tracking
- [ ] Add tax-loss harvesting analysis
- [ ] Support for multiple accounts
- [ ] Real-time exchange rate fetching from APIs
- [ ] PDF report generation
- [ ] Interactive web dashboard

### 📞 Support

For issues or questions:
- Create an issue on GitHub
- Check `PARSER_DOCUMENTATION.md` for technical details
- Run `test_parser.py` to validate your setup
- Enable DEBUG logging to troubleshoot parsing issues

---

**Migration Guide**: No changes needed - the improved parser is a drop-in replacement. Just update your code and run as before. The parser will automatically use dynamic column detection if available, with fallback to the old hardcoded positions for compatibility.
