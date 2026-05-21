"""演示：获取个股 K 线数据。

K 线类别:
  KlineCategory.MIN_1  / MIN_5  / MIN_15 / MIN_30 / MIN_60
  KlineCategory.DAY    / WEEK   / MONTH  / YEAR
"""

import pandas as pd
from xmtdx import TdxClient, Market, KlineCategory

with TdxClient.from_best_host() as c:
    bars = c.get_security_bars(Market.SZ, "002176", KlineCategory.DAY, 0, 100)
    df = pd.DataFrame([{
        "日期": f"{b.year}-{b.month:02d}-{b.day:02d}",
        "开盘": b.open,
        "最高": b.high,
        "最低": b.low,
        "收盘": b.close,
        "成交量": b.vol,
        "成交额": b.amount,
    } for b in reversed(bars)])
    print("上证指数 日K线:")
    print(df.to_string(index=False))
