"""演示：获取除权除息历史记录。"""

import pandas as pd
from xmtdx import TdxClient, Market, XDXR_CATEGORY_NAMES

with TdxClient.from_best_host() as c:
    records = c.get_xdxr_info(Market.SH, "600519")
    df = pd.DataFrame([{
        "日期": f"{r.year}-{r.month:02d}-{r.day:02d}",
        "类型": XDXR_CATEGORY_NAMES.get(r.category, f"未知({r.category})"),
        "每股分红(元)": r.fenhong,
        "送转股比例": r.songzhuangu,
        "配股价": r.peigujia,
        "配股比例": r.peigu,
    } for r in records])
    print(f"贵州茅台 除权除息记录，共 {len(df)} 条:")
    print(df.tail(10).to_string(index=False))
