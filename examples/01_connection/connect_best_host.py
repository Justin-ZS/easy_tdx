"""演示：自动从候选服务器中选延迟最低的建立连接。"""

from xmtdx import TdxClient, Market

# 方式一：手动指定服务器
with TdxClient("180.153.18.170") as c:
    print(f"已连接到 {c._host}:{c._port}")

# 方式二：自动优选最低延迟服务器
with TdxClient.from_best_host() as c:
    print(f"已自动选择最优服务器: {c._host}:{c._port}")
    count = c.get_security_count(Market.SH)
    print(f"沪市证券总数: {count}")
