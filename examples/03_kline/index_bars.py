"""演示：获取指数 K 线数据。

常用指数代码:
  上证指数: Market.SH, "000001"
  深证成指: Market.SZ, "399001"
  创业板指: Market.SZ, "399006"
"""

import pandas as pd
from xmtdx import TdxClient, Market, KlineCategory

with TdxClient.from_best_host() as c:
    bars = c.get_index_bars(Market.SH, "999999", KlineCategory.DAY, 0, 10)
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
    fmt = {"成交量": lambda x: f"{x:,.0f}", "成交额": lambda x: f"{x:,.0f}"}
    print(df.to_string(index=False, formatters=fmt))
