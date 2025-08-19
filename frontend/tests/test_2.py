import pyecharts.options as opts
from pyecharts.charts import Line
from pyecharts.faker import Faker

c = (
    Line()
    .add_xaxis(Faker.choose())
    .add_yaxis("商家A", Faker.values(), areastyle_opts=opts.AreaStyleOpts(opacity=0.5))
    .add_yaxis("商家B", Faker.values(), areastyle_opts=opts.AreaStyleOpts(opacity=0.5))
    .set_global_opts(title_opts=opts.TitleOpts(title="Line-面积图"))
    .render("line_area_style.html")
)


# 最简单的面积图，目前想用渐变色的面积图，加入JsCode定义渐变。

from pyecharts.charts import Line
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode

x_data = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
y_data = [120, 200, 150, 80, 70, 110, 130]

line = (
    Line()
    .add_xaxis(x_data)
    .add_yaxis(
        "示例",
        y_data,
        is_smooth=True,
        areastyle_opts=opts.AreaStyleOpts(
            color=JsCode(
                """new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    {offset: 0, color: 'rgba(255, 0, 0, 0.6)'},   // 顶部颜色
                    {offset: 1, color: 'rgba(255, 255, 0, 0.1)'}  // 底部颜色
                ])"""
            ),
            opacity=1,
        ),
    )
    .set_global_opts(title_opts=opts.TitleOpts(title="Line 渐变色面积图"))
)

line.render("line_gradient.html")
