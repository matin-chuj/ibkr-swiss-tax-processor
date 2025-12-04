# IBKR CSV Parser - Technical Documentation

## Overview
The improved IBKR CSV parser handles the complex structure of Interactive Brokers Activity Statement CSV files with dynamic section detection and flexible column mapping.

## CSV Structure
IBKR CSV files have a specific structure:
```
Section Name,Header,Column1,Column2,...
Section Name,Data,Value1,Value2,...
Section Name,Data,Value1,Value2,...
```

Example:
```csv
Trades,Header,Asset Category,Currency,Symbol,Date/Time,Quantity,T. Price,Proceeds,Comm/Fee
Trades,Data,Stocks,USD,AAPL,2025-01-15,10,150.00,-1500.00,1.00
Trades,Data,Stocks,EUR,BMW,2025-02-20,-5,90.00,450.00,1.50
```

## Supported Sections
The parser recognizes and processes these sections:
- **Trades** - Stock, Forex, and Warrant transactions
- **Dividends** - Dividend income
- **Withholding Tax** - Taxes withheld at source
- **Fees** - Trading fees and monthly charges
- **Interest** - Interest income on cash balances
- **Open Positions** - Current holdings

## How It Works

### 1. CSV Reading
The parser reads CSV files with variable column counts per row using a custom reader that:
- Reads line by line
- Splits by comma
- Pads rows to equal length
- Handles empty values gracefully

### 2. Section Detection
For each row, the parser:
1. Checks if column 0 matches a known section name
2. If column 1 is "Header", stores the header row for column mapping
3. If column 1 is "Data", collects the data row for processing

### 3. Column Mapping
For each section, the parser attempts to:
1. **Dynamic mapping** - Find columns by name from header row (e.g., "Symbol", "Currency", "Amount")
2. **Fallback mapping** - Use hardcoded column positions if headers not found

Example column mapping for Trades:
```python
{
    'asset_type': find_column('Asset Category'),  # or fallback to index 2
    'currency': find_column('Currency'),           # or fallback to index 3
    'symbol': find_column('Symbol'),              # or fallback to index 4
    ...
}
```

### 4. Data Processing
Each section has a specialized processor that:
- Extracts values using column mapping
- Converts strings to appropriate types (float, date, etc.)
- Handles missing/invalid data gracefully
- Converts currencies to CHF using exchange rates
- Logs warnings for failed conversions

### 5. Value Conversion
The `_safe_float()` method handles various number formats:
- Removes whitespace
- Handles both comma (,) and dot (.) as decimal separators
- Checks for NaN and Infinity
- Returns 0.0 for invalid values with logging

## Error Handling

### CSV Reading Errors
- Invalid file path → FileNotFoundError with clear message
- Encoding issues → Fallback to different encodings
- Malformed CSV → Logs warnings, continues with valid rows

### Parsing Errors
- Missing columns → Uses fallback positions or skips row with warning
- Invalid data types → Returns default value (0.0 for numbers, empty string for text)
- Unknown sections → Ignored silently

### Data Validation
- NaN values → Converted to 0.0 or empty string
- Negative amounts → Absolute value taken where appropriate (fees, taxes)
- Missing currencies → Assumed to be CHF

## Logging

The parser provides three levels of logging:

**INFO** - High-level progress:
```
INFO: Loaded CSV with 150 rows
INFO: Processing section 'Trades' with 45 data rows
INFO: ✅ Sparsowano 45 transakcji
```

**DEBUG** - Detailed parsing information:
```
DEBUG: Found section: Trades
DEBUG: Stored header for Trades
DEBUG: Added data row to Trades
DEBUG: Trades column mapping: {'asset_type': 2, 'currency': 3, ...}
DEBUG: Added transaction: AAPL (Stocks) on 2025-01-15
```

**WARNING** - Issues encountered:
```
WARNING: Failed to convert value to float: invalid literal - ValueError
WARNING: Failed to process trade row: IndexError
```

## Testing

Run the test script to validate the parser:
```bash
python3 test_parser.py
```

The test creates a mock IBKR CSV and verifies:
- ✅ All sections are detected
- ✅ Headers are parsed correctly
- ✅ Data rows are collected and processed
- ✅ Values are converted to correct types
- ✅ Currency conversions work
- ✅ Reports are generated

## Customization

### Adding Exchange Rates
Update the `fx_rates` dictionary in `__init__`:
```python
self.fx_rates = {
    'EUR': 0.93324,
    'USD': 0.79959,
    'GBP': 1.12500,  # Add new currency
    ...
}
```

### Supporting New Sections
1. Add section name to detection list in `parse_ibkr_statement()`
2. Create processor method: `_process_SECTION_NAME_improved()`
3. Add column mapping for the section
4. Extract and store data in appropriate container

### Modifying Column Mapping
Edit the `col_map` dictionary in each `_process_*_improved()` method:
```python
col_map = {
    'symbol': self._get_column_index(headers, 'Symbol'),
    'new_field': self._get_column_index(headers, 'New Field Name'),
}
```

## Troubleshooting

### No data parsed
- **Check:** CSV file format matches IBKR structure
- **Enable:** DEBUG logging to see what's happening
- **Verify:** Section names match exactly (case-sensitive)

### Wrong values
- **Check:** Column mapping is finding correct columns
- **Enable:** DEBUG logging to see column indices
- **Verify:** Exchange rates are up-to-date

### Encoding errors
- **Solution:** Ensure CSV is UTF-8 encoded
- **Alternative:** Try opening CSV and re-saving as UTF-8

### Missing transactions
- **Check:** Section name matches exactly ("Trades" not "Trade")
- **Verify:** Rows have "Data" in column 1
- **Review:** Logs for skipped rows

## Performance

The parser is optimized for typical IBKR statements:
- **Small files** (<100 KB, <1000 rows): <1 second
- **Medium files** (100-500 KB, 1000-5000 rows): 1-3 seconds
- **Large files** (>500 KB, >5000 rows): 3-10 seconds

Memory usage is proportional to file size, typically <50 MB for most statements.
