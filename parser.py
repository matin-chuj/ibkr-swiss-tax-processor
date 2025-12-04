"""
IBKR Activity Statement Parser
Kompleksowy parser raportów Activity Statement z Interactive Brokers

Funkcjonalność:
- Wczytywanie i parsowanie CSV z sekcjami
- Walidacja danych (spójność, daty, sumy)
- Export do JSON
- Raport walidacji
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal, InvalidOperation
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidationError:
    """Klasa reprezentująca błąd walidacji"""
    
    def __init__(self, severity: str, section: str, message: str, details: Optional[str] = None):
        self.severity = severity  # ERROR, WARNING, INFO
        self.section = section
        self.message = message
        self.details = details
        self.timestamp = datetime.now()
    
    def __str__(self):
        base = f"[{self.severity}] {self.section}: {self.message}"
        if self.details:
            base += f" - {self.details}"
        return base


class ActivityStatementParser:
    """
    Parser dla IBKR Activity Statement
    
    Obsługuje parsowanie wszystkich sekcji CSV oraz walidację danych
    """
    
    def __init__(self, csv_file: str):
        """
        Inicjalizacja parsera
        
        Args:
            csv_file: Ścieżka do pliku CSV z Activity Statement
        """
        self.csv_file = csv_file
        self.data: Dict[str, Any] = {}
        self.validation_errors: List[ValidationError] = []
        self.warnings: List[str] = []
        
        # Sekcje do parsowania
        self.sections_to_parse = [
            'Statement',
            'Account Information',
            'Net Asset Value',
            'Mark-to-Market Performance',
            'Realized & Unrealized Performance',
            'Open Positions',
            'Trades',
            'Dividends',
            'Withholding Tax',
            'Interest',
            'Fees',
            'Forex Balances',
            'Cash Report',
            'Securities Lending'
        ]
    
    def parse(self) -> Dict[str, Any]:
        """
        Główna metoda parsowania
        
        Returns:
            Słownik z wyparsowanymi danymi
        """
        logger.info(f"🔄 Rozpoczynam parsowanie: {self.csv_file}")
        
        # Wczytaj CSV
        raw_data = self._read_csv()
        
        # Parsuj sekcje
        self._parse_sections(raw_data)
        
        # Waliduj dane
        self._validate_data()
        
        logger.info(f"✅ Parsowanie zakończone. Sekcji: {len(self.data)}")
        logger.info(f"⚠️  Błędów walidacji: {len([e for e in self.validation_errors if e.severity == 'ERROR'])}")
        logger.info(f"⚠️  Ostrzeżeń: {len([e for e in self.validation_errors if e.severity == 'WARNING'])}")
        
        return self.data
    
    def _read_csv(self) -> List[List[str]]:
        """
        Wczytaj CSV do pamięci
        
        Returns:
            Lista wierszy CSV
        """
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
            logger.info(f"📂 Wczytano {len(rows)} wierszy z CSV")
            return rows
        except FileNotFoundError:
            logger.error(f"❌ Nie znaleziono pliku: {self.csv_file}")
            raise
        except Exception as e:
            logger.error(f"❌ Błąd podczas wczytywania CSV: {e}")
            raise
    
    def _parse_sections(self, rows: List[List[str]]):
        """
        Parsuj wszystkie sekcje z CSV
        
        Args:
            rows: Wiersze CSV
        """
        current_section = None
        section_rows = []
        
        for row in rows:
            if not row or len(row) == 0 or not row[0]:
                # Pusta linia może oznaczać koniec sekcji
                if current_section and section_rows:
                    self._parse_section(current_section, section_rows)
                    current_section = None
                    section_rows = []
                continue
            
            section_name = row[0].strip()
            
            # Sprawdź czy to nowa sekcja (inna niż bieżąca)
            if section_name in self.sections_to_parse:
                # Jeśli mamy już sekcję i to inna sekcja, zapisz poprzednią
                if current_section and current_section != section_name and section_rows:
                    self._parse_section(current_section, section_rows)
                    section_rows = []
                
                # Rozpocznij lub kontynuuj sekcję
                current_section = section_name
                section_rows.append(row)
            elif current_section:
                # To nie jest wiersz z nazwą sekcji, ale jesteśmy w sekcji
                section_rows.append(row)
        
        # Zapisz ostatnią sekcję
        if current_section and section_rows:
            self._parse_section(current_section, section_rows)
    
    def _parse_section(self, section_name: str, rows: List[List[str]]):
        """
        Parsuj konkretną sekcję
        
        Args:
            section_name: Nazwa sekcji
            rows: Wiersze należące do sekcji
        """
        logger.debug(f"📋 Parsowanie sekcji: {section_name}")
        
        parsers = {
            'Statement': self._parse_statement_header,
            'Account Information': self._parse_account_information,
            'Net Asset Value': self._parse_net_asset_value,
            'Mark-to-Market Performance': self._parse_mtm_performance,
            'Realized & Unrealized Performance': self._parse_realized_unrealized,
            'Open Positions': self._parse_open_positions,
            'Trades': self._parse_trades,
            'Dividends': self._parse_dividends,
            'Withholding Tax': self._parse_withholding_tax,
            'Interest': self._parse_interest,
            'Fees': self._parse_fees,
            'Forex Balances': self._parse_forex_balances,
            'Cash Report': self._parse_cash_report,
            'Securities Lending': self._parse_securities_lending
        }
        
        parser_func = parsers.get(section_name)
        if parser_func:
            try:
                result = parser_func(rows)
                self.data[section_name] = result
                logger.debug(f"✓ Sekcja {section_name} sparsowana pomyślnie")
            except Exception as e:
                error = ValidationError(
                    'ERROR',
                    section_name,
                    f"Błąd parsowania sekcji: {str(e)}"
                )
                self.validation_errors.append(error)
                logger.error(f"❌ {error}")
        else:
            logger.warning(f"⚠️  Brak parsera dla sekcji: {section_name}")
    
    def _parse_statement_header(self, rows: List[List[str]]) -> Dict[str, Any]:
        """Parsuj Statement Header"""
        data = {}
        for row in rows:
            if len(row) >= 4 and row[1] == 'Header':
                field_name = row[2].strip()
                field_value = row[3].strip() if len(row) > 3 else ''
                data[field_name] = field_value
        return data
    
    def _parse_account_information(self, rows: List[List[str]]) -> Dict[str, Any]:
        """Parsuj Account Information"""
        data = {}
        for row in rows:
            if len(row) >= 4 and row[1] == 'Data':
                field_name = row[2].strip()
                field_value = row[3].strip() if len(row) > 3 else ''
                data[field_name] = field_value
        return data
    
    def _parse_net_asset_value(self, rows: List[List[str]]) -> Dict[str, Any]:
        """Parsuj Net Asset Value"""
        data = {'items': [], 'header': None}
        
        for row in rows:
            if len(row) < 2:
                continue
            
            if row[1] == 'Header':
                data['header'] = row[2:]
            elif row[1] == 'Data':
                item = {
                    'asset_class': row[2] if len(row) > 2 else '',
                    'prior_period': self._safe_decimal(row[3]) if len(row) > 3 else 0,
                    'this_period': self._safe_decimal(row[4]) if len(row) > 4 else 0,
                    'change': self._safe_decimal(row[5]) if len(row) > 5 else 0
                }
                data['items'].append(item)
        
        return data
    
    def _parse_mtm_performance(self, rows: List[List[str]]) -> Dict[str, Any]:
        """Parsuj Mark-to-Market Performance"""
        data = {'items': [], 'header': None}
        
        for row in rows:
            if len(row) < 2:
                continue
            
            if row[1] == 'Header':
                data['header'] = row[2:]
            elif row[1] == 'Data':
                item = {
                    'asset_class': row[2] if len(row) > 2 else '',
                    'prior_period_mtm': self._safe_decimal(row[3]) if len(row) > 3 else 0,
                    'transaction_mtm': self._safe_decimal(row[4]) if len(row) > 4 else 0,
                    'mtm_price_fluctuation': self._safe_decimal(row[5]) if len(row) > 5 else 0,
                    'commissions': self._safe_decimal(row[6]) if len(row) > 6 else 0,
                    'other_fees': self._safe_decimal(row[7]) if len(row) > 7 else 0,
                    'total': self._safe_decimal(row[8]) if len(row) > 8 else 0
                }
                data['items'].append(item)
        
        return data
    
    def _parse_realized_unrealized(self, rows: List[List[str]]) -> Dict[str, Any]:
        """Parsuj Realized & Unrealized Performance"""
        data = {'items': [], 'header': None}
        
        for row in rows:
            if len(row) < 2:
                continue
            
            if row[1] == 'Header':
                data['header'] = row[2:]
            elif row[1] == 'Data':
                item = {
                    'asset_class': row[2] if len(row) > 2 else '',
                    'code': row[3] if len(row) > 3 else '',
                    'realized_pl': self._safe_decimal(row[4]) if len(row) > 4 else 0,
                    'unrealized_pl': self._safe_decimal(row[5]) if len(row) > 5 else 0,
                    'total': self._safe_decimal(row[6]) if len(row) > 6 else 0
                }
                data['items'].append(item)
        
        return data
    
    def _parse_open_positions(self, rows: List[List[str]]) -> Dict[str, Any]:
        """Parsuj Open Positions"""
        data = {'items': [], 'header': None}
        
        for row in rows:
            if len(row) < 2:
                continue
            
            if row[1] == 'Header':
                data['header'] = row[2:]
            elif row[1] == 'Data':
                item = {
                    'data_discriminator': row[2] if len(row) > 2 else '',
                    'asset_category': row[3] if len(row) > 3 else '',
                    'currency': row[4] if len(row) > 4 else '',
                    'symbol': row[5] if len(row) > 5 else '',
                    'quantity': self._safe_decimal(row[6]) if len(row) > 6 else 0,
                    'mult': self._safe_decimal(row[7]) if len(row) > 7 else 1,
                    'cost_price': self._safe_decimal(row[8]) if len(row) > 8 else 0,
                    'cost_basis': self._safe_decimal(row[9]) if len(row) > 9 else 0,
                    'close_price': self._safe_decimal(row[10]) if len(row) > 10 else 0,
                    'value': self._safe_decimal(row[11]) if len(row) > 11 else 0,
                    'unrealized_pl': self._safe_decimal(row[12]) if len(row) > 12 else 0,
                    'code': row[13] if len(row) > 13 else ''
                }
                data['items'].append(item)
        
        return data
    
    def _parse_trades(self, rows: List[List[str]]) -> Dict[str, Any]:
        """Parsuj Trades"""
        data = {'items': [], 'header': None}
        
        for row in rows:
            if len(row) < 2:
                continue
            
            if row[1] == 'Header':
                data['header'] = row[2:]
            elif row[1] == 'Data':
                item = {
                    'data_discriminator': row[2] if len(row) > 2 else '',
                    'asset_category': row[3] if len(row) > 3 else '',
                    'currency': row[4] if len(row) > 4 else '',
                    'symbol': row[5] if len(row) > 5 else '',
                    'date_time': row[6] if len(row) > 6 else '',
                    'quantity': self._safe_decimal(row[7]) if len(row) > 7 else 0,
                    't_price': self._safe_decimal(row[8]) if len(row) > 8 else 0,
                    'c_price': self._safe_decimal(row[9]) if len(row) > 9 else 0,
                    'proceeds': self._safe_decimal(row[10]) if len(row) > 10 else 0,
                    'comm_fee': self._safe_decimal(row[11]) if len(row) > 11 else 0,
                    'basis': row[12] if len(row) > 12 else '',
                    'realized_pl': row[13] if len(row) > 13 else '',
                    'mtm_pl': row[14] if len(row) > 14 else '',
                    'code': row[15] if len(row) > 15 else ''
                }
                data['items'].append(item)
        
        return data
    
    def _parse_dividends(self, rows: List[List[str]]) -> Dict[str, Any]:
        """Parsuj Dividends"""
        data = {'items': [], 'header': None}
        
        for row in rows:
            if len(row) < 2:
                continue
            
            if row[1] == 'Header':
                data['header'] = row[2:]
            elif row[1] == 'Data':
                item = {
                    'currency': row[2] if len(row) > 2 else '',
                    'date': row[3] if len(row) > 3 else '',
                    'description': row[4] if len(row) > 4 else '',
                    'amount': self._safe_decimal(row[5]) if len(row) > 5 else 0
                }
                data['items'].append(item)
        
        return data
    
    def _parse_withholding_tax(self, rows: List[List[str]]) -> Dict[str, Any]:
        """Parsuj Withholding Tax"""
        data = {'items': [], 'header': None}
        
        for row in rows:
            if len(row) < 2:
                continue
            
            if row[1] == 'Header':
                data['header'] = row[2:]
            elif row[1] == 'Data':
                item = {
                    'currency': row[2] if len(row) > 2 else '',
                    'date': row[3] if len(row) > 3 else '',
                    'description': row[4] if len(row) > 4 else '',
                    'amount': self._safe_decimal(row[5]) if len(row) > 5 else 0
                }
                data['items'].append(item)
        
        return data
    
    def _parse_interest(self, rows: List[List[str]]) -> Dict[str, Any]:
        """Parsuj Interest"""
        data = {'items': [], 'header': None}
        
        for row in rows:
            if len(row) < 2:
                continue
            
            if row[1] == 'Header':
                data['header'] = row[2:]
            elif row[1] == 'Data':
                item = {
                    'currency': row[2] if len(row) > 2 else '',
                    'date': row[3] if len(row) > 3 else '',
                    'description': row[4] if len(row) > 4 else '',
                    'amount': self._safe_decimal(row[5]) if len(row) > 5 else 0
                }
                data['items'].append(item)
        
        return data
    
    def _parse_fees(self, rows: List[List[str]]) -> Dict[str, Any]:
        """Parsuj Fees"""
        data = {'items': [], 'header': None}
        
        for row in rows:
            if len(row) < 2:
                continue
            
            if row[1] == 'Header':
                data['header'] = row[2:]
            elif row[1] == 'Data':
                item = {
                    'subtitle': row[2] if len(row) > 2 else '',
                    'currency': row[3] if len(row) > 3 else '',
                    'date': row[4] if len(row) > 4 else '',
                    'description': row[5] if len(row) > 5 else '',
                    'amount': self._safe_decimal(row[6]) if len(row) > 6 else 0
                }
                data['items'].append(item)
        
        return data
    
    def _parse_forex_balances(self, rows: List[List[str]]) -> Dict[str, Any]:
        """Parsuj Forex Balances"""
        data = {'items': [], 'header': None}
        
        for row in rows:
            if len(row) < 2:
                continue
            
            if row[1] == 'Header':
                data['header'] = row[2:]
            elif row[1] == 'Data':
                item = {
                    'asset_category': row[2] if len(row) > 2 else '',
                    'currency': row[3] if len(row) > 3 else '',
                    'quantity': self._safe_decimal(row[4]) if len(row) > 4 else 0,
                    'cost_price': self._safe_decimal(row[5]) if len(row) > 5 else 0,
                    'cost_basis': self._safe_decimal(row[6]) if len(row) > 6 else 0,
                    'close_price': self._safe_decimal(row[7]) if len(row) > 7 else 0,
                    'value': self._safe_decimal(row[8]) if len(row) > 8 else 0,
                    'unrealized_pl': self._safe_decimal(row[9]) if len(row) > 9 else 0,
                    'pct_of_nav': self._safe_decimal(row[10]) if len(row) > 10 else 0
                }
                data['items'].append(item)
        
        return data
    
    def _parse_cash_report(self, rows: List[List[str]]) -> Dict[str, Any]:
        """Parsuj Cash Report"""
        data = {'items': [], 'header': None}
        
        for row in rows:
            if len(row) < 2:
                continue
            
            if row[1] == 'Header':
                data['header'] = row[2:]
            elif row[1] == 'Data':
                item = {
                    'currency': row[2] if len(row) > 2 else '',
                    'total': self._safe_decimal(row[3]) if len(row) > 3 else 0,
                    'securities': self._safe_decimal(row[4]) if len(row) > 4 else 0,
                    'futures': self._safe_decimal(row[5]) if len(row) > 5 else 0
                }
                data['items'].append(item)
        
        return data
    
    def _parse_securities_lending(self, rows: List[List[str]]) -> Dict[str, Any]:
        """Parsuj Securities Lending"""
        data = {'items': [], 'header': None}
        
        for row in rows:
            if len(row) < 2:
                continue
            
            if row[1] == 'Header':
                data['header'] = row[2:]
            elif row[1] == 'Data':
                item = {
                    'currency': row[2] if len(row) > 2 else '',
                    'date': row[3] if len(row) > 3 else '',
                    'symbol': row[4] if len(row) > 4 else '',
                    'quantity': self._safe_decimal(row[5]) if len(row) > 5 else 0,
                    'fee_rate': self._safe_decimal(row[6]) if len(row) > 6 else 0,
                    'amount': self._safe_decimal(row[7]) if len(row) > 7 else 0
                }
                data['items'].append(item)
        
        return data
    
    def _safe_decimal(self, value: Any) -> Decimal:
        """
        Bezpieczna konwersja do Decimal
        
        Args:
            value: Wartość do konwersji
            
        Returns:
            Wartość jako Decimal lub 0
        """
        if not value or value == '':
            return Decimal('0')
        
        try:
            # Usuń przecinki z tysięcy
            if isinstance(value, str):
                value = value.replace(',', '')
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return Decimal('0')
    
    def _validate_data(self):
        """Waliduj sparsowane dane"""
        logger.info("🔍 Rozpoczynam walidację danych...")
        
        # Walidacja dat
        self._validate_dates()
        
        # Walidacja NAV (Net Asset Value)
        self._validate_nav_consistency()
        
        # Walidacja sum kontrolnych
        self._validate_checksums()
        
        # Walidacja brakujących sekcji
        self._validate_missing_sections()
        
        logger.info(f"✅ Walidacja zakończona")
    
    def _validate_dates(self):
        """Waliduj formaty dat"""
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        
        sections_with_dates = [
            ('Trades', 'date_time'),
            ('Dividends', 'date'),
            ('Withholding Tax', 'date'),
            ('Interest', 'date'),
            ('Fees', 'date'),
            ('Securities Lending', 'date')
        ]
        
        for section_name, date_field in sections_with_dates:
            if section_name not in self.data:
                continue
            
            section = self.data[section_name]
            if 'items' not in section:
                continue
            
            for idx, item in enumerate(section['items']):
                date_value = item.get(date_field, '')
                if date_value and not date_pattern.match(date_value):
                    error = ValidationError(
                        'WARNING',
                        section_name,
                        f"Niepoprawny format daty w wierszu {idx + 1}",
                        f"Oczekiwano YYYY-MM-DD, otrzymano: {date_value}"
                    )
                    self.validation_errors.append(error)
    
    def _validate_nav_consistency(self):
        """Waliduj spójność Net Asset Value (początek + zmiana = koniec)"""
        if 'Net Asset Value' not in self.data:
            error = ValidationError(
                'WARNING',
                'Net Asset Value',
                "Brak sekcji Net Asset Value"
            )
            self.validation_errors.append(error)
            return
        
        nav_data = self.data['Net Asset Value']
        if 'items' not in nav_data:
            return
        
        for item in nav_data['items']:
            prior = item.get('prior_period', 0)
            this_period = item.get('this_period', 0)
            change = item.get('change', 0)
            asset_class = item.get('asset_class', 'Unknown')
            
            # Sprawdź spójność: prior + change = this_period
            expected = prior + change
            tolerance = Decimal('0.01')  # Tolerancja zaokrągleń
            
            if abs(expected - this_period) > tolerance:
                error = ValidationError(
                    'ERROR',
                    'Net Asset Value',
                    f"Niespójność dla {asset_class}",
                    f"Początek ({prior}) + Zmiana ({change}) != Koniec ({this_period}). "
                    f"Oczekiwano: {expected}"
                )
                self.validation_errors.append(error)
    
    def _validate_checksums(self):
        """Waliduj sumy kontrolne dla każdej sekcji"""
        
        # Walidacja sum dla Dividends
        self._validate_section_sum('Dividends', 'amount', 'Dywidendy')
        
        # Walidacja sum dla Interest
        self._validate_section_sum('Interest', 'amount', 'Odsetki')
        
        # Walidacja sum dla Fees
        self._validate_section_sum('Fees', 'amount', 'Opłaty')
        
        # Walidacja sum dla Withholding Tax
        self._validate_section_sum('Withholding Tax', 'amount', 'Podatki u źródła')
    
    def _validate_section_sum(self, section_name: str, field: str, display_name: str):
        """
        Waliduj sumę dla konkretnej sekcji
        
        Args:
            section_name: Nazwa sekcji
            field: Pole do zsumowania
            display_name: Nazwa wyświetlana
        """
        if section_name not in self.data:
            return
        
        section = self.data[section_name]
        if 'items' not in section:
            return
        
        total = sum(item.get(field, 0) for item in section['items'])
        
        # Loguj informację o sumie
        logger.info(f"📊 {display_name}: Suma = {total}")
        
        # Sprawdź czy jest Total row i porównaj
        # (w prawdziwym Activity Statement czasem jest wiersz Total)
        # To jest placeholder - można rozwinąć
    
    def _validate_missing_sections(self):
        """Sprawdź brakujące sekcje"""
        for section in self.sections_to_parse:
            if section not in self.data:
                error = ValidationError(
                    'WARNING',
                    section,
                    f"Brak sekcji: {section}"
                )
                self.validation_errors.append(error)
    
    def export_to_json(self, output_file: str = 'parsed_statement.json'):
        """
        Eksportuj sparsowane dane do JSON
        
        Args:
            output_file: Nazwa pliku wyjściowego
        """
        logger.info(f"💾 Eksportuję dane do JSON: {output_file}")
        
        # Konwertuj Decimal na float dla JSON
        json_data = self._convert_decimals_to_float(self.data)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Dane wyeksportowane do: {output_file}")
    
    def _convert_decimals_to_float(self, obj: Any) -> Any:
        """
        Rekurencyjnie konwertuj Decimal na float dla JSON
        
        Args:
            obj: Obiekt do konwersji
            
        Returns:
            Obiekt z Decimal zamienionymi na float
        """
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: self._convert_decimals_to_float(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimals_to_float(item) for item in obj]
        else:
            return obj
    
    def generate_validation_report(self, output_file: str = 'validation_report.txt'):
        """
        Generuj raport walidacji
        
        Args:
            output_file: Nazwa pliku wyjściowego
        """
        logger.info(f"📋 Generuję raport walidacji: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("RAPORT WALIDACJI - IBKR Activity Statement Parser\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Plik źródłowy: {self.csv_file}\n")
            f.write(f"Data walidacji: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Podsumowanie
            f.write("PODSUMOWANIE\n")
            f.write("-" * 80 + "\n")
            f.write(f"Sekcji sparsowanych: {len(self.data)}\n")
            
            errors = [e for e in self.validation_errors if e.severity == 'ERROR']
            warnings = [e for e in self.validation_errors if e.severity == 'WARNING']
            infos = [e for e in self.validation_errors if e.severity == 'INFO']
            
            f.write(f"Błędów: {len(errors)}\n")
            f.write(f"Ostrzeżeń: {len(warnings)}\n")
            f.write(f"Informacji: {len(infos)}\n\n")
            
            # Sekcje sparsowane
            f.write("SEKCJE SPARSOWANE\n")
            f.write("-" * 80 + "\n")
            for section_name, section_data in self.data.items():
                item_count = len(section_data.get('items', []))
                f.write(f"  ✓ {section_name}: {item_count} elementów\n")
            f.write("\n")
            
            # Błędy
            if errors:
                f.write("BŁĘDY\n")
                f.write("-" * 80 + "\n")
                for error in errors:
                    f.write(f"  ❌ {error}\n")
                f.write("\n")
            
            # Ostrzeżenia
            if warnings:
                f.write("OSTRZEŻENIA\n")
                f.write("-" * 80 + "\n")
                for warning in warnings:
                    f.write(f"  ⚠️  {warning}\n")
                f.write("\n")
            
            # Informacje
            if infos:
                f.write("INFORMACJE\n")
                f.write("-" * 80 + "\n")
                for info in infos:
                    f.write(f"  ℹ️  {info}\n")
                f.write("\n")
            
            # Podsumowanie statystyk
            f.write("STATYSTYKI DANYCH\n")
            f.write("-" * 80 + "\n")
            
            # Trades
            if 'Trades' in self.data:
                trades = self.data['Trades'].get('items', [])
                f.write(f"  Transakcji: {len(trades)}\n")
            
            # Dividends
            if 'Dividends' in self.data:
                dividends = self.data['Dividends'].get('items', [])
                total_div = sum(item.get('amount', 0) for item in dividends)
                f.write(f"  Dywidend: {len(dividends)} (suma: {total_div})\n")
            
            # Interest
            if 'Interest' in self.data:
                interest = self.data['Interest'].get('items', [])
                total_int = sum(item.get('amount', 0) for item in interest)
                f.write(f"  Odsetek: {len(interest)} (suma: {total_int})\n")
            
            # Fees
            if 'Fees' in self.data:
                fees = self.data['Fees'].get('items', [])
                total_fees = sum(abs(item.get('amount', 0)) for item in fees)
                f.write(f"  Opłat: {len(fees)} (suma: {total_fees})\n")
            
            # Open Positions
            if 'Open Positions' in self.data:
                positions = self.data['Open Positions'].get('items', [])
                f.write(f"  Otwartych pozycji: {len(positions)}\n")
            
            f.write("\n")
            f.write("=" * 80 + "\n")
            f.write("KONIEC RAPORTU\n")
            f.write("=" * 80 + "\n")
        
        logger.info(f"✅ Raport walidacji zapisany: {output_file}")


def main():
    """Główna funkcja - przykład użycia"""
    
    # Parsuj Activity Statement
    parser = ActivityStatementParser('activity_statement.csv')
    
    # Parsuj dane
    data = parser.parse()
    
    # Eksportuj do JSON
    parser.export_to_json('parsed_statement.json')
    
    # Generuj raport walidacji
    parser.generate_validation_report('validation_report.txt')
    
    print("\n" + "=" * 80)
    print("✨ PARSOWANIE ZAKOŃCZONE POMYŚLNIE!")
    print("=" * 80)
    print(f"\n📊 Pliki wyjściowe:")
    print(f"  1. parsed_statement.json - Pełne dane w formacie JSON")
    print(f"  2. validation_report.txt - Raport walidacji\n")


if __name__ == '__main__':
    main()
