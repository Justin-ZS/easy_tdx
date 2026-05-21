"""演示：测量多台通达信服务器延迟并排序。"""

import pandas as pd
from xmtdx import TdxClient

results = TdxClient.ping_all()
df = pd.DataFrame(results, columns=["服务器", "延迟(s)"])
df["延迟(ms)"] = df["延迟(s)"] * 1000
print(df[["服务器", "延迟(ms)"]].to_string(index=False))
