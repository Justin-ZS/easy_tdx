"""演示：获取今日分时数据（240 条）。"""

import pandas as pd
from xmtdx import TdxClient, Market

with TdxClient.from_best_host() as c:
    bars = c.get_minute_time_data(Market.SH, "600000")
    df = pd.DataFrame([{
        "序号": i + 1,
        "价格": bar.price,
        "成交量": bar.vol,
    } for i, bar in enumerate(bars)])
    print(f"浦发银行今日分时，共 {len(df)} 条:")
    print(df.to_string(index=False))
