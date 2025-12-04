#!/usr/bin/env python3
"""
Test script for Activity Statement Parser

Demonstracja funkcjonalności parsera z przykładami użycia
"""

from parser import ActivityStatementParser, ValidationError
import json


def test_basic_parsing():
    """Test podstawowego parsowania"""
    print("\n" + "=" * 80)
    print("TEST 1: Podstawowe parsowanie Activity Statement")
    print("=" * 80)
    
    parser = ActivityStatementParser('activity_statement.csv')
    data = parser.parse()
    
    print(f"\n✅ Sparsowano {len(data)} sekcji")
    
    for section_name, section_data in data.items():
        item_count = len(section_data.get('items', []))
        if item_count > 0:
            print(f"  • {section_name}: {item_count} elementów")


def test_validation():
    """Test walidacji danych"""
    print("\n" + "=" * 80)
    print("TEST 2: Walidacja danych")
    print("=" * 80)
    
    parser = ActivityStatementParser('activity_statement.csv')
    data = parser.parse()
    
    errors = [e for e in parser.validation_errors if e.severity == 'ERROR']
    warnings = [e for e in parser.validation_errors if e.severity == 'WARNING']
    
    print(f"\n📊 Wyniki walidacji:")
    print(f"  • Błędów (ERROR): {len(errors)}")
    print(f"  • Ostrzeżeń (WARNING): {len(warnings)}")
    
    if errors:
        print("\n❌ Błędy:")
        for error in errors:
            print(f"  {error}")
    
    if warnings:
        print("\n⚠️  Ostrzeżenia:")
        for warning in warnings:
            print(f"  {warning}")
    
    if not errors and not warnings:
        print("\n✅ Brak błędów i ostrzeżeń!")


def test_specific_sections():
    """Test konkretnych sekcji"""
    print("\n" + "=" * 80)
    print("TEST 3: Sprawdzenie konkretnych sekcji")
    print("=" * 80)
    
    parser = ActivityStatementParser('activity_statement.csv')
    data = parser.parse()
    
    # Test Trades
    if 'Trades' in data:
        trades = data['Trades']['items']
        print(f"\n📈 TRADES ({len(trades)} transakcji):")
        for i, trade in enumerate(trades[:3], 1):  # Pokaż pierwsze 3
            print(f"  {i}. {trade['symbol']} - {trade['quantity']} @ {trade['t_price']} "
                  f"({trade['date_time']})")
    
    # Test Dividends
    if 'Dividends' in data:
        dividends = data['Dividends']['items']
        total = sum(d['amount'] for d in dividends)
        print(f"\n💰 DIVIDENDS ({len(dividends)} wpłat, suma: {total}):")
        for i, div in enumerate(dividends[:3], 1):
            print(f"  {i}. {div['currency']} {div['amount']} - {div['date']}")
    
    # Test Open Positions
    if 'Open Positions' in data:
        positions = data['Open Positions']['items']
        print(f"\n📊 OPEN POSITIONS ({len(positions)} pozycji):")
        for i, pos in enumerate(positions, 1):
            print(f"  {i}. {pos['symbol']} - {pos['quantity']} units @ {pos['close_price']} "
                  f"(P/L: {pos['unrealized_pl']})")


def test_nav_consistency():
    """Test spójności Net Asset Value"""
    print("\n" + "=" * 80)
    print("TEST 4: Spójność Net Asset Value")
    print("=" * 80)
    
    parser = ActivityStatementParser('activity_statement.csv')
    data = parser.parse()
    
    if 'Net Asset Value' in data:
        nav = data['Net Asset Value']['items']
        print(f"\n💼 NET ASSET VALUE:")
        print(f"{'Asset Class':<15} {'Prior':>12} {'Change':>12} {'This Period':>12} {'Spójność':>10}")
        print("-" * 70)
        
        for item in nav:
            asset_class = item['asset_class']
            try:
                prior = float(item['prior_period'])
                change = float(item['change'])
                this_period = float(item['this_period'])
            except (ValueError, TypeError):
                # Skip items with invalid data
                continue
            
            expected = prior + change
            is_consistent = abs(expected - this_period) < 0.01
            status = "✅" if is_consistent else "❌"
            
            print(f"{asset_class:<15} {prior:>12.2f} {change:>12.2f} {this_period:>12.2f} {status:>10}")


def test_json_export():
    """Test eksportu do JSON"""
    print("\n" + "=" * 80)
    print("TEST 5: Export do JSON")
    print("=" * 80)
    
    parser = ActivityStatementParser('activity_statement.csv')
    data = parser.parse()
    
    output_file = 'test_output.json'
    parser.export_to_json(output_file)
    
    # Wczytaj i zweryfikuj
    with open(output_file, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)
    
    print(f"\n✅ Dane wyeksportowane do: {output_file}")
    print(f"  • Rozmiar pliku: {len(json.dumps(loaded_data))} bajtów")
    print(f"  • Sekcji: {len(loaded_data)}")
    
    # Pokaż fragment
    if 'Statement' in loaded_data:
        print(f"\n📋 Fragment (Statement Header):")
        for key, value in loaded_data['Statement'].items():
            if key and value:
                print(f"  • {key}: {value}")


def test_validation_report():
    """Test raportu walidacji"""
    print("\n" + "=" * 80)
    print("TEST 6: Generowanie raportu walidacji")
    print("=" * 80)
    
    parser = ActivityStatementParser('activity_statement.csv')
    data = parser.parse()
    
    report_file = 'test_validation_report.txt'
    parser.generate_validation_report(report_file)
    
    # Przeczytaj i wyświetl fragment
    with open(report_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"\n✅ Raport wygenerowany: {report_file}")
    print(f"  • Wierszy: {len(lines)}")
    print(f"\n📋 Fragment raportu (pierwsze 20 linii):")
    print("".join(lines[:20]))


def run_all_tests():
    """Uruchom wszystkie testy"""
    print("\n" + "=" * 80)
    print("🧪 URUCHAMIANIE TESTÓW PARSERA")
    print("=" * 80)
    
    try:
        test_basic_parsing()
        test_validation()
        test_specific_sections()
        test_nav_consistency()
        test_json_export()
        test_validation_report()
        
        print("\n" + "=" * 80)
        print("✅ WSZYSTKIE TESTY ZAKOŃCZONE POMYŚLNIE!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ BŁĄD: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    run_all_tests()
