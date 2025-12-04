#!/usr/bin/env python3
"""
Przykład użycia Activity Statement Parser

Ten skrypt pokazuje podstawowe użycie parsera do przetwarzania
plików Activity Statement z Interactive Brokers.
"""

from parser import ActivityStatementParser


def example_basic_usage():
    """Przykład 1: Podstawowe użycie"""
    print("\n" + "=" * 80)
    print("PRZYKŁAD 1: Podstawowe parsowanie")
    print("=" * 80 + "\n")
    
    # Utwórz parser
    parser = ActivityStatementParser('activity_statement.csv')
    
    # Parsuj dane
    data = parser.parse()
    
    # Wyświetl liczbę sparsowanych sekcji
    print(f"✅ Sparsowano {len(data)} sekcji\n")


def example_export_json():
    """Przykład 2: Export do JSON"""
    print("\n" + "=" * 80)
    print("PRZYKŁAD 2: Export danych do JSON")
    print("=" * 80 + "\n")
    
    parser = ActivityStatementParser('activity_statement.csv')
    data = parser.parse()
    
    # Eksportuj do JSON
    parser.export_to_json('moj_raport.json')
    print("✅ Dane wyeksportowane do: moj_raport.json\n")


def example_validation_report():
    """Przykład 3: Generowanie raportu walidacji"""
    print("\n" + "=" * 80)
    print("PRZYKŁAD 3: Raport walidacji")
    print("=" * 80 + "\n")
    
    parser = ActivityStatementParser('activity_statement.csv')
    data = parser.parse()
    
    # Generuj raport walidacji
    parser.generate_validation_report('moj_raport_walidacji.txt')
    print("✅ Raport walidacji zapisany do: moj_raport_walidacji.txt\n")


def example_access_data():
    """Przykład 4: Dostęp do sparsowanych danych"""
    print("\n" + "=" * 80)
    print("PRZYKŁAD 4: Dostęp do konkretnych danych")
    print("=" * 80 + "\n")
    
    parser = ActivityStatementParser('activity_statement.csv')
    data = parser.parse()
    
    # Dostęp do transakcji
    if 'Trades' in data:
        trades = data['Trades']['items']
        print(f"📊 Liczba transakcji: {len(trades)}")
        
        # Pierwsza transakcja
        if trades:
            first_trade = trades[0]
            print(f"\nPierwsza transakcja:")
            print(f"  Symbol: {first_trade['symbol']}")
            print(f"  Data: {first_trade['date_time']}")
            print(f"  Ilość: {first_trade['quantity']}")
            print(f"  Cena: {first_trade['t_price']}")
    
    # Dostęp do dywidend
    if 'Dividends' in data:
        dividends = data['Dividends']['items']
        total = sum(d['amount'] for d in dividends)
        print(f"\n💰 Liczba dywidend: {len(dividends)}")
        print(f"💰 Suma dywidend: {total}")
    
    print()


def example_check_validation():
    """Przykład 5: Sprawdzenie wyników walidacji"""
    print("\n" + "=" * 80)
    print("PRZYKŁAD 5: Sprawdzenie wyników walidacji")
    print("=" * 80 + "\n")
    
    parser = ActivityStatementParser('activity_statement.csv')
    data = parser.parse()
    
    # Sprawdź błędy
    errors = [e for e in parser.validation_errors if e.severity == 'ERROR']
    warnings = [e for e in parser.validation_errors if e.severity == 'WARNING']
    
    print(f"Błędów (ERROR): {len(errors)}")
    print(f"Ostrzeżeń (WARNING): {len(warnings)}")
    
    if errors:
        print("\n❌ BŁĘDY:")
        for error in errors:
            print(f"  {error}")
    
    if warnings:
        print("\n⚠️  OSTRZEŻENIA:")
        for warning in warnings:
            print(f"  {warning}")
    
    if not errors and not warnings:
        print("\n✅ Brak błędów i ostrzeżeń - dane są poprawne!")
    
    print()


def example_filter_data():
    """Przykład 6: Filtrowanie danych"""
    print("\n" + "=" * 80)
    print("PRZYKŁAD 6: Filtrowanie i analiza danych")
    print("=" * 80 + "\n")
    
    parser = ActivityStatementParser('activity_statement.csv')
    data = parser.parse()
    
    # Filtruj transakcje dla konkretnego symbolu
    if 'Trades' in data:
        trades = data['Trades']['items']
        aapl_trades = [t for t in trades if t['symbol'] == 'AAPL']
        
        print(f"📊 Transakcje AAPL: {len(aapl_trades)}")
        for trade in aapl_trades:
            print(f"  {trade['date_time']}: {trade['quantity']} @ {trade['t_price']}")
    
    # Oblicz sumę dywidend dla każdej waluty
    if 'Dividends' in data:
        dividends = data['Dividends']['items']
        currency_totals = {}
        
        for div in dividends:
            currency = div['currency']
            amount = float(div['amount'])
            currency_totals[currency] = currency_totals.get(currency, 0) + amount
        
        print(f"\n💰 Dywidendy per waluta:")
        for currency, total in currency_totals.items():
            print(f"  {currency}: {total:.2f}")
    
    print()


def main():
    """Uruchom wszystkie przykłady"""
    print("\n" + "=" * 80)
    print("📚 PRZYKŁADY UŻYCIA ACTIVITY STATEMENT PARSER")
    print("=" * 80)
    
    example_basic_usage()
    example_export_json()
    example_validation_report()
    example_access_data()
    example_check_validation()
    example_filter_data()
    
    print("\n" + "=" * 80)
    print("✅ WSZYSTKIE PRZYKŁADY WYKONANE")
    print("=" * 80)
    print("\n💡 Sprawdź wygenerowane pliki:")
    print("  - moj_raport.json")
    print("  - moj_raport_walidacji.txt\n")


if __name__ == '__main__':
    main()
