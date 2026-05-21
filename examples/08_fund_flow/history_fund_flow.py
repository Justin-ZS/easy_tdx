"""演示：获取个股历史日线资金流向序列。"""

import pandas as pd
from xmtdx import TdxClient, Market

with TdxClient.from_best_host() as c:
    flows = c.get_history_fund_flow(Market.SH, "600519", 0, 10)
    df = pd.DataFrame([{
        "日期": f"{f.year}-{f.month:02d}-{f.day:02d}",
        "超大单净流入(亿)": (f.super_in - f.super_out) / 1e8,
        "大单净流入(亿)": (f.large_in - f.large_out) / 1e8,
        "主力净流入(亿)": f.main_net_inflow / 1e8,
    } for f in flows])
    print(f"贵州茅台 历史资金流向，共 {len(df)} 天:")
    print(df.to_string(index=False))
