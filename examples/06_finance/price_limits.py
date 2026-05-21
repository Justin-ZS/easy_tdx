"""演示：计算个股涨跌停价格。"""

import pandas as pd
from xmtdx import TdxClient, Market

CODE = "600519"
NAME = "贵州茅台"

with TdxClient.from_best_host() as c:
    quotes = c.get_security_quotes([(Market.SH, CODE)])
    if quotes:
        q = quotes[0]
        limit_up, limit_down = c.get_price_limits(
            Market.SH, CODE, NAME, q.pre_close
        )
        df = pd.DataFrame([{
            "代码": CODE,
            "名称": NAME,
            "昨收": q.pre_close,
            "涨停价": limit_up,
            "跌停价": limit_down,
        }])
        print(df.to_string(index=False))
