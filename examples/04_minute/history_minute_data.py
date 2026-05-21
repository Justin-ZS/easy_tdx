"""演示：获取历史某日分时数据。date 参数为 YYYYMMDD 格式的整数。"""

import pandas as pd
from xmtdx import TdxClient, Market

with TdxClient.from_best_host() as c:
    date = 20250110
    bars = c.get_history_minute_time_data(Market.SH, "600000", date)
    df = pd.DataFrame([{
        "序号": i + 1,
        "价格": bar.price,
        "成交量": bar.vol,
    } for i, bar in enumerate(bars)])
    print(f"浦发银行 {date} 分时数据，共 {len(df)} 条:")
    print(df.to_string(index=False))
