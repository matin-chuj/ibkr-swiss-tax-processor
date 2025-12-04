"""
Basel-Landschaft Tax Calculator
Handles tax-specific calculations for the Canton of Basel-Landschaft
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class TaxCalculatorBL:
    """Tax calculator for Basel-Landschaft canton"""

    def __init__(self, config_file: str = 'basellandschaft_config.json'):
        """
        Initialize tax calculator with BL configuration
        
        Args:
            config_file: Path to Basel-Landschaft configuration file
        """
        self.config = self._load_config(config_file)
        self.canton = self.config['canton']
        self.tax_year = self.config['tax_year']
        
        # Tax rates
        self.income_tax_rate = self.config['tax_rates']['income_tax_rate']
        self.wealth_tax_rate = self.config['tax_rates']['wealth_tax_rate']
        self.minimum_threshold = self.config['tax_rates']['minimum_taxable_threshold']
        
        # Currency rates
        self.fx_rates = self.config['currency_rates']['rates']
        
        logger.info(f"Tax calculator initialized for {self.canton}, year {self.tax_year}")

    def _load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file"""
        config_path = Path(config_file)
        if not config_path.exists():
            logger.warning(f"Config file {config_file} not found, using defaults")
            return self._get_default_config()
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _get_default_config(self) -> Dict:
        """Get default configuration if file not found"""
        return {
            "canton": "Basel-Landschaft",
            "tax_year": 2025,
            "tax_rates": {
                "income_tax_rate": 0.1055,
                "wealth_tax_rate": 0.0008,
                "minimum_taxable_threshold": 50.0
            },
            "currency_rates": {
                "rates": {
                    "CHF": 1.0,
                    "EUR": 0.93324,
                    "USD": 0.79959
                }
            }
        }

    def calculate_wealth_tax(self, total_assets_chf: float) -> Dict[str, float]:
        """
        Calculate wealth tax (Vermögenssteuer)
        
        Args:
            total_assets_chf: Total assets in CHF
            
        Returns:
            Dictionary with wealth tax details
        """
        if total_assets_chf < self.minimum_threshold:
            return {
                'taxable_wealth': 0.0,
                'wealth_tax': 0.0,
                'tax_rate': self.wealth_tax_rate,
                'exemption_applied': True
            }
        
        wealth_tax = total_assets_chf * self.wealth_tax_rate
        
        return {
            'taxable_wealth': total_assets_chf,
            'wealth_tax': wealth_tax,
            'tax_rate': self.wealth_tax_rate,
            'exemption_applied': False
        }

    def calculate_income_tax(self, total_income_chf: float, 
                            deductible_costs_chf: float = 0.0) -> Dict[str, float]:
        """
        Calculate income tax (Einkommenssteuer)
        
        Args:
            total_income_chf: Total income in CHF
            deductible_costs_chf: Deductible costs
            
        Returns:
            Dictionary with income tax details
        """
        taxable_income = max(0, total_income_chf - deductible_costs_chf)
        
        if taxable_income < self.minimum_threshold:
            return {
                'gross_income': total_income_chf,
                'deductible_costs': deductible_costs_chf,
                'taxable_income': 0.0,
                'income_tax': 0.0,
                'tax_rate': self.income_tax_rate,
                'exemption_applied': True
            }
        
        income_tax = taxable_income * self.income_tax_rate
        
        return {
            'gross_income': total_income_chf,
            'deductible_costs': deductible_costs_chf,
            'taxable_income': taxable_income,
            'income_tax': income_tax,
            'tax_rate': self.income_tax_rate,
            'exemption_applied': False
        }

    def calculate_foreign_tax_credit(self, foreign_taxes_by_country: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate foreign tax credit (Steuerrückerstattung)
        
        Args:
            foreign_taxes_by_country: Dictionary with country codes as keys and tax amounts in CHF
            
        Returns:
            Dictionary with credit details
        """
        total_foreign_tax = sum(foreign_taxes_by_country.values())
        
        # US withholding tax is fully creditable
        us_tax = foreign_taxes_by_country.get('US', 0.0)
        other_tax = total_foreign_tax - us_tax
        
        # Simplified credit calculation - actual BL rules may be more complex
        creditable_amount = us_tax * 1.0 + other_tax * 0.8  # 100% US, 80% other
        
        return {
            'total_foreign_tax': total_foreign_tax,
            'us_withholding_tax': us_tax,
            'other_foreign_tax': other_tax,
            'creditable_amount': creditable_amount,
            'non_creditable_amount': total_foreign_tax - creditable_amount
        }

    def calculate_net_tax_liability(self, 
                                    wealth_tax: float,
                                    income_tax: float,
                                    foreign_tax_credit: float) -> Dict[str, float]:
        """
        Calculate net tax liability after credits
        
        Args:
            wealth_tax: Calculated wealth tax
            income_tax: Calculated income tax
            foreign_tax_credit: Foreign tax credit amount
            
        Returns:
            Dictionary with net tax liability
        """
        gross_tax = wealth_tax + income_tax
        net_tax = max(0, gross_tax - foreign_tax_credit)
        
        return {
            'wealth_tax': wealth_tax,
            'income_tax': income_tax,
            'gross_tax_liability': gross_tax,
            'foreign_tax_credit': foreign_tax_credit,
            'net_tax_liability': net_tax
        }

    def calculate_capital_gains_summary(self, transactions: List[Dict]) -> Dict[str, float]:
        """
        Calculate capital gains/losses summary
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            Summary of capital gains/losses
        """
        realized_gains = 0.0
        realized_losses = 0.0
        
        for t in transactions:
            proceeds_chf = t.get('proceeds_chf', 0.0)
            
            if proceeds_chf > 0:
                realized_gains += proceeds_chf
            else:
                realized_losses += abs(proceeds_chf)
        
        net_gain_loss = realized_gains - realized_losses
        
        return {
            'realized_gains': realized_gains,
            'realized_losses': realized_losses,
            'net_capital_gain_loss': net_gain_loss
        }

    def categorize_income_by_source(self, dividends: List[Dict], 
                                    interests: List[Dict]) -> Dict[str, Dict]:
        """
        Categorize income by source (Swiss vs Foreign)
        
        Args:
            dividends: List of dividend dictionaries
            interests: List of interest dictionaries
            
        Returns:
            Categorized income summary
        """
        swiss_dividends = 0.0
        foreign_dividends = 0.0
        total_interest = 0.0
        
        for div in dividends:
            amount_chf = div.get('amount_chf', 0.0)
            symbol = div.get('symbol', '')
            
            # Simple heuristic: Swiss symbols typically don't have country suffix
            # This should be improved with actual country data
            if symbol and len(symbol) <= 4:
                swiss_dividends += amount_chf
            else:
                foreign_dividends += amount_chf
        
        for interest in interests:
            total_interest += interest.get('amount_chf', 0.0)
        
        return {
            'swiss': {
                'dividends': swiss_dividends,
                'total': swiss_dividends
            },
            'foreign': {
                'dividends': foreign_dividends,
                'total': foreign_dividends
            },
            'interest': {
                'total': total_interest
            }
        }

    def calculate_fx_gains_losses(self, forex_transactions: List[Dict]) -> Dict[str, float]:
        """
        Calculate foreign exchange gains/losses
        
        Args:
            forex_transactions: List of forex transaction dictionaries
            
        Returns:
            FX gains/losses summary
        """
        fx_gains = 0.0
        fx_losses = 0.0
        
        for fx in forex_transactions:
            proceeds_chf = fx.get('proceeds_chf', 0.0)
            
            if proceeds_chf > 0:
                fx_gains += proceeds_chf
            else:
                fx_losses += abs(proceeds_chf)
        
        net_fx = fx_gains - fx_losses
        
        return {
            'fx_gains': fx_gains,
            'fx_losses': fx_losses,
            'net_fx_result': net_fx
        }

    def calculate_total_costs(self, transactions: List[Dict], 
                             fees: List[Dict]) -> Dict[str, float]:
        """
        Calculate total deductible costs
        
        Args:
            transactions: List of transactions with commissions
            fees: List of account fees
            
        Returns:
            Total costs summary
        """
        transaction_fees = sum(t.get('commission_chf', 0.0) for t in transactions)
        account_fees = sum(f.get('amount_chf', 0.0) for f in fees)
        other_costs = 0.0  # Placeholder for other costs
        
        total_costs = transaction_fees + account_fees + other_costs
        
        return {
            'transaction_fees': transaction_fees,
            'account_fees': account_fees,
            'other_costs': other_costs,
            'total_deductible_costs': total_costs
        }

    def generate_tax_summary(self, parsed_data: Dict) -> Dict:
        """
        Generate complete tax summary for Basel-Landschaft
        
        Args:
            parsed_data: Parsed IBKR statement data
            
        Returns:
            Complete tax summary
        """
        # Extract data
        transactions = parsed_data.get('transactions', [])
        dividends = parsed_data.get('dividends', [])
        interests = [d for d in dividends if d.get('type') == 'Interest']
        div_only = [d for d in dividends if d.get('type') != 'Interest']
        taxes = parsed_data.get('taxes', [])
        fees = parsed_data.get('fees', [])
        open_positions = parsed_data.get('open_positions', [])
        
        # Filter forex transactions
        forex_transactions = [t for t in transactions if t.get('type') == 'Forex']
        stock_transactions = [t for t in transactions if t.get('type') != 'Forex']
        
        # Calculate components
        wealth_position = sum(p.get('value_chf', 0.0) for p in open_positions)
        
        income_by_source = self.categorize_income_by_source(div_only, interests)
        total_income = (income_by_source['swiss']['total'] + 
                       income_by_source['foreign']['total'] + 
                       income_by_source['interest']['total'])
        
        capital_gains = self.calculate_capital_gains_summary(stock_transactions)
        fx_result = self.calculate_fx_gains_losses(forex_transactions)
        costs = self.calculate_total_costs(transactions, fees)
        
        # Calculate taxes
        wealth_tax_calc = self.calculate_wealth_tax(wealth_position)
        income_tax_calc = self.calculate_income_tax(total_income, costs['total_deductible_costs'])
        
        # Foreign tax credit
        foreign_taxes_by_country = {'US': sum(t.get('amount_chf', 0.0) for t in taxes)}
        foreign_credit = self.calculate_foreign_tax_credit(foreign_taxes_by_country)
        
        net_liability = self.calculate_net_tax_liability(
            wealth_tax_calc['wealth_tax'],
            income_tax_calc['income_tax'],
            foreign_credit['creditable_amount']
        )
        
        return {
            'canton': self.canton,
            'tax_year': self.tax_year,
            'calculation_date': datetime.now().strftime('%Y-%m-%d'),
            'wealth': {
                'total_assets_chf': wealth_position,
                **wealth_tax_calc
            },
            'income': {
                'total_income_chf': total_income,
                'by_source': income_by_source,
                **income_tax_calc
            },
            'capital_gains': capital_gains,
            'fx_result': fx_result,
            'costs': costs,
            'foreign_tax': {
                'total_withheld': sum(t.get('amount_chf', 0.0) for t in taxes),
                **foreign_credit
            },
            'tax_liability': net_liability
        }


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    calculator = TaxCalculatorBL()
    
    # Example data
    example_data = {
        'transactions': [
            {'type': 'Stocks', 'proceeds_chf': 1000, 'commission_chf': 5},
            {'type': 'Forex', 'proceeds_chf': 50, 'commission_chf': 0}
        ],
        'dividends': [
            {'symbol': 'AAPL', 'amount_chf': 100, 'type': 'Dividend'},
            {'symbol': 'MSFT', 'amount_chf': 50, 'type': 'Interest'}
        ],
        'taxes': [
            {'amount_chf': 15, 'country': 'US'}
        ],
        'fees': [
            {'amount_chf': 10}
        ],
        'open_positions': [
            {'value_chf': 5000}
        ]
    }
    
    summary = calculator.generate_tax_summary(example_data)
    print(json.dumps(summary, indent=2))
