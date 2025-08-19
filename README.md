# GZ_FDN_EMS

## Code Grave
1、tracemalloc.start() 为什么需要手动调用
```python
# todo: 这个不能默认开启吗？
import tracemalloc

tracemalloc.start()
```

2、pandas 之截断到小数点后X位
```python
# beginregion 截断到小数点后X位
# 仅选择数值列（float或int）
numeric_cols = raw_details.select_dtypes(include=["float64", "int64"]).columns
_decimals = 7 # 暂时的，目前的数据太小了
raw_details[numeric_cols] = (np.trunc(raw_details[numeric_cols] * 10 ** _decimals)) / 10 ** _decimals
# endregion
```

3、线路负载详情 最初版
```python
with ui.card().classes("w-full min-h-64"):
    ui.label("线路负载详情").classes("text-base font-bold mt-2 mb-2")
    for line in line_details:
        with ui.row().classes("items-center justify-between mb-2"):
            ui.label(f"{line["name"]} ({line["from"]} → {line["to"]})").classes("w-1/4")
            ui.label(f"负载率: {line["loading"]:.2f} %").classes("w-1/4")
            ui.label(f"功率: {line["power"]} MW").classes("w-1/4")
            ui.label(f"电流: {line["current"]} A").classes("w-1/4")
            # math.trunc + 缩放，先放大100倍截断，再缩小，实现保留 2 位小数
            ui.linear_progress(value=math.trunc(line["loading"] / 100.0 * 100) / 100).classes("w-full mt-1")
```