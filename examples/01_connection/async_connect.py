"""演示：异步客户端连接与基本用法。"""

import asyncio
from xmtdx import AsyncTdxClient, Market, KlineCategory


async def main():
    # 手动指定服务器
    async with AsyncTdxClient("180.153.18.170") as c:
        count = await c.get_security_count(Market.SH)
        print(f"沪市证券总数: {count}")

    # 自动优选服务器
    async with AsyncTdxClient.from_best_host() as c:
        bars = await c.get_security_bars(
            Market.SH, "600000", KlineCategory.DAY, 0, 5
        )
        for bar in bars:
            print(f"{bar.year}-{bar.month:02d}-{bar.day:02d} "
                  f"开:{bar.open:.2f} 高:{bar.high:.2f} "
                  f"低:{bar.low:.2f} 收:{bar.close:.2f}")


asyncio.run(main())
