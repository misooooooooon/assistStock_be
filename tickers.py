# Top Market Cap Stocks for KR and US
# KR: KOSPI & KOSDAQ Top 50+
# US: S&P 100 / Nasdaq 100 Top 50+

KR_TICKERS = [
    "005930.KS", # Samsung Elec
    "000660.KS", # SK Hynix
    "373220.KS", # LG Energy Solution
    "207940.KS", # Samsung Biologics
    "005380.KS", # Hyundai Motor
    "000270.KS", # Kia
    "005490.KS", # POSCO Holdings
    "068270.KS", # Celltrion
    "035420.KS", # NAVER
    "051910.KS", # LG Chem
    "003550.KS", # LG Corp
    "035720.KS", # Kakao
    "006400.KS", # Samsung SDI
    "105560.KS", # KB Financial
    "055550.KS", # Shinhan Financial
    "028260.KS", # Samsung C&T
    "015760.KS", # KEPCO
    "032830.KS", # Samsung Life
    "086790.KS", # Hana Financial
    "012330.KS", # Hyundai Mobis
    "000810.KS", # Samsung Fire & Marine
    "032640.KS", # LG Uplus
    "017670.KS", # SK Telecom
    "018260.KS", # Samsung SDS
    "096770.KS", # SK Innovation
    "010130.KS", # Korea Zinc
    "009540.KS", # HD Korea Shipbuilding
    "011200.KS", # HMM
    "010950.KS", # S-Oil
    "003490.KS", # Korean Air
    "034020.KS", # Doosan Enerbility
    "009150.KS", # Samsung Electro-Mechanics
    "030200.KS", # KT
    "034730.KS", # SK inc
    "005935.KS", # Samsung Elec Pref
    "033780.KS", # KT&G
    "088350.KS", # Hanwha Life
    "326030.KS", # SK Bioscience
    "251270.KS", # Netmarble
    "036570.KS", # NCSoft
    "247540.KQ", # Ecopro BM
    "086520.KQ", # Ecopro
    "091990.KQ", # Celltrion Pharm
    "022100.KQ", # POSCO DX
    "035900.KQ", # JYP Ent
    "122870.KQ", # YG PLUS
    "041510.KQ", # SM Ent
    "052690.KQ", # Hanmi Semiconductor
    "028300.KQ", # HLB
    "293490.KQ"  # Kakao Games
]

US_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK-B", "UNH", "JNJ",
    "XOM", "V", "PG", "JPM", "MA", "HD", "CVX", "LLY", "ABBV", "PEP",
    "MRK", "KO", "AVGO", "COST", "TMO", "MCD", "CSCO", "ACN", "ABT", "DHR",
    "WMT", "LIN", "PFE", "NKE", "TXN", "DIS", "PM", "NEE", "ORCL", "BMY",
    "AMD", "NFLX", "QCOM", "UNP", "CAT", "BA", "IBM", "GE", "HON", "AMGN",
    "SPGI", "RTX", "INTC", "SBUX", "LOW", "DE", "EL", "GS", "PLD", "BLK",
    "MS", "BKNG", "INTU", "GILD", "ADP", "ISRG", "MDLZ", "TJX", "AXP", "CVS",
    "SCHW", "MMC", "ADI", "AMT", "LMT", "C", "CI", "TMUS", "PYPL", "MO",
    "CB", "REGN", "VRTX", "SO", "EOG", "PGR", "SLB", "BDX", "ZTS", "BSX",
    "AON", "CL", "ITW", "ATVI", "EQIX", "APD", "BSX", "KLAC", "SNPS", "ICE"
]

def get_tickers(market="KR"):
    if market == "KR":
        return KR_TICKERS
    return US_TICKERS
