# IBKR Swiss Tax Processor - Basel-Landschaft

🇨🇭 Narzędzie do przetwarzania raportów IBKR Activity Statement i generowania raportów podatkowych dla kantonu Basel-Landschaft. 

## Funcje

✅ **Parsowanie CSV z IBKR** - Automatyczne czytanie i strukturyzowanie danych
✅ **Konwersja walut** - Obsługa EUR, USD, JPY, NOK, PLN, SEK → CHF
✅ **Kategoryzacja podatkowa** - Zgodnie z wymogami Basel-Landschaft
✅ **Excel Report** - Siedem arkuszy ze szczegółami
✅ **HTML Preview** - Interaktywny podgląd raportów
✅ **Polskie tłumaczenie** - Wszystkie nazwy w języku polskim

## Wymagania

- Python 3. 8+
- pandas
- openpyxl
- requests

## Instalacja

```bash
pip install -r requirements.txt
```

## Użycie

### Podstawowe użycie

```python
from ibkr_processor import IBKRTaxProcessor

# Inicjalizacja
processor = IBKRTaxProcessor(
    'U11673931_20250101_20251203.csv',
    tax_year=2025
)

# Przetworzenie i generowanie raportów
processor.process()
```

### Output

Proces generuje dwa pliki:

1. **tax_report_2025.xlsx** - Plik Excel z siedmioma arkuszami:
   - 📊 PODSUMOWANIE - Przegląd roczny
   - 📈 TRANSAKCJE_SZCZEGÓŁOWE - Wszystkie transakcje akcji
   - 💱 FOREX - Konwersje walut i zyski
   - 💰 DYWIDENDY - Dochód z dywidend
   - 📍 ODSETKI - Odsetki od depozytów
   - 🎯 POZYCJE_OTWARTE - Aktualne holdingi
   - 💳 KOSZTY - Prowizje i opłaty

2. **tax_report_2025.html** - Interaktywny podgląd w przeglądarce

## Struktura danych

### Summary (Podsumowanie)
```
Dywidendy (brutto)      → CHF
Odsetki                 → CHF
Zyski z Forex           → CHF
Koszty (prowizje)       → CHF
Podatki u źródła        → CHF
Pozycje otwarte         → CHF
```

### Transakcje
```
Data | Symbol | Typ | Ilość | Cena | Wartość CHF | Komisja CHF
```

### Dywidendy
```
Data | Waluta | Kwota | Kwota CHF | Podatek u źródła
```

## Basel-Landschaft - Wymogi podatkowe

Canton Basel-Landschaft wymaga:

✓ Separacji zysków krótko- i długoterminowych
✓ Raportowania dochodów z lokat (dywidendy, odsetki)
✓ Raportowania podatków u źródła per kraj
✓ Deklaracji kosztów handlowych (prowizje, opłaty)
✓ Konwersji wszystkich walut na CHF

## Kursy walut

Domyślnie używane kursy z raportu IBKR (stan: 3 grudnia 2025):

```
EUR/CHF: 0.93324
USD/CHF: 0.79959
JPY/CHF: 0.0051507
NOK/CHF: 0.07952
PLN/CHF: 0. 22084
SEK/CHF: 0.085358
```

Kursy mogą być aktualizowane w kodzie lub zaciągane z API SNB/ECB.

## Obsługiwane waluty

- EUR (Euro)
- USD (Dolar ameryski)
- JPY (Jen japoński)
- NOK (Korona norweska)
- PLN (Złoty polski)
- SEK (Korona szwedzka)
- CHF (Frank szwajcarski - waluta bazowa)

## Rozwiązywanie problemów

### Problem: "Module not found: pandas"
**Rozwiązanie:** `pip install -r requirements.txt`

### Problem: Błędy przy parsowaniu CSV
**Rozwiązanie:** Upewnij się, że plik CSV pochodzi bezpośrednio z IBKR, bez edycji

### Problem: Kursy walut niezgodne
**Rozwiązanie:** Zmodyfikuj słownik `self.fx_rates` w klasie `IBKRTaxProcessor`

## Struktura projektu

```
ibkr-swiss-tax-processor/
├── parser.py               # Moduł parsera CSV Activity Statement
├── ibkr_processor.py       # Główna klasa procesora podatkowego
├── test_parser.py          # Testy jednostkowe parsera
├── example_usage.py        # Przykłady użycia parsera
├── requirements.txt        # Zależności Python
├── README.md               # Dokumentacja
└── examples/
    └── sample_report/
        ├── tax_report_2025.xlsx
        └── tax_report_2025.html
```

## Parser Activity Statement (parser.py)

Nowy moduł `parser.py` zapewnia szczegółowe parsowanie plików CSV z IBKR Activity Statement.

### Funkcjonalność parsera:

✅ **Ekstrakcja danych konta:**
- Numer konta i typ
- Waluta bazowa
- Okres raportowania
- Nazwa brokera

✅ **Net Asset Value (NAV):**
- Wartość początkowa i końcowa
- Obsługa multi-walut

✅ **Transakcje:**
- Akcje (Stocks)
- Forex
- Forex conversions
- Szczegóły: data, symbol, ilość, cena, prowizje

✅ **Dywidendy:**
- Multi-walutowe (USD, EUR, NOK, PLN, CHF, SEK, JPY, GBP, CAD, AUD)
- Data, kwota, symbol

✅ **Podatki u źródła:**
- Według kraju
- Multi-walutowe
- Przypisanie do transakcji

✅ **Odsetki:**
- Multi-walutowe
- Credit interest

✅ **Opłaty i prowizje:**
- Activity fees
- Market data fees
- Prowizje transakcyjne

✅ **Pozycje otwarte:**
- Aktualne holdingi
- Wartości rynkowe
- Niezrealizowane zyski/straty

✅ **Securities Lending:**
- Opłaty za pożyczanie papierów wartościowych

✅ **Salda walutowe:**
- Cash Report
- Początkowe i końcowe salda

### Użycie parsera:

#### Podstawowe użycie:

```python
from parser import parse_ibkr_activity_statement

# Parsowanie pliku CSV
data = parse_ibkr_activity_statement('activity_statement.csv')

# Dostęp do danych
print(f"Konto: {data['account_info']['account_id']}")
print(f"Waluta bazowa: {data['account_info']['base_currency']}")
print(f"Liczba transakcji: {len(data['transactions'])}")
print(f"Liczba dywidend: {len(data['dividends'])}")
```

#### Zaawansowane użycie:

```python
from parser import IBKRActivityStatementParser

# Tworzenie instancji parsera
parser = IBKRActivityStatementParser('activity_statement.csv')

# Parsowanie
result = parser.parse()

# Przetwarzanie transakcji
for tx in result['transactions']:
    print(f"{tx['date']} {tx['symbol']} {tx['quantity']} @ {tx['price']}")

# Export do JSON
json_data = parser.to_json()
with open('output.json', 'w') as f:
    f.write(json_data)
```

### Walidacja danych:

Parser automatycznie waliduje:

**Daty:**
- Format ISO: `YYYY-MM-DD`
- Format europejski: `DD.MM.YYYY`
- Format slash: `DD/MM/YYYY`
- Datetime: `YYYY-MM-DD, HH:MM:SS`

**Kwoty:**
- Liczby proste: `1000.50`
- Z separatorem tysięcy: `1,000.50`
- Z przecinkiem dziesiętnym: `1000,50`
- Ujemne: `-1000.50` lub `(1000.50)`
- Z symbolami walut: `$1,000.50`, `€500.25`

### Struktura danych wyjściowych:

```json
{
  "account_info": {
    "account_id": "U11673931",
    "base_currency": "CHF",
    "period": "2025-01-01 - 2025-12-03",
    "account_type": "Individual",
    "broker_name": "Interactive Brokers"
  },
  "nav": {
    "beginning": {"amount": 100000.00, "currency": "CHF"},
    "ending": {"amount": 125000.50, "currency": "CHF"}
  },
  "transactions": [...],
  "dividends": [...],
  "taxes": [...],
  "fees": [...],
  "interest": [...],
  "open_positions": [...],
  "securities_lending": [...],
  "forex_balances": [...],
  "exchange_rates": {...}
}
```

### Testowanie:

```bash
# Uruchomienie testów jednostkowych
python -m unittest test_parser -v

# Przykłady użycia
python example_usage.py
```

## Notatki prawne

⚠️ Ten skrypt jest narzędziem pomocniczym i nie stanowi porady podatkowej. 
Zawsze weryfikuj wygenerowany raport z doradcą podatkowym przed złożeniem deklaracji w Basel-Landschaft.

## Licencja

MIT License - Użycie na własne ryzyko

## Kontakt & Wsparcie

Pytania?  Utwórz issue na GitHub lub skontaktuj się z autorem. 

---

**Wersja:** 1.0.0  
**Ostatnia aktualizacja:** Grudzień 2025  
**Kompatybilność:** Python 3.8+
