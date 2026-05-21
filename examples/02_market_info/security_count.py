"""演示：获取市场证券总数。"""

from xmtdx import TdxClient, Market

with TdxClient.from_best_host() as c:
    sh_count = c.get_security_count(Market.SH)
    sz_count = c.get_security_count(Market.SZ)
    print(f"沪市证券总数: {sh_count}")
    print(f"深市证券总数: {sz_count}")
