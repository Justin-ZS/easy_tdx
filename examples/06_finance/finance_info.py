"""演示：获取最新财务数据。"""

import pandas as pd
from xmtdx import TdxClient, Market

with TdxClient.from_best_host() as c:
    info = c.get_finance_info(Market.SH, "600519")
    df = pd.DataFrame([
        {"项目": "总股本(万股)", "数值": info.zong_guben},
        {"项目": "流通股本(万股)", "数值": info.liutong_guben},
        {"项目": "每股净资产", "数值": info.meigujing_zichan},
        {"项目": "净利润(元)", "数值": info.jing_lirun},
        {"项目": "主营收入(元)", "数值": info.zhuying_shouru},
        {"项目": "主营利润(元)", "数值": info.zhuying_lirun},
        {"项目": "净资产(元)", "数值": info.jing_zichan},
        {"项目": "总资产(元)", "数值": info.zong_zichan},
        {"项目": "股东人数", "数值": info.gudong_renshu},
        {"项目": "上市日期", "数值": info.ipo_date},
    ])
    print("贵州茅台 最新财务数据:")
    print(df.to_string(index=False, formatters={"数值": lambda x: f"{x:,.0f}"}))
