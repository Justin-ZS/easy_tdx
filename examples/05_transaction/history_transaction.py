"""演示：获取历史逐笔成交数据。date 参数为 YYYYMMDD 格式的整数。"""

import pandas as pd
from xmtdx import TdxClient, Market

with TdxClient.from_best_host() as c:
    date = 20250110
    records = c.get_history_transaction_data(Market.SH, "600000", date, 0, 20)
    df = pd.DataFrame([{
        "时间": f"{r.hour:02d}:{r.minute:02d}",
        "成交价": r.price,
        "成交量": r.vol,
        "方向": "买" if r.buyorsell == 0 else "卖",
    } for r in records])
    print(f"浦发银行 {date} 最近 {len(df)} 笔成交:")
    print(df.to_string(index=False))
