import functools
import math
import warnings
from typing import List, Dict, Tuple, Annotated, Iterable

import numpy as np
import pandas as pd
import deprecation
import aiohttp
import anyio
from aiohttp.client import ClientResponse  # 客户端（如爬虫、API 调用），用 aiohttp.client.ClientResponse
from loguru import logger
from lupa.luajit20 import LuaRuntime
from nicegui import ui, app, run

import exceptions
import settings
import typeddicts
import dialogs
import i18n


def locate_item(data: List[Dict], key, value) -> Dict:
    """从 List[Dict] 中定位到目标 Dict"""
    if not hasattr(locate_item, "lua"):
        # 挂载，参考 js。说实在的，动态语言似乎就该这样！虽然可能导致维护困难，但是足够灵活，甚至可以改变自己的思维方式，增加思考维度和角度
        setattr(locate_item, "lua", LuaRuntime())

    lua = getattr(locate_item, "lua")
    # fixme: 使用 lua.eval 是完全没有必要的，单纯练习罢了
    # todo: 找到 python 真的需要调用 lua 的场景！或者说实现出来一个类似 dst 的小型使用，python-引擎层，lua-业务层
    return lua.eval("""\
    function(data, key, value)
        for v in python.iter(data) do
            if v[key] == value then
                return v
            end
        end
        error("未找到对应元素，出错")
    end
    """)(data, key, value)


class RequestUtils:
    """请求相关工具"""


class ResponseUtils:
    """响应相关工具"""

    @staticmethod
    def is_json_content_type(response: ClientResponse):
        return response.content_type == "application/json"


class ApiErrorHandler:
    """接口错误处理工具"""

    @staticmethod
    @deprecation.deprecated(details="设计有误，不推荐使用")
    async def handle_500_error(response: ClientResponse) -> bool:
        """
        处理响应为 500 的错误
        :param response: response
        :return: 处理了错误为 True，否则为 False。目前想到的场景是：链式调用，这个是设计模式的耶。
        """
        if response.status != 500:
            return False
        # 这种错误属于 unexcepted 错误
        #   - 返回体是 json 格式，则 await response.json() 并将其转为表单展示
        #   - 返回体是 text 格式
        await dialogs.show_error_dialog(f"详情：{await response.json()}")
        return True

    @staticmethod
    @deprecation.deprecated(details="设计有误，不推荐使用")
    async def handle_non_200_error(response: ClientResponse) -> bool:
        # 必定需要在末尾被调用才行，所以这设计的不好，显然需要废弃了
        if response.status == 200:
            return False
        # 注意，此处 dialog 似乎不太好吧？返回会交给用户处理比较好吧。而且我发现当某个 dialog 打开后，再触发其他 dialog 似乎不行。
        await dialogs.show_error_dialog(f"详情：{await response.json()}")
        return True


class _AuthManager:
    """管理认证（Authentication）类"""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
            # 以下内容在登录过期（两个场景，一是主动退出登录，二是 token 过期）时，清空
            cls._instance._access_token_key = "_AuthManager:access_token"
            cls._instance._refresh_token_key = "_AuthManager:refresh_token"
            cls._instance._user_info_key = "_AuthManager:user_info"  # 登录时存储用户信息
        return cls._instance

    def debug_tostring(self):
        """用于调试使用，打印储存的信息"""
        return str({
            "access_token": app.storage.user[self._access_token_key],
            "refresh_token": app.storage.user[self._refresh_token_key],
            "user_info": app.storage.user[self._user_info_key],
        })

    def store_user_info(self, user_info: typeddicts.LoginedUserInfo):
        app.storage.user[self._user_info_key] = user_info

    def get_username(self) -> str | None:
        if self._user_info_key not in app.storage.user:
            return None
        return app.storage.user[self._user_info_key].get("username")

    def store_access_token(self, value: str):
        """存储 access_token 到指定位置"""
        # app.storage.browser 不可以，做不到，这个似乎在 ui.page 渲染的时候使用
        # app.storage.browser["access_token"] = value

        # 供参考信息：
        #     在登录成功后设置
        #     app.storage.user.update({
        #         'authenticated': True,
        #         'token': 'your_auth_token',
        #         'user_info': {...}
        #     })

        app.storage.user[self._access_token_key] = value

    def store_refresh_token(self, value: str):
        """存储 refresh_token 到指定位置"""
        app.storage.user[self._refresh_token_key] = value

    def get_access_token(self) -> str | None:
        if self._access_token_key not in app.storage.user:
            return None
        return app.storage.user[self._access_token_key]

    def get_refresh_token(self) -> str | None:
        if self._refresh_token_key not in app.storage.user:
            return None
        return app.storage.user[self._refresh_token_key]

    def remove_token(self) -> str | None:
        logger.debug("[remove_token] self._access_token_key: {}", app.storage.user.get(self._access_token_key))
        logger.debug("[remove_token] self._refresh_token_key: {}", app.storage.user.get(self._refresh_token_key))
        if self._access_token_key in app.storage.user:
            del app.storage.user[self._access_token_key]
        if self._refresh_token_key in app.storage.user:
            del app.storage.user[self._refresh_token_key]

    @deprecation.deprecated(details="使用 self.get_authorization_header 替代")
    def add_auth_header(self, headers: Dict) -> Tuple[bool, Dict]:
        """获得 Authorization header"""
        if self._access_token_key in headers:
            raise exceptions.UnexpectedError("headers 已存在 access_token 键")
        if self._access_token_key not in app.storage.user:
            return False, headers
        access_token = app.storage.user[self._access_token_key]
        headers["Authorization"] = f"Bearer {access_token}"
        return True, headers

    def get_authorization_header(self) -> Tuple[str, str] | None:
        """获得 Authorization header"""
        access_token = self.get_access_token()
        if access_token is None:
            return None
        if settings.DEBUG:
            logger.debug(f"access_token: {access_token}")
        return "Authorization", f"Bearer {access_token}"


auth_manager = _AuthManager()


async def create_common_header():
    """创建通用 html 页面头"""
    # 暂且在此处执行一些通用操作，后续再移出去
    ui.query(".nicegui-content").classes("px-16")

    @app.on_connect
    async def get_title():
        # just for test -> /docs/nicegui获取当前页面的标题.md
        # logger.debug("{}", await ui.run_javascript("return document.title;"))
        pass

    # ------------------------------------------------------------------------ #

    # 渐变颜色（深紫色到浅紫色）
    gradient = "linear-gradient(135deg, rgb(80, 70, 160), rgb(110, 98, 195), rgb(140, 130, 220))"

    # 【知识点】添加自定义CSS样式（非常好，只不过我不懂，系统学习 css 之后应该就不会那么难受了）
    ui.add_head_html(f"""
        <style>
            .gradient-header {{
                background: {gradient};
                color: white;
                /* padding: 1.5rem 2rem; */ /* 参考 tailwind css 的 p */
                /* box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2); */ /* 盒子周围有阴影 */
                /* position: relative; */ /* header 和下方有较长的距离了 */
                overflow: hidden;
                z-index: 1;
            }}

            .gradient-header::before {{
                content: "";
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 70%);
                transform: rotate(30deg);
                z-index: -1;
                pointer-events: none;
            }}
            
            .menu-hover:hover {{
                background: #877dd8 !important;
            }}
        </style>
    """)

    with ui.header().classes("items-center place-items-center").classes("gradient-header"):
        # 标题
        with ui.link(target="/").classes("""
            row gap-4 items-center mr-auto      
            no-underline text-lg text-white font-bold
        """):
            ui.html("""
            <svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M20.317 4.4921C18.7873 3.80147 17.147 3.29265 15.4319 3.00122C15.4007 2.9956 15.3695 3.00965 15.3534 3.03777C15.1424 3.40697 14.9087 3.88862 14.7451 4.26719C12.9004 3.99545 11.0652 3.99545 9.25832 4.26719C9.09465 3.8802 8.85248 3.40697 8.64057 3.03777C8.62449 3.01059 8.59328 2.99654 8.56205 3.00122C6.84791 3.29172 5.20756 3.80054 3.67693 4.4921C3.66368 4.49772 3.65233 4.5071 3.64479 4.51928C0.533392 9.09311 -0.31895 13.5545 0.0991801 17.9606C0.101072 17.9822 0.11337 18.0028 0.130398 18.0159C2.18321 19.4993 4.17171 20.3998 6.12328 20.9967C6.15451 21.0061 6.18761 20.9949 6.20748 20.9695C6.66913 20.3492 7.08064 19.6952 7.43348 19.0073C7.4543 18.967 7.43442 18.9192 7.39186 18.9033C6.73913 18.6597 6.1176 18.3626 5.51973 18.0253C5.47244 17.9981 5.46865 17.9316 5.51216 17.8997C5.63797 17.8069 5.76382 17.7104 5.88396 17.613C5.90569 17.5952 5.93598 17.5914 5.96153 17.6026C9.88928 19.3672 14.1415 19.3672 18.023 17.6026C18.0485 17.5905 18.0788 17.5942 18.1015 17.612C18.2216 17.7095 18.3475 17.8069 18.4742 17.8997C18.5177 17.9316 18.5149 17.9981 18.4676 18.0253C17.8697 18.3692 17.2482 18.6597 16.5945 18.9024C16.552 18.9183 16.533 18.967 16.5538 19.0073C16.9143 19.6942 17.3258 20.3483 17.7789 20.9686C17.7978 20.9949 17.8319 21.0061 17.8631 20.9967C19.8241 20.3998 21.8126 19.4993 23.8654 18.0159C23.8834 18.0028 23.8948 17.9831 23.8967 17.9616C24.3971 12.8676 23.0585 8.4428 20.3482 4.52021C20.3416 4.5071 20.3303 4.49772 20.317 4.4921ZM8.02002 15.2778C6.8375 15.2778 5.86313 14.2095 5.86313 12.8976C5.86313 11.5857 6.8186 10.5175 8.02002 10.5175C9.23087 10.5175 10.1958 11.5951 10.1769 12.8976C10.1769 14.2095 9.22141 15.2778 8.02002 15.2778ZM15.9947 15.2778C14.8123 15.2778 13.8379 14.2095 13.8379 12.8976C13.8379 11.5857 14.7933 10.5175 15.9947 10.5175C17.2056 10.5175 18.1705 11.5951 18.1516 12.8976C18.1516 14.2095 17.2056 15.2778 15.9947 15.2778Z"></path></svg>
            """).classes("fill-white scale-125 m-1")
            ui.label(settings.TITLE)

        # 选项卡
        with ui.row():
            for config in settings.TAB_CONFIGS:
                ui.link(config["name"], target=config["url"]).classes("no-underline text-lg text-white")

        # 设置
        with ui.link().classes("ml-auto mr-4 no-underline text-lg text-white"):
            # 【知识点】一门技术还得是官网，或者比官网更好的博客。比如：nicegui 官网被人按自己理解翻译整理的网站 https://visionz.readthedocs.io/zh-cn/latest/ext/nicegui/intro.html 就很好用，但是如果英语更好，显然**细细且反复**看官网即可。 # noqa
            # todo: 设置菜单
            with ui.icon("menu").classes("w-8 h-8 hover:bg-blue-400 hover:rounded-full").classes("menu-hover"):
                with ui.menu() as menu:
                    def update_password():
                        """修改密码"""
                        if hasattr(update_password, "dialog"):
                            dialog: ui.dialog = getattr(update_password, "dialog")
                            dialog.open()
                            return

                        dialog: ui.dialog = ui.dialog()

                        def close_dialog():
                            """删除 dialog（因为 dialog.close 存在显示 bug）"""
                            dialog.delete()
                            delattr(update_password, "dialog")

                        async def save():
                            url = settings.BACKEND_BASE_URL + "/authentication/change_password/"
                            async with aiohttp.ClientSession() as session:
                                async with session.post(url, json={
                                    "username": auth_manager.get_username(),
                                    "password": old_password.value,
                                    "new_password": new_password.value,
                                    "confirm_password": confirm_password.value,
                                }) as response:
                                    if response.status != 200:
                                        ui.notify(f"修改密码失败！原因：{await response.json()}", type="negative")
                                        # close_dialog()  # todo: try finally 似乎可以让 return 前继续执行 finally
                                        return

                            ui.notify("修改密码成功！", type="positive")
                            close_dialog()
                            # 【知识点】定时器登出，且需要设置成非周期性定时器（once=True）
                            ui.timer(2, lambda: logout(), once=True)

                        with dialog.classes("w-64 h-64"):
                            with ui.card().classes("px-0 pt-0 rounded-none"):
                                with ui.row().classes("flex w-full justify-between items-center bg-gray-100 border"):
                                    ui.label("修改密码").classes("pl-4")
                                    # todo: props 如何使用？
                                    ui.button(icon="close", on_click=lambda: close_dialog()).classes("pr-4").props(
                                        "flat color=gray")
                                with ui.grid(columns=3).classes("items-center"):
                                    # todo: 前端进行数据校验

                                    ui.label("旧密码").classes("justify-self-end")
                                    old_password = ui.input(placeholder="请输入密码", password=True,
                                                            password_toggle_button=True)
                                    ui.space()

                                    ui.label("新密码").classes("justify-self-end")
                                    new_password = ui.input(placeholder="请输入密码", password=True,
                                                            password_toggle_button=True)
                                    ui.space()

                                    ui.label("确认密码").classes("justify-self-end")
                                    confirm_password = ui.input(placeholder="请输入密码", password=True,
                                                                password_toggle_button=True)
                                    ui.space()
                                with ui.element("div").classes("flex w-full justify-end"):
                                    with ui.row().classes("w-1/2"):
                                        ui.button("关闭", on_click=lambda: close_dialog())
                                        ui.button("保存", on_click=lambda: save())

                        dialog.open()
                        setattr(update_password, "dialog", dialog)

                    async def logout():
                        """用户注销，安全退出"""

                        def logout_by_frontend():
                            # 客户端令牌也给删除掉（logout 接口调用后，虽然成功加入进黑名单，但是不知道为什么没用）
                            # 其实这都不能算是客户端，这就是服务端。。即便只是这里将数据删除，安全性也是完全有保障的。
                            try:
                                auth_manager.remove_token()
                                return True
                            except Exception as e:
                                logger.error(e)
                                return False

                        async def logout_by_backend():
                            """后端 jwt token 提前过期"""
                            refresh_token = auth_manager.get_refresh_token()
                            # 如果客户端没有 token，则不必调用后端
                            if not refresh_token:
                                return True

                            url = settings.BACKEND_BASE_URL + "/authentication/logout/"
                            async with aiohttp.ClientSession() as session:
                                async with session.post(url, json={"refresh_token": refresh_token}) as response:
                                    if response.status == 200:
                                        return True
                                    reason = "未知"
                                    if ResponseUtils.is_json_content_type(response):
                                        reason = await response.json()
                                    logger.error("退出登录失败，原因：{}", reason)
                                    return False

                        # 先执行后端，再执行前端。均要执行，但是只要有一个成功就算成功
                        successes = (await logout_by_backend(), logout_by_frontend())
                        if any(successes):
                            logger.info("退出登录成功")
                            ui.navigate.to("/login")
                        else:
                            # 即使退出登录失败，则依旧无感知
                            ui.navigate.to("/login")

                    ui.menu_item("修改密码", on_click=lambda: update_password(), auto_close=False)
                    ui.menu_item("退出登录", on_click=lambda: logout())

                    ui.separator()

                    admin_url = settings.BACKEND_BASE_URL + "/admin/"
                    ui.menu_item("后台管理", on_click=lambda: ui.navigate.to(admin_url))


# -------------------------------------------------------------------------------------------------------------------- #
async def _get_authorization_headers(headers: Dict[str, str] = None, onload=False) -> Dict[str, str]:
    headers = {} if headers is None else headers
    authorization_header = auth_manager.get_authorization_header()
    if authorization_header is None:
        await dialogs.show_unauthorized_dialog(onload=onload)
        return headers
    headers.update([authorization_header])
    return headers


async def verify_authorization_info() -> bool:
    """检查当前客户端连接的认证信息，无权限则弹无权限窗口"""
    # 【知识点】对于前端的每个 page，每次访问（刷新等）都将进行一次权限验证。
    #          而对于后端接口调用，我将选择不在前端处理，返回 200 就视为正常，否则就显示空值。
    #          但是说实在的，其实还是需要处理的，
    verify_url = settings.BACKEND_BASE_URL + "/authentication/login/verify/"
    async with aiohttp.ClientSession() as session:
        async with session.post(verify_url, json={"token": auth_manager.get_access_token()}) as response:
            if response.status != 200:
                await dialogs.show_unauthorized_dialog()
                return False
            return True


class _DataService:
    """数据服务"""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    @staticmethod
    def format_crossplatform_time(ts: pd.Timestamp):
        """pandas Timestamp 拿到时分并转为字符串（00:00:00 和 01:00:00 -> 0:00 和 1:00）"""
        return f"{ts.hour}:{ts.minute:02d}"

    def get_top_statistic_data(self):
        """系统概览 - 顶部四个统计卡片 数据"""
        filepath = settings.DEMO_DATA_DIR / "dimension_scores.csv"
        df = pd.read_csv(filepath)
        # 数据目前只有一行，就将 df 第一行转为字典吧
        for col in df.columns:
            # fixme: 空值填充为 90-100 之间的随机数
            df[col] = df[col].fillna(np.random.uniform(90, 100))
        return df.iloc[0].to_dict()

    async def get_overall_indicator_data(self):
        """光伏承载力 - 获得 总览指标卡片 数据"""
        data = {}

        # 总览指标卡片 - 总装机容量、当前发电量、实际消纳量、消纳效率
        filepath = settings.DEMO_DATA_DIR / "pv_region_distribution.csv"
        df = await run.io_bound(lambda: pd.read_csv(filepath))

        data.update({
            # fixme: 此处是多个区域啊
            "installed_capacity_MW_approx": df["installed_capacity_MW_approx"].sum(),
            "current_gen_avg_MW": df["current_gen_avg_MW"].sum(),
            "E_region_pv_consumed_MWh": df["E_region_pv_consumed_MWh"].sum(),
            "consume_rate_pct": df["consume_rate_pct"].mean(),
        })

        return data

    async def get_plot_generation_consumption_curve_data(self):
        """光伏承载力 - 获得 发电量与消纳量曲线图 数据"""
        data = {}

        # 发电量与消纳量曲线图 - 时间、发电量、消纳量
        filepath = settings.DEMO_DATA_DIR / "hourly_region_pv.csv "
        df = await run.io_bound(lambda: pd.read_csv(filepath, parse_dates=["time"]))

        data.update({
            "hours": [self.format_crossplatform_time(ts) for ts in df["time"]],
            # fixme: 哪个字段啊？
            "gen": df["C_pv_MW"].tolist(),
            "use": df["C_consumed_MW"].tolist(),
        })

        logger.debug("[get_plot_generation_consumption_curve_data:data]: {}", data)
        return data

    async def get_line_loading_details(self):
        """潮流计算 - 获得 线路负载详情 数据（潮流计算页面）"""

        @functools.lru_cache()
        async def get_raw_details():

            # 【知识点】parse_dates 目的是将 CSV 文件中指定列自动解析为 Pandas 的 datetime 对象，而不是保留为原始字符串格式。

            # 数据结构（一条）：
            #           时间          Line0     Line1     ...    Line34  Line35  Line36
            #   2023-01-01 00:00:00  0.000147  0.000131  ...      0.0     0.0     0.0

            filepath = settings.DEMO_DATA_DIR / "pf_line_loading.csv"
            _raw_details = await run.io_bound(lambda: pd.read_csv(filepath, parse_dates=["时间"]))  # 已改为异步读取
            logger.debug(f"raw_details:\n{_raw_details}")
            return _raw_details

        # todo: 这个 raw_details 数据外界对它的操作很多，其实如果能将其抽为一个类，那会舒服很多
        raw_details: pd.DataFrame = await get_raw_details()

        _topology_data = await self.get_topology_structure_data(onload=True)
        edges = _topology_data.get("edges", [])

        line_loading_details = []

        # 如果 edges 返回值是空的，且长度和 details 的 Line0 - LineX 个数不匹配，则
        if not edges or len(edges) != len(raw_details.columns) - 1:
            logger.warning("线路负载详情为空，可能原因：无数据/前后端数据不匹配")
            return line_loading_details

        # 【知识点】【数据转换】将从 csv 拿到的数据整理成渲染时需要用到的数据格式

        # todo: 根据上方图像的时间点（点击触发）来进行刷新和渲染操作（是否可以使用响应式呢），目前暂时默认选择 00:00:00，即第一条数据
        time_point_line_loading_data = (raw_details.loc[0].drop("时间") * 300000).tolist()  # 暂时直接放大，因为是编的数据

        assert len(time_point_line_loading_data) == len(
            edges), f"负载数据长度（{len(time_point_line_loading_data)}）和边数据长度（{len(edges)}）不匹配"

        for i, edge in enumerate(edges):
            line_loading_details.append({
                "name": f"线路{edge["source"]}-{edge["target"]}",
                "from": edge["source"],
                "to": edge["target"],
                "loading": time_point_line_loading_data[i],
                "power": "unknown",
                "current": "unknown",
            })

        return line_loading_details

    async def get_topology_structure_data(self,
                                          onload: Annotated[
                                              bool, "是否属于加载阶段"] = False) -> typeddicts.TopologyStructure:
        """拓扑结构 - 获得 拓扑结构 数据"""
        # internal dependencies

        url = settings.BACKEND_BASE_URL + "/pdn/get_topology_structure/"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=await _get_authorization_headers(onload=onload)) as response:
                if not ResponseUtils.is_json_content_type(response):
                    logger.error(f"error response: {response}")
                    await dialogs.show_error_dialog("非受检异常，请联系维护人员。")
                    return {"nodes": [], "edges": []}
                if response.status != 200:
                    if response.status == 403:
                        await dialogs.show_unauthorized_dialog(onload=onload)
                        return {"nodes": [], "edges": []}
                    await dialogs.show_error_dialog(f"{await response.json()}")
                    return {"nodes": [], "edges": []}
                return await response.json()

    async def get_power_flow_calculation_result(self, onload: Annotated[bool, "是否属于加载阶段"] = False):
        """潮流计算 - 获得 潮流计算 结果"""

        async def version_1_0():
            """旧版本逻辑，直接调用后端接口，现在先走文件数据逻辑，但是旧版本依旧暂时保留（至少可以进行认证校验）"""
            url = settings.BACKEND_BASE_URL + "/pdn/get_power_flow_calculation_result/"
            res = {}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=await _get_authorization_headers(onload=onload)) as response:
                    if response.status != 200:
                        if response.status == 403:
                            await dialogs.show_unauthorized_dialog(onload=onload)
                            return res
                        await dialogs.show_error_dialog(f"{await response.json()}")
                        return res
                    return await response.json()

        data = await version_1_0()

        # 新版本逻辑
        # 需要返回的数据如下：
        #   指标卡 - 总功率、最大负载率、电压偏差率、网损率
        #   多曲线面积图 - x 轴的时间列表、有功功率 series、无功功率 series、电压 series
        new_data = {}

        hourly_curve_df = pd.read_csv(settings.DEMO_DATA_DIR / "dashboard_hourly_curve.csv", parse_dates=["time"])

        # 指标卡 - S_MVA, max_line_loading_pct, voltage_deviation_pct, loss_rate_pct
        # todo: 由于数据是多行数据，我选先计算平均值（对于百分比数据）
        new_data.update({
            "total_power": hourly_curve_df["S_MVA"].sum(),
            "max_loading": hourly_curve_df["max_line_loading_pct"].mean(),
            "voltage_deviation": hourly_curve_df["voltage_deviation_pct"].mean(),
            "network_loss": hourly_curve_df["loss_rate_pct"].mean(),
        })

        # 多曲线面积图 - time, P_MW, Q_MVAr, U_avg_pu
        new_data.update({
            "times": [self.format_crossplatform_time(ts) for ts in hourly_curve_df["time"].tolist()],
            "p_series": hourly_curve_df["P_MW"].tolist(),
            "q_series": hourly_curve_df["Q_MVAr"].tolist(),
            "v_series": hourly_curve_df["U_avg_pu"].tolist(),
        })

        # 多曲线面积图 - 还需要获得动态的功率/电压最小值向下取整，和最大值向上取整（左闭右闭）
        def caculate_range(*args: List[Iterable]):
            values = []
            for arg in args:
                values.extend(arg)
            return [math.floor(min(values)), math.ceil(max(values))]

        new_data.update({
            "power_range": caculate_range(hourly_curve_df["P_MW"], hourly_curve_df["Q_MVAr"]),
            "voltage_range": caculate_range(hourly_curve_df["U_avg_pu"]),
        })

        logger.debug(f"new_data:\n{new_data}")

        data.update(new_data)
        return data


data_service = _DataService()
