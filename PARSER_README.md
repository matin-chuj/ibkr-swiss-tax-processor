# Activity Statement Parser - IBKR

Kompletny parser dla Interactive Brokers Activity Statement z pełną walidacją danych.

## Funkcjonalność

✅ **Parsowanie CSV** - Automatyczne wczytywanie struktury sekcja-nagłówek-dane  
✅ **14 sekcji** - Wszystkie główne sekcje Activity Statement  
✅ **Walidacja** - Spójność danych, formaty dat, sumy kontrolne  
✅ **Export JSON** - Strukturyzowane dane do dalszej analizy  
✅ **Raport walidacji** - Szczegółowy raport z błędami i ostrzeżeniami  
✅ **Obsługa błędów** - Graceful handling brakujących sekcji i błędnych danych  

## Instalacja

```bash
# Brak dodatkowych zależności - używa tylko standardowej biblioteki Python
python3 parser.py
```

## Użycie

### Podstawowe użycie

```python
from parser import ActivityStatementParser

# Utwórz parser
parser = ActivityStatementParser('activity_statement.csv')

# Parsuj dane
data = parser.parse()

# Eksportuj do JSON
parser.export_to_json('parsed_statement.json')

# Generuj raport walidacji
parser.generate_validation_report('validation_report.txt')
```

### Uruchomienie z przykładowym plikiem

```bash
python3 parser.py
```

Output:
- `parsed_statement.json` - Pełne sparsowane dane
- `validation_report.txt` - Raport z walidacji

## Parsowane sekcje

Parser obsługuje następujące sekcje z Activity Statement:

| Sekcja | Opis | Pola kluczowe |
|--------|------|---------------|
| **Statement Header** | Informacje o raporcie | Title, Period, Account |
| **Account Information** | Dane konta | Account ID, Base Currency |
| **Net Asset Value** | Wartość netto aktywów | Prior/This Period, Change |
| **Mark-to-Market Performance** | Wyniki MTM | P/L, Commissions, Fees |
| **Realized & Unrealized Performance** | Zyski/straty | Realized P/L, Unrealized P/L |
| **Open Positions** | Otwarte pozycje | Symbol, Quantity, Value |
| **Trades** | Historia transakcji | Date, Symbol, Price, Proceeds |
| **Dividends** | Dywidendy | Currency, Date, Amount |
| **Withholding Tax** | Podatki u źródła | Currency, Date, Amount |
| **Interest** | Odsetki | Currency, Date, Amount |
| **Fees** | Opłaty | Type, Currency, Amount |
| **Forex Balances** | Salda walutowe | Currency, Value, P/L |
| **Cash Report** | Raport gotówkowy | Currency, Total |
| **Securities Lending** | Wynajem papierów | Symbol, Fee, Amount |

## Struktura danych wyjściowych

### JSON Structure

```json
{
  "Statement": {
    "Title": "Activity Statement",
    "Period": "January 1, 2025 - December 3, 2025",
    "Account": "U11673931"
  },
  "Account Information": {
    "Account ID": "U11673931",
    "Base Currency": "CHF"
  },
  "Trades": {
    "items": [
      {
        "symbol": "AAPL",
        "date_time": "2025-01-15",
        "quantity": 50,
        "proceeds": -7250.00,
        "comm_fee": -1.50
      }
    ]
  }
}
```

## Walidacja danych

Parser wykonuje następujące sprawdzenia:

### 1. Spójność Net Asset Value
Weryfikuje równanie: `Początek + Zmiana = Koniec`

```
Prior Period + Change = This Period
```

### 2. Format dat
Sprawdza format YYYY-MM-DD w sekcjach:
- Trades
- Dividends
- Withholding Tax
- Interest
- Fees
- Securities Lending

### 3. Sumy kontrolne
Oblicza i loguje sumy dla:
- Dywidendy (total amount)
- Odsetki (total amount)
- Opłaty (total fees)
- Podatki u źródła (total tax)

### 4. Brakujące sekcje
Wykrywa i raportuje brakujące sekcje jako ostrzeżenia.

## Raport walidacji

Przykładowy raport `validation_report.txt`:

```
================================================================================
RAPORT WALIDACJI - IBKR Activity Statement Parser
================================================================================

Plik źródłowy: activity_statement.csv
Data walidacji: 2025-12-04 11:21:50

PODSUMOWANIE
--------------------------------------------------------------------------------
Sekcji sparsowanych: 14
Błędów: 0
Ostrzeżeń: 0
Informacji: 0

SEKCJE SPARSOWANE
--------------------------------------------------------------------------------
  ✓ Statement: 0 elementów
  ✓ Account Information: 0 elementów
  ✓ Net Asset Value: 4 elementów
  ✓ Trades: 6 elementów
  ✓ Dividends: 5 elementów

STATYSTYKI DANYCH
--------------------------------------------------------------------------------
  Transakcji: 6
  Dywidend: 5 (suma: 206.00)
  Odsetek: 5 (suma: 22.95)
  Opłat: 3 (suma: 17.50)
  Otwartych pozycji: 3
```

## Format pliku CSV

Activity Statement musi mieć strukturę:

```csv
SectionName,SubType,Field1,Field2,...
SectionName,Header,HeaderName1,HeaderName2,...
SectionName,Data,Value1,Value2,...
SectionName,Data,Value1,Value2,...

NextSection,Header,...
NextSection,Data,...
```

### Przykład:

```csv
Trades,Header,DataDiscriminator,Asset Category,Currency,Symbol,Date/Time,Quantity
Trades,Data,Order,Stocks,USD,AAPL,2025-01-15,50
Trades,Data,Order,Stocks,EUR,SAP,2025-02-10,50

Dividends,Header,Currency,Date,Description,Amount
Dividends,Data,USD,2025-02-01,AAPL Cash Dividend,24.00
```

## Typy błędów

### ERROR
Poważne problemy wymagające uwagi:
- Niespójność NAV
- Błędy parsowania kluczowych sekcji

### WARNING
Ostrzeżenia nie blokujące:
- Niepoprawny format daty
- Brakujące sekcje
- Brakujące pola

### INFO
Informacje pomocnicze:
- Statystyki parsowania
- Sumy kontrolne

## Obsługa błędów

Parser gracefully obsługuje:
- **Brakujące sekcje** - Loguje ostrzeżenie, kontynuuje
- **Niepoprawne formaty** - Używa wartości domyślnych (0, '')
- **Brakujące pola** - Bezpieczna konwersja z fallback
- **Nieprawidłowe liczby** - Decimal('0')

## Rozszerzenia

### Dodanie nowej sekcji

```python
# 1. Dodaj nazwę do sections_to_parse
self.sections_to_parse.append('New Section')

# 2. Utwórz metodę parsera
def _parse_new_section(self, rows: List[List[str]]) -> Dict[str, Any]:
    data = {'items': [], 'header': None}
    for row in rows:
        if row[1] == 'Data':
            item = {
                'field1': row[2],
                'field2': self._safe_decimal(row[3])
            }
            data['items'].append(item)
    return data

# 3. Dodaj do słownika parsers w _parse_section()
parsers['New Section'] = self._parse_new_section
```

### Własna walidacja

```python
def _custom_validation(self):
    """Własna walidacja"""
    if 'Trades' in self.data:
        for trade in self.data['Trades']['items']:
            if trade['quantity'] == 0:
                error = ValidationError(
                    'WARNING',
                    'Trades',
                    'Transakcja z zerową ilością'
                )
                self.validation_errors.append(error)

# Dodaj do _validate_data()
self._custom_validation()
```

## Integracja z istniejącym kodem

Parser można łatwo zintegrować z `ibkr_processor.py`:

```python
from parser import ActivityStatementParser

# W klasie IBKRTaxProcessor
def parse_with_validation(self):
    """Parsuj z walidacją"""
    parser = ActivityStatementParser(self.csv_file)
    data = parser.parse()
    
    # Użyj sparsowanych danych
    self.transactions = data['Trades']['items']
    self.dividends = data['Dividends']['items']
    
    # Generuj raport walidacji
    parser.generate_validation_report('validation_report.txt')
    
    return data
```

## Wymagania

- Python 3.8+
- Brak zewnętrznych zależności (tylko standardowa biblioteka)

## Testy

```bash
# Uruchom z przykładowym plikiem
python3 parser.py

# Sprawdź output
cat validation_report.txt
cat parsed_statement.json
```

## Licencja

MIT License - Zobacz LICENSE w głównym repo

## Kontakt

Pytania? Utwórz issue na GitHub.

---

**Parser v1.0**  
Grudzień 2025
