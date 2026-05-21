"""演示：获取全市场涨跌统计概况。"""

import pandas as pd
from xmtdx import TdxClient

with TdxClient.from_best_host() as c:
    stat = c.get_market_stat()
    df = pd.DataFrame([{
        "上涨": stat.up_count,
        "下跌": stat.down_count,
        "平盘": stat.neutral_count,
        "停牌(估算)": stat.suspended_count,
        "总计": stat.total_count,
        "成交额(亿)": round(stat.total_amount / 1e8, 2),
        "总市值(万亿)": round(stat.total_market_cap / 1e12, 4),
        "涨停": stat.limit_up_count,
        "跌停": stat.limit_down_count,
    }])
    print(df.T.to_string(header=False))
