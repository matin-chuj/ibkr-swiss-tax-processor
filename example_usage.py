"""
Example usage of IBKR Activity Statement Parser

This script demonstrates how to use the parser to extract data from IBKR CSV files.
"""

import json
from parser import IBKRActivityStatementParser, parse_ibkr_activity_statement


def example_basic_usage():
    """Basic usage example"""
    print("=" * 80)
    print("BASIC USAGE EXAMPLE")
    print("=" * 80)
    
    # Parse a CSV file using the convenience function
    csv_file = "activity_statement.csv"
    
    # Note: This will fail if the file doesn't exist
    # In production, you would use a real file path
    try:
        data = parse_ibkr_activity_statement(csv_file)
        
        # Print summary
        print("\n📊 PARSED DATA SUMMARY:")
        print(f"  Account ID: {data['account_info'].get('account_id', 'N/A')}")
        print(f"  Base Currency: {data['account_info'].get('base_currency', 'N/A')}")
        print(f"  Period: {data['account_info'].get('period', 'N/A')}")
        print(f"\n  Transactions: {len(data['transactions'])}")
        print(f"  Dividends: {len(data['dividends'])}")
        print(f"  Taxes: {len(data['taxes'])}")
        print(f"  Fees: {len(data['fees'])}")
        print(f"  Interest: {len(data['interest'])}")
        print(f"  Open Positions: {len(data['open_positions'])}")
        print(f"  Forex Balances: {len(data['forex_balances'])}")
        
    except FileNotFoundError:
        print(f"  ⚠️  File not found: {csv_file}")
        print("  Please provide a valid IBKR Activity Statement CSV file.")


def example_advanced_usage():
    """Advanced usage example with custom processing"""
    print("\n" + "=" * 80)
    print("ADVANCED USAGE EXAMPLE")
    print("=" * 80)
    
    csv_file = "activity_statement.csv"
    
    try:
        # Create parser instance for more control
        parser = IBKRActivityStatementParser(csv_file)
        
        # Parse the file
        data = parser.parse()
        
        # Access specific data sections
        print("\n📈 TRANSACTIONS:")
        for tx in data['transactions'][:5]:  # Show first 5
            print(f"  {tx.get('date', 'N/A'):12} {tx.get('symbol', 'N/A'):8} "
                  f"{tx.get('quantity', 0):8.2f} @ {tx.get('price', 0):8.2f} "
                  f"{tx.get('currency', 'N/A')}")
        
        print("\n💰 DIVIDENDS:")
        for div in data['dividends'][:5]:  # Show first 5
            print(f"  {div.get('date', 'N/A'):12} {div.get('symbol', 'N/A'):8} "
                  f"{div.get('amount', 0):10.2f} {div.get('currency', 'N/A')}")
        
        print("\n🏛️  WITHHOLDING TAXES:")
        for tax in data['taxes'][:5]:  # Show first 5
            print(f"  {tax.get('date', 'N/A'):12} {tax.get('symbol', 'N/A'):8} "
                  f"{tax.get('amount', 0):10.2f} {tax.get('currency', 'N/A')} "
                  f"({tax.get('country', 'N/A')})")
        
        # Export to JSON
        json_output = parser.to_json()
        print(f"\n📄 JSON export available ({len(json_output)} characters)")
        
        # Save to file
        with open('parsed_data.json', 'w', encoding='utf-8') as f:
            f.write(json_output)
        print("  ✅ Saved to parsed_data.json")
        
    except FileNotFoundError:
        print(f"  ⚠️  File not found: {csv_file}")
        print("  Please provide a valid IBKR Activity Statement CSV file.")


def example_data_validation():
    """Example showing data validation features"""
    print("\n" + "=" * 80)
    print("DATA VALIDATION EXAMPLE")
    print("=" * 80)
    
    # Create a temporary parser for testing validation functions
    parser = IBKRActivityStatementParser("dummy.csv")
    
    # Test date parsing
    print("\n📅 DATE PARSING:")
    test_dates = [
        "2025-12-03",
        "03.12.2025",
        "03/12/2025",
        "2025-12-03, 14:30:00",
        "invalid_date"
    ]
    
    for date_str in test_dates:
        parsed = parser._parse_date(date_str)
        status = "✅" if parsed else "❌"
        print(f"  {status} '{date_str}' → {parsed}")
    
    # Test amount parsing
    print("\n💵 AMOUNT PARSING:")
    test_amounts = [
        "1000.50",
        "1,000.50",
        "1,234,567.89",
        "-500.25",
        "(1000.00)",
        "$1,500.00",
        "€250.50",
        "invalid"
    ]
    
    for amount_str in test_amounts:
        parsed = parser._parse_amount(amount_str)
        status = "✅" if parsed != 0.0 or amount_str == "0" else "❌"
        print(f"  {status} '{amount_str}' → {parsed:.2f}")


def example_multi_currency():
    """Example showing multi-currency support"""
    print("\n" + "=" * 80)
    print("MULTI-CURRENCY SUPPORT")
    print("=" * 80)
    
    print("\n💱 SUPPORTED CURRENCIES:")
    currencies = IBKRActivityStatementParser.SUPPORTED_CURRENCIES
    print(f"  {', '.join(currencies)}")
    
    print("\n  The parser automatically handles:")
    print("  ✓ Multi-currency transactions")
    print("  ✓ Multi-currency dividends")
    print("  ✓ Multi-currency interest")
    print("  ✓ Multi-currency fees")
    print("  ✓ Forex balances in Cash Report")


def main():
    """Run all examples"""
    print("\n" + "🚀 " * 20)
    print("IBKR ACTIVITY STATEMENT PARSER - EXAMPLES")
    print("🚀 " * 20)
    
    example_basic_usage()
    example_advanced_usage()
    example_data_validation()
    example_multi_currency()
    
    print("\n" + "=" * 80)
    print("EXAMPLES COMPLETED")
    print("=" * 80)
    print("\n💡 TIP: To use this parser with your own data:")
    print("   1. Export Activity Statement from IBKR as CSV")
    print("   2. Update the csv_file path in the examples above")
    print("   3. Run: python example_usage.py")
    print("\n📚 For more information, see the README.md file")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
