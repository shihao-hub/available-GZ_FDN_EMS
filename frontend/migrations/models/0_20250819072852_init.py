from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);
CREATE TABLE IF NOT EXISTS "client_cache" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "client_id" VARCHAR(36) NOT NULL UNIQUE /* nicegui 客户端 id */,
    "username" VARCHAR(36) /* 用户名 */,
    "so_plan" VARCHAR(20) /* 系统概览-选择方案 */,
    "so_time_range" VARCHAR(20) /* 系统概览-时间范围 */,
    "so_data_frequency" VARCHAR(20) /* 系统概览-数据频率 */
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
