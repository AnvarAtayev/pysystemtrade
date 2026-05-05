from sysdata.csv.csv_adjusted_prices import csvFuturesAdjustedPricesData

data = csvFuturesAdjustedPricesData()
instruments = data.get_list_of_instruments()  # 252 instruments
instrument = 'GOLD'
prices = data.get_adjusted_prices(instrument)