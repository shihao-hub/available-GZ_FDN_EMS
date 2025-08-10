## 🤖 Assistant

在 NiceGUI 中，`app.on_connect` 是一个事件监听器，用于在客户端连接时执行代码。如果你想在 `app.on_connect` 中执行 JavaScript（如 `ui.run_javascript`），需要注意 **`ui.run_javascript` 是异步的**，并且需要确保 **客户端已经加载完毕**。

---

## **1. 基本方法：在 `app.on_connect` 里调用 `ui.run_javascript`**
由于 `ui.run_javascript` 需要等待客户端连接完成，你可以直接使用它，但必须确保在 **异步上下文（`async`）** 中调用：
```python
from nicegui import ui

app = ui.run(title="My App")  # 初始化 NiceGUI

@app.on_connect
async def on_connect():
    await ui.run_javascript("console.log('Client connected!');")

ui.label("Hello, NiceGUI!")
app.run()
```
**关键点**：
- `app.on_connect` 必须声明为 `async`，因为 `ui.run_javascript` 是异步的。
- 使用 `await` 确保 JS 代码执行完成。

---

## **2. 检查客户端是否已加载**
如果你希望在 **客户端完全加载后** 再执行 JS（例如操作 DOM），可以结合 `ui.timer` 或 `ui.on()`：
```python
from nicegui import ui

app = ui.run(title="My App")

@app.on_connect
async def on_connect():
    # 等待客户端完全加载
    ui.timer(0.1, once=True, callback=lambda: ui.run_javascript(
        "console.log('DOM fully loaded!');"
    ))

ui.label("Hello, NiceGUI!")
app.run()
```
**说明**：
- `ui.timer(0.1, once=True)` 会在 0.1 秒后执行一次（模拟 `DOMContentLoaded`）。
- 这样可以避免 JS 代码在 DOM 未加载时报错。

---

## **3. 动态修改页面标题（示例）**
如果你想在客户端连接时修改页面标题：
```python
from nicegui import ui

app = ui.run(title="Initial Title")

@app.on_connect
async def on_connect():
    await ui.run_javascript("document.title = 'New Title';")

ui.label("Welcome!")
app.run()
```
**效果**：
- 初始标题是 `"Initial Title"`。
- 客户端连接后，标题变为 `"New Title"`。

---

## **4. 更安全的做法：使用 `ui.add_head_html`**
如果只是想 **在页面加载时运行 JS**（而不是等待 `on_connect`），可以直接注入 JS：
```python
from nicegui import ui

ui.add_head_html("""
<script>
    document.addEventListener('DOMContentLoaded', () => {
        console.log('Page loaded!');
        document.title = "Dynamic Title";
    });
</script>
""")

ui.label("Hello, NiceGUI!")
ui.run()
```
**优点**：
- 无需等待 `on_connect`，JS 会在页面加载时自动执行。
- 适用于 SEO 或静态修改。

---

## **5. 总结**
| 方法 | 适用场景 | 异步支持 | 备注 |
|------|----------|----------|------|
| **`@app.on_connect + ui.run_javascript`** | 客户端连接时执行 JS | ✅ 需要 `async/await` | 适用于动态交互 |
| **`ui.timer` + `ui.run_javascript`** | 确保 DOM 加载完成 | ✅ 延迟执行 | 避免 `document` 未定义 |
| **`ui.add_head_html`** | 页面初始化时运行 JS | ❌ 同步执行 | 适合静态修改 |

### **推荐方案**
- **动态交互** → `@app.on_connect + await ui.run_javascript`（方法1）。
- **确保 DOM 加载** → `ui.timer` + `ui.run_javascript`（方法2）。
- **静态修改（如 SEO）** → `ui.add_head_html`（方法4）。

这样你就可以在 `app.on_connect` 里安全地执行 JavaScript 了！ 🚀
