import uuid
from pathlib import Path

import asyncio
import anyio
import aiohttp
from loguru import logger


async def download_file(url, filename=None):
    if filename is None:
        filename = url.split("/")[-1]

    Path("echarts").mkdir(exist_ok=True)
    filepath = Path("echarts", filename)
    if filepath.exists():
        logger.info("文件 {} 已存在，不必下载", filename)
        return

    async with aiohttp.ClientSession() as session:
        # todo: 使用流式下载（大文件，节省内存） + tqdm.tqdm 实现带进度条下载
        async with session.get(url, timeout=10) as response:
            if response.status != 200:
                logger.error("访问 {} 下载文件失败，response.status: {}", url, response.status)
                return

            # 【知识点】通过链接下载文件，链接的响应体就是文件的二进制内容
            filepath.write_bytes(await response.read())
            logger.info("文件 {} 下载成功", filename)


async def main():
    urls = [
        "https://cdn.jsdelivr.net/npm/echarts@5/dist/" + "echarts.common.js",
        "https://cdn.jsdelivr.net/npm/echarts@5/dist/" + "echarts.common.min.js",
        "https://cdn.jsdelivr.net/npm/echarts@5/dist/" + "echarts.esm.js",
        "https://cdn.jsdelivr.net/npm/echarts@5/dist/" + "echarts.esm.min.js",
        "https://cdn.jsdelivr.net/npm/echarts@5/dist/" + "echarts.js",
        "https://cdn.jsdelivr.net/npm/echarts@5/dist/" + "echarts.min.js",
        "https://cdn.jsdelivr.net/npm/echarts@5/dist/" + "echarts.simple.js",
        "https://cdn.jsdelivr.net/npm/echarts@5/dist/" + "echarts.simple.min.js",

        "https://assets.pyecharts.org/assets/v5/" + "echarts-liquidfill.min.js",
    ]

    async with anyio.create_task_group() as tg:
        tasks = []
        for url in urls:
            # 测试发现，download_file 第二个参数如果是 kwargs，此处传参的时候无法识别，只能按顺序全填写...
            task = tg.start_soon(download_file, url, None)
            tasks.append(task)


if __name__ == '__main__':
    anyio.run(main)
