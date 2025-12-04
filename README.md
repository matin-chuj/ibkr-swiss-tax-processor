# IBKR Swiss Tax Processor - Basel-Landschaft

🇨🇭 Narzędzie do przetwarzania raportów IBKR Activity Statement i generowania raportów podatkowych dla kantonu Basel-Landschaft. 

## Funcje

### KROK A: Parser IBKR (ibkr_processor.py)
✅ **Parsowanie CSV z IBKR** - Automatyczne czytanie i strukturyzowanie danych
✅ **Konwersja walut** - Obsługa EUR, USD, JPY, NOK, PLN, SEK → CHF
✅ **Kategoryzacja podatkowa** - Zgodnie z wymogami Basel-Landschaft
✅ **Excel Report** - Siedem arkuszy ze szczegółami
✅ **HTML Preview** - Interaktywny podgląd raportów
✅ **Polskie tłumaczenie** - Wszystkie nazwy w języku polskim

### KROK B: Generator Raportów BL (report_generator_bl.py) ⭐ NOWE!
✅ **Wertschriftenverzeichnis BL 2025** - Oficjalny format dla Basel-Landschaft
✅ **Excel (.xlsx)** - 6 arkuszy z sekcjami podatkowymi + podsumowanie
✅ **PDF (.pdf)** - Profesjonalny raport gotowy do druku
✅ **JSON (.json)** - Dane strukturalne do dalszego przetwarzania
✅ **Obliczenia podatkowe** - Vermögenssteuer (0.08%) + Einkommenssteuer (10.55%)
✅ **Kredyt zagraniczny** - Automatyczne obliczanie zwrotu podatku zagranicznego
✅ **Testy jednostkowe** - 18 testów zapewniających poprawność obliczeń

📘 **[Zobacz pełną dokumentację Report Generator](REPORT_GENERATOR_README.md)**

## Wymagania

- Python 3.8+
- pandas >= 2.0.0
- openpyxl >= 3.1.0
- numpy >= 1.24.0
- requests >= 2.31.0
- reportlab >= 4.0.0 (dla PDF)

## Instalacja

```bash
pip install -r requirements.txt
```

## Użycie

### KROK A: Podstawowe użycie (Parser IBKR)

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

**Output KROK A:** Proces generuje dwa pliki:
1. **tax_report_2025.xlsx** - Plik Excel z siedmioma arkuszami
2. **tax_report_2025.html** - Interaktywny podgląd w przeglądarce

---

### KROK B: Generator Raportów BL (NOWE!) ⭐

```python
from ibkr_processor import IBKRTaxProcessor
from report_generator_bl import ReportGeneratorBL

# 1. Parse IBKR statement
processor = IBKRTaxProcessor('your_statement.csv', tax_year=2025)
processor.parse_ibkr_statement()

# 2. Prepare data
parsed_data = {
    'transactions': processor.transactions,
    'dividends': processor.dividends,
    'taxes': processor.taxes,
    'fees': processor.fees,
    'open_positions': processor.open_positions
}

# 3. Generate Basel-Landschaft reports
generator = ReportGeneratorBL(parsed_data)
reports = generator.generate_all_reports('output')

# Reports generated:
# - Wertschriftenverzeichnis_BL_2025.xlsx (Excel)
# - Tax_Report_BL_2025.pdf (PDF)
# - Tax_Summary_BL_2025.json (JSON)
```

**Output KROK B:** Proces generuje trzy pliki:
1. **Wertschriftenverzeichnis_BL_2025.xlsx** - Oficjalny raport BL w Excel
   - 0_ZUSAMMENFASSUNG - Podsumowanie podatkowe
   - 1_Vermögensaufstellung - Stan majątku
   - 2_Einkünfte - Dochody z majątku
   - 3_Kapitalgewinne - Zyski/straty kapitałowe
   - 4_Kosten - Koszty i opłaty
   - 5_Devisen - Zyski/straty walutowe

2. **Tax_Report_BL_2025.pdf** - Profesjonalny raport PDF gotowy do druku

3. **Tax_Summary_BL_2025.json** - Dane strukturalne JSON

**Szybki start z przykładem:**
```bash
python example_bl_report.py                      # Z przykładowymi danymi
python example_bl_report.py your_statement.csv   # Z Twoim plikiem CSV
```

### Output (Stary format - KROK A)

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

### Stawki podatkowe BL 2025:
- **Vermögenssteuer** (podatek od majątku): 0.08% (0.0008)
- **Einkommenssteuer** (podatek dochodowy): 10.55% (0.1055)
- **Minimum podatkowe**: CHF 50 (poniżej tej kwoty zwolnione)
- **Kredyt zagraniczny**: US 100%, inne kraje 80%

### Kalkulacje podatkowe (KROK B):
```
Podatek od majątku  = Wartość aktywów × 0.0008
Podatek dochodowy   = (Dochód - Koszty) × 0.1055
Kredyt zagraniczny  = (US podatki × 100%) + (Inne × 80%)
Netto do zapłaty    = (Podatek od majątku + dochodowy) - Kredyt
```

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

## Testy

### Uruchomienie testów jednostkowych

Generator raportów BL zawiera kompletny zestaw testów:

```bash
python test_report_generator.py
```

**Pokrycie testów:**
- ✅ 18 testów jednostkowych
- ✅ Kalkulacje podatków (wealth tax, income tax, foreign credit)
- ✅ Generowanie raportów (Excel, PDF, JSON)
- ✅ Walidacja konfiguracji
- ✅ Obsługa przypadków brzegowych

**Przykładowy output:**
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
├── ibkr_processor.py                # KROK A: Parser IBKR CSV
├── report_generator_bl.py           # KROK B: Generator raportów BL (Excel/PDF/JSON)
├── tax_calculator_bl.py             # Kalkulator podatkowy dla BL
├── basellandschaft_config.json      # Konfiguracja stawek i formatów BL
├── test_report_generator.py         # Testy jednostkowe (18 testów)
├── example_bl_report.py             # Przykład użycia z danymi sample
├── requirements.txt                 # Zależności Python
├── README.md                        # Główna dokumentacja (ten plik)
├── REPORT_GENERATOR_README.md       # Szczegółowa dokumentacja generatora
└── .gitignore                       # Wykluczenia git (pliki wynikowe)
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
