"""演示：获取板块信息（行业、概念、风格）。

常用板块文件:
  'block_zs.dat' - 行业/指数板块
  'block_gn.dat' - 概念板块
  'block_fg.dat' - 风格板块
"""

import pandas as pd
from xmtdx import TdxClient

with TdxClient.from_best_host() as c:
    blocks = c.get_block_info("block_gn.dat")
    df = pd.DataFrame([{
        "板块名称": b.name,
        "分类": b.category,
        "成分股数": b.count,
        "代码(前5)": ", ".join(b.codes[:5]),
    } for b in blocks])
    print(f"概念板块，共 {len(df)} 个:")
    print(df.head(20).to_string(index=False))
