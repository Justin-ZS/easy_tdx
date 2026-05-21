"""演示：获取沪深 A 股完整列表（含行业映射）。

展示 SecurityInfo 全部字段（含扩展行业字段）的中文映射。
注意：此方法需要拉取 tdxhy.cfg 并遍历全部证券，耗时较长。
"""

import logging
import pandas as pd
from xmtdx import TdxClient

# 启用日志，查看分页进度
logging.basicConfig(level=logging.INFO, format="%(message)s")

# timeout 调大到 30 秒，避免全量拉取时分页请求超时
with TdxClient.from_best_host(timeout=30.0) as c:
    all_stocks = c.get_security_list_all()

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
        {"英文字段": "industry_tdx",  "中文含义": "通达信行业", "类型": "str",      "说明": "如 T1001，来自 tdxhy.cfg"},
        {"英文字段": "industry_sw",   "中文含义": "申万行业",   "类型": "str",      "说明": "如 X500102，来自 tdxhy.cfg"},
    ])
    print(schema.to_string(index=False))

    # 全字段中文 DataFrame
    print(f"\n沪深 A 股总数: {len(all_stocks)}")
    df = pd.DataFrame([{
        "市场": s.market.name,
        "代码": s.code,
        "名称": s.name,
        "成交量单位(股/手)": s.volunit,
        "价格小数位": s.decimal_point,
        "昨收价": s.pre_close,
        "通达信行业": s.industry_tdx or "",
        "申万行业": s.industry_sw or "",
    } for s in all_stocks])
    print(df.head(20).to_string(index=False))
