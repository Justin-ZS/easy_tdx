# easy-tdx MCP Server Plan

## Problem Statement

Agent 需要在已知股票代码或板块代码时，稳定调用 A 股和港股的实时行情、K 线、分时、逐笔、板块和市场异动数据。当前项目已经有 Python SDK 和 `easy-tdx` CLI，但 CLI 对 Agent 来说仍然依赖字符串参数、stdout 解析和人为约定；长期作为工具入口时，参数 schema、错误包装、返回结构和能力说明不够稳定。

项目应新增 MCP server，让 Agent 通过结构化工具调用获得 `easy_tdx` 的实时行情能力，同时保留 CLI 作为人工调试和 fallback 入口。

## Solution

新增独立 MCP 适配层，不改核心协议实现。MCP 层直接 import `easy_tdx` SDK，默认使用 `UnifiedTdxClient` 和 `MacClient` 提供实时行情主路径；需要市场统计等补充能力时使用 `TdxClient`。

第一版只支持 stdio MCP，提供最小可用的实时行情 vertical slice。后续再扩展 Streamable HTTP、鉴权、缓存、限流和连接复用。

Deep module 机会：新增一个稳定的 MCP facade，把以下复杂性收进去：

- `MacClient` / `UnifiedTdxClient` / `TdxClient` 的选择。
- `DataFrame`、时间戳、枚举、NaN 的 JSON-safe 转换。
- 通达信网络错误、协议解析错误、空数据的统一错误包装。
- 工具返回结构的统一 envelope。
- 行数限制、超限错误和大 payload 防护。

Agent 看到的是市场和数据类型命名的业务工具名，不暴露 `MacClient`、`TdxClient`、`tdx` 等内部实现或数据源名。

## User Stories

- 作为 Agent，我可以调用 `a_share_realtime_quotes` 查询一只或多只 A 股实时行情，并得到结构化 JSON。
- 作为 Agent，我可以调用 `a_share_kline_bars` 查询复权或不复权 K 线，用于后续分析。
- 作为 Agent，我可以调用 `a_share_intraday_timeseries` 和 `a_share_trade_ticks` 查询分时和逐笔成交。
- 作为 Agent，我可以调用 `a_share_sector_members`、`a_share_sector_ranking`、`a_share_market_events` 获取板块和市场异动数据。
- 作为 Agent，我可以在已知港股代码时调用港股工具查询报价、K 线和分时。
- 作为 Agent，我可以调用 `a_share_technical_indicators` 获取指定 A 股 K 线指标结果，而不用手动串联 K 线拉取和指标计算。
- 作为 Agent，我可以调用 `a_share_market_analysis` 一次获取报价、K 线尾部和常用技术指标，用于回答“最近走势怎么样”这类自然语言问题。
- 作为使用者，我仍然可以用 `easy-tdx` CLI 人工验证同一类行情能力。

## Core User Flow

1. 用户给出明确代码，例如 `SH600519` 或 `HK 00700`。
2. Agent 如果只需要事实行情，调用原始数据工具，例如 `a_share_realtime_quotes` 或 `a_share_kline_bars`。
3. Agent 如果需要派生指标，调用 `technical_indicator_catalog` 确认指标能力，再调用 `a_share_technical_indicators`。
4. Agent 如果面对自然语言分析问题，优先调用 `a_share_market_analysis` 获取报价、K 线尾部和常用指标的分块数据。
5. Agent 自己基于返回数据生成解释，但不得把 MCP 返回内容表述为投资建议。
6. 工具遇到代码歧义、行数超限、网络异常或指标参数错误时，返回统一 error envelope；Agent 根据 `error.code` 调整输入或向用户说明限制。

## Implementation Decisions

- 新增 MCP 层，优先命名为 `easy_tdx.mcp`，不改 `commands`、`codec`、`transport` 的协议实现。
- 新增命令入口 `easy-tdx-mcp`，通过 optional dependency 安装 `fastmcp`。
- 第一版 MCP transport 只做 stdio，便于 Claude/Codex/本地 Agent 配置和调试。
- MCP server 使用 FastMCP；FastMCP 装饰器层只负责工具注册，业务逻辑集中在 facade，便于测试和未来替换 SDK。
- MCP 工具直接调用 SDK，不通过 shell 执行 CLI。
- 第一版工具使用短连接生命周期：每个工具调用内创建 client、执行、关闭，优先稳定和易排障；连接池作为后续优化。
- 工具名使用市场 + 数据类型语义，例如 `a_share_realtime_quotes`、`a_share_kline_bars`、`hk_realtime_quotes`，不使用 `tdx_*` 或 `mac_*`，避免把数据源/协议名暴露给 Agent。
- 默认实时行情路径使用 `MacClient` 或 `UnifiedTdxClient`；标准协议能力保留 `TdxClient` 作为补充层，不删除。
- 第一版覆盖 A 股和港股；美股、期货、期权、外汇、外盘等其他扩展市场放后续阶段。
- 第一版不提供名称/code 搜索和 symbol 列表工具；Agent 可通过联网搜索、其他 MCP 或用户输入获得明确代码。
- 所有工具返回统一 envelope：`ok`、`source`、`query`、`count`、`rows` 或 `data`、`error`。
- 时间列统一转 ISO 字符串，NaN/NaT 转 `null`，枚举参数接受稳定字符串并在 facade 内转换。
- A 股工具推荐使用结构化输入：`market=SH|SZ|BJ`、`code=600519`；兼容 `SH600519`、`SZ000001`。不对裸代码自动猜市场，无法确认市场时返回 `SYMBOL_AMBIGUOUS`。
- 港股工具推荐使用结构化输入：`market=HK_MAIN_BOARD|HK_GEM|HK_INDEX|HK_FUND`、`code=00700`。兼容 `HK 00700` 和裸 `00700`，默认解释为 `HK_MAIN_BOARD`；创业板、指数、基金等需显式 market。
- rows 型工具默认返回 200 行，单次最大 1000 行；底层协议上限更低的工具使用更低上限。
- 报价工具每次最多 80 只；板块排行默认 top 30、最大 top 100；市场异动默认 100、最大 600；多日分时最多 5 天。
- 超过最大限制时返回明确的 `LIMIT_EXCEEDED` 错误，不静默截断。
- 第一版不做投资建议、不做策略推荐，不封装缠论，只提供实时数据获取。
- 技术指标作为后续阶段加入，MCP 层只负责拉取 K 线和调用纯计算层，不新增指标算法到 MCP 层。
- 技术指标不按每个指标拆 tool；使用少量通用工具承载指标 catalog 和计算，避免工具爆炸。
- 技术指标第一批默认推荐 `MACD`、`KDJ`、`RSI`、`BOLL`、`ATR`、`CCI`、`OBV`、`BIAS`；同时补齐 `MA` / `EMA` 这类均线基础指标。
- 自定义或策略意味较强的指标，例如 `ZHUOYAO`、`BIAS_SIGNAL`，可以出现在 catalog 中，但不作为 MCP 默认推荐组合。
- 面向 Agent 的工具分三层：原始数据工具保持纯行情；技术指标工具负责派生计算；聚合分析工具一次返回报价、K 线尾部和常用指标，方便回答自然语言分析问题。
- 聚合分析工具只组织数据和元信息，不输出买卖建议，不把指标包装成策略结论。

## Testing Decisions

- 单元测试不触网，用 monkeypatch/fake client 覆盖 MCP facade、参数转换、JSON-safe 转换和错误包装。
- MCP 工具注册测试验证工具名、参数默认值和返回 envelope。
- 保留现有离线协议 fixture 测试，新增 MCP 测试不得依赖真实通达信服务器。
- CLI 不作为 MCP 的依赖路径，但可作为人工 smoke test 对照。
- 集成测试如需真实网络，继续使用显式开关跳过默认执行。

## Out of Scope

- 不删除或重构 `TdxClient`。
- 不实现交易、下单、账户、持仓能力。
- 不把 `ashare-mcp`、akshare、baostock、tushare 合并进本项目第一版。
- 不在第一版支持美股、期货、期权、外汇、外盘等非港股扩展市场。
- 不在第一版提供名称搜索、代码搜索或 symbol 列表。
- 不在第一版提供缠论、买卖点、背驰等技术分析工具。
- 不在第一版提供技术指标 MCP 工具；技术指标放在实时数据 vertical slice 稳定后的后续阶段。
- 不在第一版提供财务、F10、公告、研报等研究数据工具。
- 不在第一版实现持久连接池、服务端缓存、鉴权、多租户配置和 HTTP/Streamable HTTP 部署。
- 不保证行情数据可用于生产交易决策；只提供数据访问和分析工具。

## Open Questions

None

## Step 1: MCP Tool Skeleton

### Goal

用户可以运行 `easy-tdx-mcp` 启动 MCP server，并在 Agent 里看到第一批工具定义。

### Slice

新增 MCP package、FastMCP server 入口和工具注册。实现一个不触网的 `service_health` 工具，返回包版本、可用客户端类型和运行模式。同步更新 packaging 配置和最小 README 说明。

这个 slice 建立 MCP 外壳和工具命名约定，不接入真实行情。

### Verify

- `easy-tdx-mcp` 可以启动并注册工具。
- 单元测试验证 `service_health` 返回 JSON-safe envelope。
- `ruff check`、`mypy` 至少覆盖新增 MCP 模块。

### Depends on

None

## Step 2: Quote Vertical Slice

### Goal

Agent 可以调用 `a_share_realtime_quotes` 获取 A 股实时行情。

### Slice

实现参数 schema：`symbols` 支持结构化 market/code 输入，兼容 `["SH600519", "SZ000001"]`。Facade 负责解析 market、拒绝裸代码歧义、创建 `MacClient`、调用报价接口、转换 DataFrame、返回统一 envelope。

同时实现错误包装：无效 market、空 symbol、网络失败、空结果。

### Verify

- fake `MacClient` 返回 DataFrame 时，工具输出包含 `ok=true`、`count`、`rows`。
- 参数解析失败时，返回或抛出明确 MCP 错误。
- 裸 A 股代码无法确认市场时返回 `SYMBOL_AMBIGUOUS`。
- 人工可用 CLI 查询同一 symbol 做对照。

### Depends on

Step 1

## Step 3: Kline Vertical Slice

### Goal

Agent 可以拉取 A 股 K 线。

### Slice

实现 `a_share_kline_bars`。K 线工具使用 `MacClient.get_stock_kline`，支持 period、count、adjust。默认返回 200 行，最大 1000 行，超限返回 `LIMIT_EXCEEDED`。

这个 slice 把 period/adjust 参数转换封装在 facade，避免工具函数里散落枚举转换逻辑。

### Verify

- fake K 线 DataFrame 能转为 JSON-safe rows。
- period/adjust 参数大小写不敏感，未知值给出明确错误。
- count 超过 1000 时返回 `LIMIT_EXCEEDED`。

### Depends on

Step 2

## Step 4: Intraday And Transactions Vertical Slice

### Goal

Agent 可以查询分时和逐笔成交，支持盘中实时分析。

### Slice

实现 `a_share_intraday_timeseries` 和 `a_share_trade_ticks`。底层使用 `MacClient.get_tick_chart`、`get_tick_charts`、`get_transactions`。工具参数支持 date、days、start、count，并在 facade 中限制最大 count。

### Verify

- fake 分时和逐笔 DataFrame 均能返回稳定 envelope。
- date 参数非法时有清晰错误。
- count 超限时被限制或明确拒绝。

### Depends on

Step 2

## Step 5: Board And Market Monitor Vertical Slice

### Goal

Agent 可以查询板块列表、成分股、板块排行和市场异动。

### Slice

实现 `a_share_sector_list`、`a_share_sector_members`、`a_share_sector_ranking`、`a_share_market_events`。底层用 `MacClient`。工具参数用业务命名：sector_type、sector_symbol、sort_by、top_n，不暴露底层协议枚举细节。

### Verify

- fake sector 数据能按工具返回规范输出。
- sector_type、sort_by 的非法值有明确错误。
- `a_share_sector_ranking` 返回包含排序字段和成分统计字段。

### Depends on

Step 2

## Step 6: Market Snapshot Slice

### Goal

Agent 可以查询 A 股市场统计快照。

### Slice

实现 `a_share_market_snapshot`。底层使用 `TdxClient.get_market_stat()`，工具名保持业务语义。市场统计返回单条 snapshot。

### Verify

- fake `TdxClient` 覆盖市场统计返回路径。
- 现有 `TdxClient` 测试不因 MCP 改造退化。

### Depends on

Step 1

## Step 7: Hong Kong Market Slice

### Goal

Agent 可以在已知港股代码时查询港股市场的报价、K 线和分时。

### Slice

实现 `hk_realtime_quotes`、`hk_kline_bars`、`hk_intraday_timeseries`。底层优先使用 `UnifiedTdxClient` 或 `MacExClient`，市场范围限制在港股相关 `ExMarket`，例如 `HK_MAIN_BOARD`、`HK_GEM`、`HK_FUND`、`HK_INDEX`。裸港股代码默认 `HK_MAIN_BOARD`；创业板、指数、基金等需显式 market。K 线默认返回 200 行，最大 1000 行；港股报价每次最多 80 只。

### Verify

- fake `MacExClient` 验证港股 market 字符串转换和 DataFrame 输出。
- 非港股扩展市场返回明确错误或不暴露入口。
- 裸港股代码按 `HK_MAIN_BOARD` 解析，显式非主板 market 可覆盖默认值。
- 工具文档说明第一版仅支持已知代码查询，不提供港股代码搜索。

### Depends on

Step 2

## Step 8: Packaging And Documentation Slice

### Goal

用户能通过文档完成安装、启动、Agent 配置和本地验证。

### Slice

补充 MCP 安装说明、工具清单、参数示例、返回示例、网络限制和数据免责声明。同步更新 optional dependency、entry point、README 的 MCP 小节。

### Verify

- 新环境执行 `pip install -e ".[mcp,dev]"` 成功。
- `easy-tdx-mcp --help` 或等价启动命令可用。
- 文档中的最小配置可复制运行。

### Depends on

Step 1

## Step 9: Reliability Slice

### Goal

MCP server 在常见网络失败、服务器不可达、接口空结果、Agent 大请求下表现可控。

### Slice

加入统一超时、最大行数、工具级错误分类、可选缓存和简单限流。仍保持短连接默认策略；连接复用只作为可配置优化，不作为默认行为。

### Verify

- 单元测试覆盖超限、超时、空数据、异常转换。
- 默认工具不会返回过大 payload。
- 错误消息包含可操作字段，不泄漏无用 traceback。

### Depends on

Step 2, Step 3, Step 4

## Step 10: Technical Indicator Catalog And A-share Slice

### Goal

Agent 可以在已知 A 股代码时，基于 K 线计算常用技术指标，并能先查询可用指标元数据。

### Slice

新增两个 MCP 工具：

- `technical_indicator_catalog`：返回 `indicator.py` 现有 registry 中的指标元数据，包括 name、description、inputs、outputs、default_params。
- `a_share_technical_indicators`：输入 A 股 symbol 或 market/code、period、count、adjust、indicators、params、keep_ohlcv；内部先拉 K 线，再调用 `compute_indicators()`，最后返回统一 envelope。

指标计算继续复用 `indicator.py` / `MyTT.py` 的纯计算层，MCP facade 只做参数解析、K 线获取、错误包装和 JSON-safe 转换。

第一批默认推荐指标：

- `MACD`：趋势和动能。
- `KDJ`：短线超买超卖。
- `RSI`：相对强弱。
- `BOLL`：波动区间。
- `ATR`：波动率和风险距离。
- `CCI`：价格偏离和趋势强弱。
- `OBV`：量价关系。
- `BIAS`：乖离率。

同时在 `indicator.py` registry 中补齐基础均线：

- `MA`：简单移动平均线。
- `EMA`：指数移动平均线。

`count` 表示最终返回行数，rows 返回上限为 1000。为保证 EMA/MACD 等指标收敛，技术指标工具允许内部多拉 K 线作为 warmup，默认 `warmup_rows = 120`，内部拉取数量使用 `fetch_count = min(max(count + warmup_rows, 200), 1200)`。返回 rows 只保留最后 `count` 行，内部 warmup 数据不直接返回。

指标工具使用两个明确上限：

- `count <= 1000`：最终返回行数上限。
- `fetch_count <= 1200`：内部 K 线拉取上限。

如果未来发现底层服务无法稳定支持 1200 条内部拉取，则把指标工具的 `count` 上限降为 880，并在 metadata 中返回 `warmup_rows = 120`；不允许静默截断。

`params` 使用结构化 dict，例如：

```json
{
  "MACD": {"SHORT": 12, "LONG": 26, "M": 9},
  "RSI": {"N": 14},
  "BOLL": {"N": 20, "P": 2}
}
```

暂不把每个指标拆成独立 MCP tool。`ZHUOYAO`、`BIAS_SIGNAL` 等偏自定义或策略意味较强的指标可以通过 catalog 暴露，但不进入默认推荐组合，也不在工具描述中包装成交易信号。

### Verify

- fake K 线 DataFrame + `compute_indicators()` 输出能返回稳定 envelope。
- `technical_indicator_catalog` 不触网，返回 registry 元数据。
- `a_share_technical_indicators` 能正确转换 market/code、period、adjust、params、keep_ohlcv。
- 未知指标返回 `UNKNOWN_INDICATOR`，非法参数返回 `INVALID_INDICATOR_PARAM`。
- 指标所需输入列缺失时返回 `INDICATOR_INPUT_MISSING`。
- count 超过 1000 或 fetch_count 超过 1200 时返回 `LIMIT_EXCEEDED`。
- 单元测试覆盖 `MACD`、`KDJ`、`RSI`、`BOLL`、`ATR`、`CCI`、`OBV`、`BIAS` 和新增 `MA` / `EMA` 的基本输出列。

### Depends on

Step 3, Step 9

## Step 11: Hong Kong Technical Indicator Slice

### Goal

Agent 可以在已知港股代码时，基于港股 K 线计算同一套常用技术指标。

### Slice

新增 `hk_technical_indicators`。工具 schema 与 `a_share_technical_indicators` 保持一致，但 symbol 解析使用港股规则：裸代码默认 `HK_MAIN_BOARD`，创业板、指数、基金等需显式 market。

底层先调用港股 K 线接口获取 OHLCV，再复用 `compute_indicators()`。不新增新的港股专属指标算法。

### Verify

- fake 港股 K 线 DataFrame 能计算并返回指标列。
- 港股 market 字符串转换和日期/period/adjust 参数校验与现有港股 K 线工具一致。
- 非港股扩展市场不会通过该工具暴露。
- 与 A 股指标工具共享错误 envelope 和行数限制策略。

### Depends on

Step 7, Step 10

## Step 12: A-share Agent Analysis Slice

### Goal

Agent 可以用一次工具调用获得回答自然语言走势问题所需的常见上下文。

### Slice

新增 `a_share_market_analysis`。该工具是面向 Agent 的聚合数据工具，不替代底层原始数据工具。

输入参数：

- `symbol` 或 `market/code`：A 股代码，沿用现有 A 股解析规则。
- `period`：默认 `DAILY`。
- `count`：最终返回 K 线和指标行数，默认 120，最大 1000。
- `adjust`：默认 `QFQ`。
- `indicators`：默认 `["MACD", "KDJ", "RSI", "BOLL", "MA", "EMA"]`。
- `include_quote`：是否包含实时报价，默认 true。
- `include_kline`：是否包含 K 线尾部，默认 true。
- `include_indicators`：是否包含指标，默认 true。
- `params`：指标参数覆盖，使用结构化 dict。

返回结构使用 `data` 分块，而不是把所有列混在单个 rows 中：

```json
{
  "ok": true,
  "source": "easy_tdx",
  "query": {},
  "count": 1,
  "data": {
    "quote": {},
    "kline": {"count": 120, "rows": []},
    "indicators": {"count": 120, "rows": []},
    "metadata": {
      "period": "DAILY",
      "adjust": "QFQ",
      "indicator_params": {},
      "warning": "technical indicators are derived data, not investment advice"
    }
  }
}
```

实现仍只做数据聚合和派生指标计算，不生成“看涨 / 看跌 / 买入 / 卖出”等结论。Agent 可以基于返回数据自行组织解释。

`a_share_kline_bars` 等原始数据工具保持纯行情，不默认附带指标，避免 payload 膨胀和 count 语义混乱。

### Verify

- fake quote + fake K 线 + 指标计算能返回分块 `data`。
- `include_quote`、`include_kline`、`include_indicators` 能独立控制返回块。
- 默认指标包含 `MACD`、`KDJ`、`RSI`、`BOLL`、`MA`、`EMA`。
- 工具返回 metadata warning，且不产生买卖建议字段。
- 聚合工具采用核心块 all-or-nothing、非核心块局部失败：`kline` 是核心块；`indicators` 在 `include_indicators=true` 时是核心块；`quote` 是非核心块。
- 核心块失败时整体 `ok=false`，错误 details 中包含 `block`；只有 quote 失败时整体 `ok=true`，`data.quote=null`，并在 `data.errors` 中记录 `block=quote` 的局部错误。
- count / fetch_count 仍遵守最大行数限制。

### Depends on

Step 2, Step 3, Step 10

## Step 13: Hong Kong Agent Analysis Slice

### Goal

Agent 可以用一次工具调用获得港股报价、K 线尾部和常用技术指标。

### Slice

新增 `hk_market_analysis`。工具 schema 与 `a_share_market_analysis` 保持一致，但 symbol 解析使用港股规则：裸代码默认 `HK_MAIN_BOARD`，创业板、指数、基金等需显式 market。

底层使用港股报价、港股 K 线和 `compute_indicators()`。返回结构同样使用 `data.quote`、`data.kline`、`data.indicators`、`data.metadata` 分块。

### Verify

- fake 港股 quote + K 线能返回分块 `data`。
- 港股 market 字符串转换和 period/adjust 参数校验与现有港股工具一致。
- 非港股扩展市场不会通过该工具暴露。
- 不产生买卖建议字段。

### Depends on

Step 7, Step 11, Step 12
