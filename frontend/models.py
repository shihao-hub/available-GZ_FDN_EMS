import tortoise
from tortoise import Tortoise, fields, models

from settings import TORTOISE_ORM


# 【知识点】nicegui 的 models.py 可以视为浏览器的存储功能（由于不是客户端，所以安全性等方面根本不需要考虑）

# cls._instance._cache_info_key = "_AuthManager:cache_info"  # 用户缓存信息，如记忆选项卡


class ClientCache(models.Model):
    client_id = fields.CharField(description="nicegui 客户端 id", max_length=36, unique=True)
    # 该项目无匿名用户，任何访问都需要登录，所以不可为空？但是这导致初始化不方便，其实既然是 ClientCache，我推荐一律允许为空
    username = fields.CharField(description="用户名", max_length=36, null=True)
    so_plan = fields.CharField(description="系统概览-选择方案", max_length=20, null=True)
    so_time_range = fields.CharField(description="系统概览-时间范围", max_length=20, null=True)
    so_data_frequency = fields.CharField(description="系统概览-数据频率", max_length=20, null=True)

    class Meta:
        table = "client_cache"

    def __str__(self):
        return f"{self.client_id}"


def tortoise_init():
    async def init():
        """初始化 tortoise 操作，必做操作"""
        # 配置数据库连接
        await Tortoise.init(
            db_url=TORTOISE_ORM["connections"]["default"],
            modules={"models": TORTOISE_ORM["apps"]["models"]["models"]},
        )
        # 生成数据库表（不要，用 aerich 帮忙生成）
        # await Tortoise.generate_schemas()

    tortoise.run_async(init())
