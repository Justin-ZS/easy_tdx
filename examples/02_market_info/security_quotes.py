"""演示：批量获取实时五档行情。最多支持 80 只/次。"""

import pandas as pd
from xmtdx import TdxClient, Market

with TdxClient.from_best_host() as c:
    stocks = [
        (Market.SH, "600000"),  # 浦发银行
        (Market.SH, "600519"),  # 贵州茅台
        (Market.SZ, "000001"),  # 平安银行
        (Market.SZ, "000858"),  # 五粮液
    ]
    quotes = c.get_security_quotes(stocks)
    df = pd.DataFrame([{
        "代码": q.code,
        "现价": q.price,
        "涨跌幅%": (q.price - q.pre_close) / q.pre_close * 100,
        "今开": q.open,
        "最高": q.high,
        "最低": q.low,
        "昨收": q.pre_close,
        "成交量(手)": q.vol,
        "成交额": q.amount,
    } for q in quotes])
    print(df.to_string(index=False))
