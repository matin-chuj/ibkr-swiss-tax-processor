"""
KROK B: Tax Calculator for Basel-Landschaft Canton
Calculates taxes according to Basel-Landschaft rules for 2025
"""

import logging
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class BaselLandschaftTaxCalculator:
    """Tax calculator for Basel-Landschaft canton"""
    
    # Basel-Landschaft tax rates (2025)
    INCOME_TAX_RATE = 0.1055  # 10.55% income tax rate
    WEALTH_TAX_RATE = 0.0008  # 0.08% wealth tax rate
    WEALTH_TAX_EXEMPTION = 50000.0  # CHF 50,000 exemption
    
    # FX rates (can be updated via API or manual input)
    DEFAULT_FX_RATES = {
        'CHF': 1.0,
        'EUR': 0.93324,
        'USD': 0.79959,
        'JPY': 0.0051507,
        'NOK': 0.07952,
        'PLN': 0.22084,
        'SEK': 0.085358,
    }
    
    def __init__(self, parser_data: Dict, fx_rates: Dict = None, tax_year: int = 2025):
        self.parser_data = parser_data
        self.fx_rates = fx_rates or self.DEFAULT_FX_RATES
        self.tax_year = tax_year
        
        # Results containers
        self.assets = {}
        self.income = {}
        self.capital_gains = {}
        self.expenses = {}
        self.tax_summary = {}
        
    def calculate_all(self):
        """Calculate all tax components"""
        logger.info("🧮 Calculating Basel-Landschaft taxes...")
        
        self._calculate_assets()
        self._calculate_income()
        self._calculate_capital_gains()
        self._calculate_expenses()
        self._calculate_tax_summary()
        
        logger.info("✅ Tax calculations complete")
        
    def _convert_to_chf(self, amount: float, currency: str) -> float:
        """Convert amount to CHF"""
        if currency == 'CHF':
            return amount
        rate = self.fx_rates.get(currency, 1.0)
        return amount * rate
    
    def _calculate_assets(self):
        """Calculate total assets (for wealth tax)"""
        logger.info("📊 Calculating assets...")
        
        # Open positions value
        stocks_value = 0.0
        stocks_detail = []
        
        for pos in self.parser_data.get('open_positions', []):
            value_chf = self._convert_to_chf(pos['value'], pos['currency'])
            stocks_value += value_chf
            stocks_detail.append({
                'symbol': pos['symbol'],
                'quantity': pos['quantity'],
                'value_chf': value_chf,
                'unrealized_pl': pos['unrealized_pl'],
            })
        
        # Cash balances
        cash_value = 0.0
        cash_detail = []
        
        for cash in self.parser_data.get('cash_balances', []):
            value_chf = self._convert_to_chf(cash['amount'], cash['currency'])
            cash_value += value_chf
            cash_detail.append({
                'currency': cash['currency'],
                'amount': cash['amount'],
                'value_chf': value_chf,
            })
        
        total_assets = stocks_value + cash_value
        
        self.assets = {
            'stocks_value': stocks_value,
            'stocks_detail': stocks_detail,
            'cash_value': cash_value,
            'cash_detail': cash_detail,
            'total_assets': total_assets,
        }
        
        logger.info(f"   Stocks: CHF {stocks_value:,.2f}")
        logger.info(f"   Cash: CHF {cash_value:,.2f}")
        logger.info(f"   Total: CHF {total_assets:,.2f}")
    
    def _calculate_income(self):
        """Calculate taxable income"""
        logger.info("💰 Calculating income...")
        
        # Dividends
        total_dividends = 0.0
        dividends_detail = []
        
        for div in self.parser_data.get('dividends', []):
            amount_chf = self._convert_to_chf(div['amount'], div['currency'])
            total_dividends += amount_chf
            dividends_detail.append({
                'date': div['date'],
                'description': div.get('description', ''),
                'currency': div['currency'],
                'amount': div['amount'],
                'amount_chf': amount_chf,
            })
        
        # Interest
        total_interest = 0.0
        interest_detail = []
        
        for int_item in self.parser_data.get('interest', []):
            amount_chf = self._convert_to_chf(int_item['amount'], int_item['currency'])
            total_interest += amount_chf
            interest_detail.append({
                'date': int_item['date'],
                'description': int_item.get('description', ''),
                'currency': int_item['currency'],
                'amount': int_item['amount'],
                'amount_chf': amount_chf,
            })
        
        # Securities Lending
        total_lending = 0.0
        lending_detail = []
        
        for lending in self.parser_data.get('securities_lending', []):
            amount_chf = self._convert_to_chf(lending['amount'], lending['currency'])
            total_lending += amount_chf
            lending_detail.append({
                'date': lending['date'],
                'description': lending.get('description', ''),
                'currency': lending['currency'],
                'amount': lending['amount'],
                'amount_chf': amount_chf,
            })
        
        # Withholding taxes (negative income)
        total_withholding = 0.0
        withholding_detail = []
        
        for tax in self.parser_data.get('withholding_taxes', []):
            amount_chf = self._convert_to_chf(tax['amount'], tax['currency'])
            total_withholding += amount_chf
            
            # Extract country code from description
            country = self._extract_country_from_description(tax.get('description', ''))
            
            withholding_detail.append({
                'date': tax['date'],
                'description': tax.get('description', ''),
                'currency': tax['currency'],
                'amount': tax['amount'],
                'amount_chf': amount_chf,
                'country': country,
            })
        
        self.income = {
            'dividends_total': total_dividends,
            'dividends_detail': dividends_detail,
            'interest_total': total_interest,
            'interest_detail': interest_detail,
            'securities_lending_total': total_lending,
            'securities_lending_detail': lending_detail,
            'withholding_tax_total': total_withholding,
            'withholding_tax_detail': withholding_detail,
            'gross_investment_income': total_dividends + total_interest + total_lending,
            'net_investment_income': total_dividends + total_interest + total_lending - total_withholding,
        }
        
        logger.info(f"   Dividends: CHF {total_dividends:,.2f}")
        logger.info(f"   Interest: CHF {total_interest:,.2f}")
        logger.info(f"   Securities Lending: CHF {total_lending:,.2f}")
        logger.info(f"   Withholding Tax: CHF -{total_withholding:,.2f}")
    
    def _calculate_capital_gains(self):
        """Calculate capital gains and losses"""
        logger.info("📈 Calculating capital gains...")
        
        # Realized gains from trades
        realized_gains_st = 0.0  # Short-term (< 6 months)
        realized_gains_lt = 0.0  # Long-term (>= 6 months)
        realized_losses_st = 0.0
        realized_losses_lt = 0.0
        
        gains_detail = []
        losses_detail = []
        
        for trade in self.parser_data.get('trades', []):
            realized_pl = trade.get('realized_pl', 0.0)
            realized_pl_chf = self._convert_to_chf(realized_pl, trade['currency'])
            
            # Determine if short or long term (simplified - assumes < 6 months is ST)
            is_short_term = True  # Default to short-term for safety
            
            if realized_pl_chf > 0:
                if is_short_term:
                    realized_gains_st += realized_pl_chf
                else:
                    realized_gains_lt += realized_pl_chf
                    
                gains_detail.append({
                    'date': trade['date_time'],
                    'symbol': trade['symbol'],
                    'quantity': trade['quantity'],
                    'proceeds_chf': self._convert_to_chf(trade['proceeds'], trade['currency']),
                    'gain_chf': realized_pl_chf,
                    'term': 'short' if is_short_term else 'long',
                })
            elif realized_pl_chf < 0:
                if is_short_term:
                    realized_losses_st += abs(realized_pl_chf)
                else:
                    realized_losses_lt += abs(realized_pl_chf)
                    
                losses_detail.append({
                    'date': trade['date_time'],
                    'symbol': trade['symbol'],
                    'quantity': trade['quantity'],
                    'proceeds_chf': self._convert_to_chf(trade['proceeds'], trade['currency']),
                    'loss_chf': abs(realized_pl_chf),
                    'term': 'short' if is_short_term else 'long',
                })
        
        # Unrealized gains from open positions
        unrealized_gains_st = 0.0
        unrealized_gains_lt = 0.0
        unrealized_detail = []
        
        for pos in self.parser_data.get('open_positions', []):
            unrealized_pl = pos.get('unrealized_pl', 0.0)
            unrealized_pl_chf = self._convert_to_chf(unrealized_pl, pos['currency'])
            
            if unrealized_pl_chf > 0:
                # Assume short-term for unrealized
                unrealized_gains_st += unrealized_pl_chf
                
                unrealized_detail.append({
                    'symbol': pos['symbol'],
                    'quantity': pos['quantity'],
                    'unrealized_pl_chf': unrealized_pl_chf,
                })
        
        # Forex gains/losses
        forex_pl_total = 0.0
        forex_detail = []
        
        for forex in self.parser_data.get('forex_transactions', []):
            realized_pl = forex.get('realized_pl', 0.0)
            realized_pl_chf = self._convert_to_chf(realized_pl, forex['currency'])
            forex_pl_total += realized_pl_chf
            
            forex_detail.append({
                'date': forex['date_time'],
                'symbol': forex['symbol'],
                'quantity': forex['quantity'],
                'realized_pl_chf': realized_pl_chf,
            })
        
        net_realized = (realized_gains_st + realized_gains_lt) - (realized_losses_st + realized_losses_lt)
        
        self.capital_gains = {
            'realized_gains_st': realized_gains_st,
            'realized_gains_lt': realized_gains_lt,
            'realized_losses_st': realized_losses_st,
            'realized_losses_lt': realized_losses_lt,
            'net_realized': net_realized,
            'gains_detail': gains_detail,
            'losses_detail': losses_detail,
            'unrealized_gains_st': unrealized_gains_st,
            'unrealized_gains_lt': unrealized_gains_lt,
            'unrealized_detail': unrealized_detail,
            'forex_pl_total': forex_pl_total,
            'forex_detail': forex_detail,
        }
        
        logger.info(f"   Realized Gains (ST): CHF {realized_gains_st:,.2f}")
        logger.info(f"   Realized Gains (LT): CHF {realized_gains_lt:,.2f}")
        logger.info(f"   Realized Losses (ST): CHF -{realized_losses_st:,.2f}")
        logger.info(f"   Realized Losses (LT): CHF -{realized_losses_lt:,.2f}")
        logger.info(f"   Net Realized: CHF {net_realized:,.2f}")
        logger.info(f"   Unrealized (ST): CHF {unrealized_gains_st:,.2f}")
        logger.info(f"   Forex P/L: CHF {forex_pl_total:,.2f}")
    
    def _calculate_expenses(self):
        """Calculate deductible expenses"""
        logger.info("💸 Calculating expenses...")
        
        # Trading commissions
        total_commissions = 0.0
        commissions_detail = []
        
        for trade in self.parser_data.get('trades', []):
            commission = abs(trade.get('commission', 0.0))
            commission_chf = self._convert_to_chf(commission, trade['currency'])
            total_commissions += commission_chf
            
            if commission_chf > 0:
                commissions_detail.append({
                    'date': trade['date_time'],
                    'symbol': trade['symbol'],
                    'commission_chf': commission_chf,
                })
        
        # Other fees
        total_fees = 0.0
        fees_detail = []
        
        for fee in self.parser_data.get('fees', []):
            amount_chf = self._convert_to_chf(fee['amount'], fee['currency'])
            total_fees += amount_chf
            fees_detail.append({
                'date': fee['date'],
                'subtitle': fee.get('subtitle', ''),
                'description': fee.get('description', ''),
                'amount_chf': amount_chf,
            })
        
        total_expenses = total_commissions + total_fees
        
        self.expenses = {
            'commissions_total': total_commissions,
            'commissions_detail': commissions_detail,
            'fees_total': total_fees,
            'fees_detail': fees_detail,
            'total_expenses': total_expenses,
        }
        
        logger.info(f"   Commissions: CHF -{total_commissions:,.2f}")
        logger.info(f"   Other Fees: CHF -{total_fees:,.2f}")
        logger.info(f"   Total: CHF -{total_expenses:,.2f}")
    
    def _calculate_tax_summary(self):
        """Calculate final tax summary for Basel-Landschaft"""
        logger.info("📋 Calculating tax summary...")
        
        # Taxable income = Investment income - Expenses
        # Note: In Basel-Landschaft, capital gains for private investors are NOT taxed
        # Only investment income (dividends, interest) is taxed
        gross_income = self.income['gross_investment_income']
        deductible_expenses = self.expenses['total_expenses']
        taxable_income = max(0, gross_income - deductible_expenses)
        
        # Income tax
        income_tax = taxable_income * self.INCOME_TAX_RATE
        
        # Wealth tax
        taxable_wealth = max(0, self.assets['total_assets'] - self.WEALTH_TAX_EXEMPTION)
        wealth_tax = taxable_wealth * self.WEALTH_TAX_RATE
        
        # Foreign tax credit
        foreign_tax_paid = self.income['withholding_tax_total']
        
        # Foreign tax credit is limited to the portion of Swiss tax attributable to foreign income
        # All investment income is typically foreign, so we use 100% ratio
        # In practice, a tax advisor would calculate this more precisely
        if gross_income > 0:
            # Assume all investment income is foreign-sourced
            foreign_income_ratio = 1.0
        else:
            foreign_income_ratio = 0.0
            
        max_foreign_credit = income_tax * foreign_income_ratio
        foreign_tax_credit = min(foreign_tax_paid, max_foreign_credit)
        
        # Total tax due
        total_tax_before_credit = income_tax + wealth_tax
        total_tax_due = max(0, total_tax_before_credit - foreign_tax_credit)
        
        self.tax_summary = {
            'tax_year': self.tax_year,
            'canton': 'Basel-Landschaft',
            
            # Income components
            'gross_investment_income': gross_income,
            'deductible_expenses': deductible_expenses,
            'taxable_income': taxable_income,
            
            # Wealth components
            'total_assets': self.assets['total_assets'],
            'wealth_exemption': self.WEALTH_TAX_EXEMPTION,
            'taxable_wealth': taxable_wealth,
            
            # Tax calculations
            'income_tax_rate': self.INCOME_TAX_RATE,
            'income_tax': income_tax,
            'wealth_tax_rate': self.WEALTH_TAX_RATE,
            'wealth_tax': wealth_tax,
            'total_tax_before_credit': total_tax_before_credit,
            
            # Foreign tax credit
            'foreign_tax_paid': foreign_tax_paid,
            'foreign_tax_credit': foreign_tax_credit,
            
            # Final tax
            'total_tax_due': total_tax_due,
            
            # Additional info
            'capital_gains_note': 'Capital gains are tax-free for private investors in Basel-Landschaft',
        }
        
        logger.info(f"   Taxable Income: CHF {taxable_income:,.2f}")
        logger.info(f"   Income Tax: CHF {income_tax:,.2f}")
        logger.info(f"   Taxable Wealth: CHF {taxable_wealth:,.2f}")
        logger.info(f"   Wealth Tax: CHF {wealth_tax:,.2f}")
        logger.info(f"   Foreign Tax Credit: CHF -{foreign_tax_credit:,.2f}")
        logger.info(f"   Total Tax Due: CHF {total_tax_due:,.2f}")
    
    def _extract_country_from_description(self, description: str) -> str:
        """Extract country code from tax description"""
        # Common patterns: "US Tax", "DE Tax", etc.
        desc_upper = description.upper()
        
        country_codes = {
            'US': 'United States',
            'DE': 'Germany',
            'NO': 'Norway',
            'GB': 'United Kingdom',
            'FR': 'France',
            'CH': 'Switzerland',
        }
        
        for code, name in country_codes.items():
            if code in desc_upper or name.upper() in desc_upper:
                return code
                
        return 'Unknown'
    
    def get_results(self) -> Dict:
        """Get all calculation results"""
        return {
            'assets': self.assets,
            'income': self.income,
            'capital_gains': self.capital_gains,
            'expenses': self.expenses,
            'tax_summary': self.tax_summary,
        }
