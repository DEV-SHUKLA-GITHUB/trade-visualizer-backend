import pandas as pd
from jugaad_trader import Zerodha
kite = Zerodha()
instruments = pd.DataFrame(kite.instruments())
print(instruments)
print(set(instruments[(instruments['segment'] =='NFO-OPT') & (instruments['name'] =='NIFTY')].expiry))