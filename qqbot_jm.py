import asyncio
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import nonebot
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Adapter, Bot, GroupMessageEvent, Message, MessageEvent


ROOT = Path(__file__).resolve().parent
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
JMCOMIC = ROOT / ".venv" / "Scripts" / "jmcomic.exe"
OPTION = ROOT / "option_zip.yml"
DOWNLOAD_DIR = ROOT / "downloads"
NAPCAT_SHARED_DIR = "/app/napcat/shared"


def newest_zip(before: set[Path]) -> Path | None:
    zip_dir = DOWNLOAD_DIR / "zip"
    if not zip_dir.exists():
        return None

    candidates = [
        path
        for path in zip_dir.glob("*.zip")
        if path not in before and path.is_file()
    ]

    if not candidates:
        candidates = [path for path in zip_dir.glob("*.zip") if path.is_file()]

    return max(candidates, key=lambda path: path.stat().st_mtime, default=None)


def parse_jm_id(text: str) -> str | None:
    match = re.search(r"(?:jm)?\s*(\d{3,})", text, flags=re.IGNORECASE)
    return match.group(1) if match else None


async def run_download(album_id: str) -> tuple[int, str, Path | None]:
    if DOWNLOAD_DIR.exists():
        shutil.rmtree(DOWNLOAD_DIR)

    zip_dir = DOWNLOAD_DIR / "zip"
    zip_dir.mkdir(parents=True, exist_ok=True)
    before: set[Path] = set()

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    process = await asyncio.create_subprocess_exec(
        str(JMCOMIC),
        album_id,
        "--option",
        str(OPTION),
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    output_bytes, _ = await process.communicate()
    output = output_bytes.decode("utf-8", errors="replace")
    return process.returncode, output[-1500:], newest_zip(before)


nonebot.init()
driver = nonebot.get_driver()
driver.register_adapter(Adapter)

jm = on_message(priority=10, block=False)


@jm.handle()
async def handle_jm(bot: Bot, event: MessageEvent):
    text = event.get_plaintext().strip()
    if not re.search(r"(?i)(^|[\s/])jm\s*\d{3,}", text):
        return

    album_id = parse_jm_id(text)
    if album_id is None:
        await jm.finish("用法：/jm 350234")

    await jm.send(f"收到 JM{album_id}，开始下载并打包 zip。")

    code, output, zip_file = await run_download(album_id)
    if code != 0 or zip_file is None:
        await jm.finish(f"下载失败，退出码 {code}。\n{output}")

    if isinstance(event, GroupMessageEvent):
        try:
            upload_path = f"{NAPCAT_SHARED_DIR}/{zip_file.name}"
            await bot.call_api(
                "upload_group_file",
                group_id=event.group_id,
                file=upload_path,
                name=zip_file.name,
            )
        except Exception as exc:
            await jm.finish(
                f"JM{album_id} 已打包完成，但上传群文件失败：{exc}\n"
                f"文件在本机：{zip_file}"
            )

        await jm.finish(f"JM{album_id} 已打包并上传：{zip_file.name}")

    try:
        upload_path = f"{NAPCAT_SHARED_DIR}/{zip_file.name}"
        await bot.call_api(
            "upload_private_file",
            user_id=event.user_id,
            file=upload_path,
            name=zip_file.name,
        )
    except Exception as exc:
        await jm.finish(
            f"JM{album_id} 已打包完成，但私聊发送文件失败：{exc}\n"
            f"文件在本机：{zip_file}"
        )

    await jm.finish(f"JM{album_id} 已打包并私聊发送：{zip_file.name}")


if __name__ == "__main__":
    nonebot.run(host="127.0.0.1", port=8080)
