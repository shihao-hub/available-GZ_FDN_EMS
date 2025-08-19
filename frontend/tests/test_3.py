# 创建图表
bar = (
    Bar(init_opts=opts.InitOpts(
        width="1000px",
        height=f"{dynamic_height}px",
        js_host="https://cdn.jsdelivr.net/npm/echarts@5/dist/"
    ))
    .add_xaxis(short_names)
    # 负载率部分
    .add_yaxis(
        "负载率",
        v_load,
        stack="total",
        category_gap="50%",
        bar_width=16,
        label_opts=opts.LabelOpts(
            position="right",
            formatter=JsCode("function(p){return p.value > 1 ? p.value.toFixed(1)+'%' : '';}"),
            font_size=11,
            color="#333"
        ),
        itemstyle_opts=opts.ItemStyleOpts(
            color=JsCode(
                "new echarts.graphic.LinearGradient(0,0,1,0,["
                "{offset:0,color:'#4caf50'},{offset:0.5,color:'#ffeb3b'},{offset:1,color:'#f44336'}])"
            ),
            border_radius=[9, 0, 0, 9],
        ),
    )
    # 剩余部分
    .add_yaxis(
        "剩余",
        v_rest,
        stack="total",
        category_gap="50%",
        bar_width=16,
        label_opts=opts.LabelOpts(is_show=False),
        itemstyle_opts=opts.ItemStyleOpts(color="#f5f7fa", border_radius=[0, 9, 9, 0]),
    )
    .reversal_axis()
    .set_global_opts(
        title_opts=opts.TitleOpts(
            title="线路负载详情",
            subtitle="节点间负载热力图",
            pos_left="center",
            title_textstyle_opts=opts.TextStyleOpts(font_size=16, font_weight="bold")
        ),
        legend_opts=opts.LegendOpts(is_show=False),
        xaxis_opts=opts.AxisOpts(
            max_=100,
            axislabel_opts=opts.LabelOpts(formatter="{value}%", font_size=10),
            splitline_opts=opts.SplitLineOpts(is_show=True, linestyle_opts=opts.LineStyleOpts(type_="dashed"))
        ),
        yaxis_opts=opts.AxisOpts(
            axislabel_opts=opts.LabelOpts(font_size=11),
            axisline_opts=opts.AxisLineOpts(is_show=False),
            axistick_opts=opts.AxisTickOpts(is_show=False)
        ),
        tooltip_opts=opts.TooltipOpts(
            trigger="item",
            formatter=JsCode(
                """function(params) {
                    var index = params.dataIndex;
                    var fullName = %s[index];
                    var loadVal = %s[index];
                    var restVal = %s[index];

                    return fullName + '<br/>' +
                           '负载率: ' + loadVal.toFixed(1) + '%<br/>' +
                           '剩余: ' + restVal.toFixed(1) + '%<br/>' +
                           '功率: 12.05 MW<br/>' +
                           '电流: 126.7 A';
                }""" % (y_names, v_load, v_rest)
            ),
            # 当节点过多时启用滚动条
            datazoom_opts=[opts.DataZoomOpts(
                type_="inside",
                yaxis_index=0,
                orient="vertical",
                start_value=0,
                end_value=min(15, len(lines) - 1)
            )] if len(lines) > 15 else None
        )
        # 添加网格布局优化
        .set_series_opts(
            emphasis_opts=opts.EmphasisOpts(
                itemstyle_opts=opts.ItemStyleOpts(border_width=2, border_color="#333")
            )
        )
    )
)