"""演示：获取市场证券列表（分页）。

展示 SecurityInfo 全部字段的中文映射与表结构。
"""

import pandas as pd
from xmtdx import TdxClient, Market

with TdxClient.from_best_host() as c:
    stocks = c.get_security_list(Market.SH, start=0)

    # 表结构说明
    print("=" * 70)
    print("SecurityInfo 表结构（字段中英文对照）")
    print("=" * 70)
    schema = pd.DataFrame([
        {"英文字段": "market",        "中文含义": "市场",      "类型": "Market",   "说明": "SZ=深圳 SH=上海 BJ=北京"},
        {"英文字段": "code",          "中文含义": "证券代码",   "类型": "str",      "说明": "6位代码，如 600000"},
        {"英文字段": "name",          "中文含义": "证券名称",   "类型": "str",      "说明": "GBK 解码"},
        {"英文字段": "volunit",       "中文含义": "成交量单位", "类型": "int",      "说明": "1手 = volunit 股"},
        {"英文字段": "decimal_point", "中文含义": "价格小数位", "类型": "int",      "说明": "通常为 2"},
        {"英文字段": "pre_close",     "中文含义": "昨收价",     "类型": "float",    "说明": "通达信自定义浮点"},
        {"英文字段": "industry_tdx",  "中文含义": "通达信行业", "类型": "str",      "说明": "需 get_security_list_all()"},
        {"英文字段": "industry_sw",   "中文含义": "申万行业",   "类型": "str",      "说明": "需 get_security_list_all()"},
    ])
    print(schema.to_string(index=False))

    # 全字段中文 DataFrame
    print(f"\n沪市第 1 页，共 {len(stocks)} 只:")
    df = pd.DataFrame([{
        "市场": s.market.name,
        "代码": s.code,
        "名称": s.name,
        "成交量单位(股/手)": s.volunit,
        "价格小数位": s.decimal_point,
        "昨收价": s.pre_close,
        "通达信行业": s.industry_tdx or "",
        "申万行业": s.industry_sw or "",
    } for s in stocks])
    print(df.head(20).to_string(index=False))
