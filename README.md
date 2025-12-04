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

- Python 3.8+
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
PLN/CHF: 0.22084
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
├── ibkr_processor.py        # Główna klasa procesora
├── requirements.txt         # Zależności Python
├── README.md               # Dokumentacja
└── examples/
    └── sample_report/
        ├── tax_report_2025.xlsx
        └── tax_report_2025.html
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
