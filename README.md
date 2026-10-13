# pump.fun 每小时毕业代币看板
统计每小时内盘打满（毕业）的 pump.fun 代币数量及其 ATH 市值（UTC+7）。
数据：pump.fun frontend-api-v3（代币、ATH/当前市值）+ GeckoTerminal（PumpSwap 建池时间=毕业时间）。
更新：`python3 fetch.py && python3 build.py`，页面在 `public/index.html`。
限制：pump.fun 接口非官方，单次最多翻 1000 条；历史靠多次运行累积，最多保留 7 天。
