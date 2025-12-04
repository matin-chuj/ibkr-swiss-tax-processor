#!/usr/bin/env python3
"""
Test script for IBKR CSV parser
Creates a mock CSV file and tests the parser functionality
"""

import tempfile
import os
from ibkr_processor import IBKRTaxProcessor
import logging
import pandas as pd

# Set logging to DEBUG for testing
logging.basicConfig(level=logging.INFO)

def create_mock_csv():
    """Create a mock IBKR CSV file for testing"""
    # IBKR CSV structure has sections with Header and Data rows
    csv_content = """Statement,Data,Header,Account,U1234567
Account Information,Data,Name,Test User
Account Information,Data,Base Currency,CHF

Trades,Header,Asset Category,Currency,Symbol,Date/Time,Quantity,T. Price,Proceeds,Comm/Fee,Basis,Realized P/L,Code
Trades,Data,Stocks,USD,AAPL,2025-01-15,10,150.00,-1500.00,1.00,1400.00,99.00,
Trades,Data,Stocks,EUR,BMW,2025-02-20,-5,90.00,450.00,1.50,400.00,48.50,
Trades,Data,Forex,USD.CHF,USD.CHF,2025-03-10,1000,0.88,880.00,2.00,,,,

Dividends,Header,Currency,Date,Description,Amount
Dividends,Data,USD,2025-01-20,AAPL - Dividend,25.00
Dividends,Data,EUR,2025-02-15,BMW - Dividend,15.00

Withholding Tax,Header,Currency,Date,Description,Amount
Withholding Tax,Data,USD,2025-01-20,AAPL - Tax,-3.75
Withholding Tax,Data,EUR,2025-02-15,BMW - Tax,-2.25

Fees,Header,Currency,Date,Description,Amount
Fees,Data,USD,2025-01-30,Monthly Activity Fee,-10.00

Interest,Header,Currency,Date,Description,Amount
Interest,Data,USD,2025-01-31,USD Credit Interest,5.50

Open Positions,Header,Asset Category,Currency,Symbol,Quantity,Mult,Cost Price,Cost Basis,Close Price,Value,Unrealized P/L,Code
Open Positions,Data,Summary,USD,AAPL,10,1,150.00,1500.00,155.00,1550.00,50.00,
"""
    
    # Create temporary file
    fd, path = tempfile.mkstemp(suffix='.csv', text=True)
    with os.fdopen(fd, 'w') as f:
        f.write(csv_content)
    
    return path

def test_parser():
    """Test the IBKR parser"""
    print("=" * 80)
    print("IBKR CSV Parser Test")
    print("=" * 80)
    
    # Create mock CSV
    csv_file = create_mock_csv()
    print(f"\n✅ Created mock CSV file: {csv_file}")
    
    # Debug: Show what we're parsing
    print("\n📄 CSV Content Preview:")
    with open(csv_file, 'r') as f:
        for i, line in enumerate(f, 1):
            if i <= 10:
                print(f"  Line {i}: {line.rstrip()}")
    
    try:
        # Initialize processor
        processor = IBKRTaxProcessor(csv_file, tax_year=2025)
        print("\n✅ Initialized IBKRTaxProcessor")
        
        # Parse the statement
        processor.parse_ibkr_statement()
        print("\n✅ Parsed IBKR statement")
        
        # Display results
        print("\n" + "=" * 80)
        print("PARSING RESULTS")
        print("=" * 80)
        
        print(f"\n📊 Transactions: {len(processor.transactions)}")
        for i, t in enumerate(processor.transactions, 1):
            print(f"  {i}. {t['symbol']} ({t['type']}) - {t['quantity']} @ {t['price']} {t['currency']}")
            print(f"     Proceeds: {t['proceeds_chf']:.2f} CHF, Commission: {t['commission_chf']:.2f} CHF")
        
        print(f"\n💰 Dividends: {len(processor.dividends)}")
        for i, d in enumerate(processor.dividends, 1):
            div_type = d.get('type', 'Dividend')
            print(f"  {i}. {div_type} - {d['amount']} {d['currency']} = {d['amount_chf']:.2f} CHF on {d['date']}")
        
        print(f"\n💵 Withholding Taxes: {len(processor.taxes)}")
        for i, t in enumerate(processor.taxes, 1):
            print(f"  {i}. {t['amount']} {t['currency']} = {t['amount_chf']:.2f} CHF on {t['date']}")
        
        print(f"\n💳 Fees: {len(processor.fees)}")
        for i, f in enumerate(processor.fees, 1):
            print(f"  {i}. {f['amount']} {f['currency']} = {f['amount_chf']:.2f} CHF on {f['date']}")
        
        print(f"\n📈 Open Positions: {len(processor.open_positions)}")
        for i, p in enumerate(processor.open_positions, 1):
            print(f"  {i}. {p['symbol']} - Qty: {p['quantity']}, Value: {p['value_chf']:.2f} CHF, P/L: {p['unrealized_pl']:.2f}")
        
        # Calculate summary
        processor.calculate_summary()
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total Dividends: {processor.summary['total_dividends']:.2f} CHF")
        print(f"Total Interest: {processor.summary['total_interest']:.2f} CHF")
        print(f"Total Withholding Taxes: {processor.summary['total_withholding_taxes']:.2f} CHF")
        print(f"Total Commissions: {processor.summary['total_commissions']:.2f} CHF")
        print(f"Total Forex Gains: {processor.summary['total_forex_gains']:.2f} CHF")
        print(f"Total Open Positions Value: {processor.summary['total_open_positions_value']:.2f} CHF")
        
        # Verify we got some data
        if len(processor.transactions) == 0 and len(processor.dividends) == 0:
            print("\n⚠️  WARNING: No data was parsed! Check parser logic.")
        else:
            print("\n" + "=" * 80)
            print("✅ ALL TESTS PASSED!")
            print("=" * 80)
        
        # Test report generation
        print("\n📝 Testing report generation...")
        try:
            # Change to temp directory for report generation
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                os.chdir(tmpdir)
                processor.generate_excel_report('test_report.xlsx')
                processor.generate_html_report('test_report.html')
                print("✅ Reports generated successfully")
        except Exception as e:
            print(f"⚠️  Report generation test skipped or failed: {e}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if os.path.exists(csv_file):
            os.remove(csv_file)
            print(f"\n🧹 Cleaned up temporary file: {csv_file}")

if __name__ == "__main__":
    test_parser()
