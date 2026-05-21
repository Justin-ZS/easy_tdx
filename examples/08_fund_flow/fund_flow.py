"""演示：获取个股当日资金流向（基于 L1 逐笔数据统计）。

资金分为四级: 超大(>100万)、大(20-100万)、中(4-20万)、小(<4万)。
"""

import pandas as pd
from xmtdx import TdxClient, Market

with TdxClient.from_best_host() as c:
    flow = c.get_fund_flow(Market.SH, "600519")
    df = pd.DataFrame([
        {"级别": "超大单", "流入(亿)": flow.super_in / 1e8, "流出(亿)": flow.super_out / 1e8},
        {"级别": "大单",   "流入(亿)": flow.large_in / 1e8, "流出(亿)": flow.large_out / 1e8},
        {"级别": "中单",   "流入(亿)": flow.medium_in / 1e8, "流出(亿)": flow.medium_out / 1e8},
        {"级别": "小单",   "流入(亿)": flow.small_in / 1e8, "流出(亿)": flow.small_out / 1e8},
    ])
    df["净流入(亿)"] = df["流入(亿)"] - df["流出(亿)"]
    print("贵州茅台 当日资金流向:")
    print(df.to_string(index=False))
