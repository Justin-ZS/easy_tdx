"""DSL 策略定义模块 (P1 — 骨架)。

v1 提供 @dsl_strategy 装饰器的基本实现。
字符串 DSL 解析器将在后续版本实现。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np

from .strategy import Strategy


def dsl_strategy(func: Callable[..., Any]) -> type[Strategy]:
    """将函数编译为 Strategy 子类。

    函数签名: (df: pd.DataFrame) -> tuple[np.ndarray[bool], np.ndarray[bool]]
    返回 (buy_mask, sell_mask)。

    用法::

        @dsl_strategy
        def dual_ma(df):
            buy = CROSS(MA(df.close, 5), MA(df.close, 20))
            sell = CROSS(MA(df.close, 20), MA(df.close, 5))
            return buy, sell
    """

    class DSLStrategy(Strategy):
        _signal_func = staticmethod(func)
        _buy_mask: np.ndarray | None = None
        _sell_mask: np.ndarray | None = None

        def init(self) -> None:
            pass

        def next(self) -> None:
            if self._buy_mask is None:
                return
            idx = self._bar_index
            if idx < len(self._buy_mask) and self._buy_mask[idx]:
                self.buy(size=0)
            elif idx < len(self._sell_mask) and self._sell_mask[idx]:
                self.sell(size=0)

    DSLStrategy.__name__ = func.__name__
    DSLStrategy.__qualname__ = func.__qualname__
    DSLStrategy._signal_func = func  # type: ignore[attr-defined]

    return DSLStrategy
