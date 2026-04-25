# https://quantpedia.com/strategies/accrual-anomaly/
#
# The investment universe consists of all stocks on NYSE, AMEX, and NASDAQ. Balance sheet based accruals (the non-cash component of
# earnings) are calculated as: BS_ACC = ( ∆CA – ∆Cash) – ( ∆CL – ∆STD – ∆ITP) – Dep
# Where:
# ∆CA = annual change in current assets
# ∆Cash = change in cash and cash equivalents
# ∆CL = change in current liabilities
# ∆STD = change in debt included in current liabilities
# ∆ITP = change in income taxes payable
# Dep = annual depreciation and amortization expense
# Stocks are then sorted into deciles and investor goes long stocks with the lowest accruals and short stocks with the highest accruals. 
# The portfolio is rebalanced yearly during May (after all companies publish their earnings).
#
# Personal note: Increased coarse_count from 1000 to 1500 to capture more mid-cap stocks and
# reduce the chance of missing candidates with low accruals that fall outside the top 1000 by volume.
#
# Personal note 2: Changed leverage from 5 to 3 to reduce margin risk during volatile periods.
# The original leverage of 5 felt aggressive for a long/short strategy with annual rebalancing.

from AlgorithmImports import *

class AccrualAnomaly(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2006, 1, 1)
        self.SetCash(100000)
        
        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol

        # Increased from 1000 to 1500 to broaden the selection universe
        self.coarse_count = 1500
        
        self.long = []
        self.short = []
        
        # Latest accruals data.
        self.accrual_data = {}
        
        self.selection_flag = False
        self.UniverseSettings.Resolution = Resolution.Daily
        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
        self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)

    def OnSecuritiesChanged(self, changes):
        for security in changes.AddedSecurities:
            security.SetFeeModel(CustomFeeModel())
            # Reduced from 5 to 3 to limit margin exposure on annual-rebalance long/short book
            security.SetLeverage(3)

        for security in changes.RemovedSecurities:
            symbol = security.Symbol
            if symbol in self.accrual_data:
                del self.accrual_data[symbol]
                
    def CoarseSelectionFunction(self, coarse):
        if not self.selection_flag:
            return Universe.Unchanged
        
        # selected = [x.Symbol for x in coarse if x.HasFundamentalData and x.Market == 'usa']
        selected = [x.Symbol
            for x in sorted([x for x in coarse if x.HasFundamentalData and x.Market == 'usa'],
                key = lambda x: x.DollarVolume, reverse = True)[:self.coarse_count]]
        
        return selected
    
    def FineSelectionFunction(self, fine):
        fine = [x for x in fine if (float(x.FinancialStatements.BalanceSheet.CurrentAssets.TwelveMonths) != 0) 
                                and (float(x.FinancialStatements.BalanceSheet.CashAndCashEquivalents.TwelveMonths) != 0)
                                and (float(x.FinancialStatements.BalanceSheet.CurrentLiabilities.TwelveMonth