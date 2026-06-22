import asyncio
import json
import os
import re
import shutil
import smtplib
import subprocess
import sys
import time
from email.message import EmailMessage
from pathlib import Path

import pyzipper
import nonebot
from nonebot import on_message, on_notice, on_request
from nonebot.adapters.onebot.v11 import (
    Adapter,
    Bot,
    FriendRequestEvent,
    GroupMessageEvent,
    MessageEvent,
    NoticeEvent,
)
from nonebot.log import logger


ROOT = Path(__file__).resolve().parent
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
JMCOMIC = ROOT / ".venv" / "Scripts" / "jmcomic.exe"
OPTION = ROOT / "config" / "option_zip.yml"
DOWNLOAD_DIR = ROOT / "downloads"

ALERT_CONFIG = ROOT / "config" / "alert_config.json"
ALERT_CONFIG_LOCAL = ROOT / "config" / "alert_config.local.json"
QRCODE_PATH = ROOT / "logs" / "napcat-qrcode.png"
WEBUI_CONFIG = ROOT / "tools" / "napcat-docker" / "config" / "webui.json"


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


def shared_file_uri(name: str) -> str:
    """Desktop(原生)模式：NapCat 与机器人在同一台 Windows 上，直接用 zip 的
    本机真实路径生成 file:// URI（Path.as_uri() 自带百分号编码），交给 NapCat 读取。
    传裸路径会被 NapCat 的 new URL() 解析成 "识别URL失败 (retcode=1200)"，故用 file://。"""
    return (DOWNLOAD_DIR / "zip" / name).as_uri()


# 上传前清洗文件名：去掉 ♥ 〜 （） ○ ・ 等符号，并截断到文件系统能接受的长度。
# 保留中日文、字母数字、空格和 []()-_. 安全字符，其余替换成空格再合并。
_SAFE_FILENAME_PUNCT = set(" -_[]().")
# NapCat 在 Linux 容器里 open() 文件，单个文件名上限 255 字节(UTF-8)，
# 超长会报 ENAMETOOLONG。留余量，整个文件名(含 .zip)最长 200 字节。
_MAX_NAME_BYTES = 200


def sanitize_zip_name(name: str, album_id: str) -> str:
    stem = name[:-4] if name.lower().endswith(".zip") else name
    cleaned = "".join(
        ch if (ch.isalnum() or ch in _SAFE_FILENAME_PUNCT) else " "
        for ch in stem
    )
    cleaned = " ".join(cleaned.split()).strip()
    if not cleaned:
        cleaned = f"JM{album_id}"
    # 按 UTF-8 字节截断（给 ".zip" 留 4 字节），不切断多字节字符
    budget = _MAX_NAME_BYTES - len(b".zip")
    if len(cleaned.encode()) > budget:
        cleaned = cleaned.encode()[:budget].decode("utf-8", errors="ignore").rstrip()
    return f"{cleaned}.zip"


def make_group_pack(inner_zip: Path, album_id: str) -> Path:
    """群文件容易被和谐：QQ 会把上传的 zip 解开扫描内容，普通压缩包（哪怕套几层）
    都防不住——它读得到里面的图。改用 AES 加密压缩包：QQ 解不开、读不到内容，
    就不会拦下载。外层文件名只用 JM+车号，解压密码 = 车号（机器人会在群里回出来）。
    内层已是压缩包，ZIP_STORED 不二次压缩。"""
    outer = inner_zip.with_name(f"JM{album_id}.zip")
    # 标题为空时 sanitize 也会得到 JMxxxx.zip，避免外层名与内层名相撞
    if outer == inner_zip:
        outer = inner_zip.with_name(f"JM{album_id}_pack.zip")
    with pyzipper.AESZipFile(
        outer, "w", compression=pyzipper.ZIP_STORED, encryption=pyzipper.WZ_AES
    ) as zf:
        zf.setpassword(album_id.encode())
        zf.write(inner_zip, arcname=inner_zip.name)
    return outer


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
friend_request = on_request(priority=5, block=False)

# 串行化下载：同一时间只允许一个下载+上传任务，避免并发时
# run_download 开头的 rmtree(downloads) 互删文件、或把 zip 发错人。
# 后到的请求会自动排队，按 FIFO 依次执行。
download_lock = asyncio.Lock()


@friend_request.handle()
async def handle_friend_request(bot: Bot, event: FriendRequestEvent):
    await bot.call_api(
        "set_friend_add_request",
        flag=event.flag,
        approve=True,
    )


@jm.handle()
async def handle_jm(bot: Bot, event: MessageEvent):
    text = event.get_plaintext().strip()
    if not re.search(r"(?i)(^|[\s/])jm\s*\d{3,}", text):
        return

    album_id = parse_jm_id(text)
    if album_id is None:
        await jm.finish("用法：/jm 350234")

    if download_lock.locked():
        await jm.send(f"收到 JM{album_id}，前面有任务在下载，已排队，请稍候…")
    else:
        await jm.send(f"收到 JM{album_id}，开始下载并打包 zip。")

    # 整个“下载 + 上传”过程都持锁：上传读取的是 downloads/zip 里的文件，
    # 必须等上传完成才放锁，否则下一个任务的 rmtree 会把 zip 删掉。
    async with download_lock:
        code, output, zip_file = await run_download(album_id)
        if code != 0 or zip_file is None:
            await jm.finish(f"下载失败，退出码 {code}。\n{output}")

        # 先清洗文件名去掉特殊字符，再用 file:// URI 上传（双保险）。
        safe_name = sanitize_zip_name(zip_file.name, album_id)
        if zip_file.name != safe_name:
            zip_file = zip_file.rename(zip_file.with_name(safe_name))

        upload_path = shared_file_uri(zip_file.name)

        if isinstance(event, GroupMessageEvent):
            # 群文件易被和谐：再套一层，外层只用 JM+车号命名（不含漫画名）后上传。
            pack = await asyncio.to_thread(make_group_pack, zip_file, album_id)
            try:
                await bot.call_api(
                    "upload_group_file",
                    group_id=event.group_id,
                    file=pack.as_uri(),
                    name=pack.name,
                )
            except Exception as exc:
                await jm.finish(
                    f"JM{album_id} 已打包完成，但上传群文件失败：{exc}\n"
                    f"文件在本机：{pack}"
                )

            await jm.finish(
                f"JM{album_id} 已上传：{pack.name}\n解压密码：{album_id}"
            )

        try:
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


# ---------------------------------------------------------------------------
# 掉线告警：QQ 被踢 / NapCat 断开时发邮件提醒（服务器无人值守场景）
# 配置放在 alert_config.json（已被 .gitignore 忽略），缺失则只记日志不发信。
# ---------------------------------------------------------------------------

_alert_lock = asyncio.Lock()
_last_alert_at = 0.0  # 上次成功发信的 time.monotonic()，0 表示可立即发
_current_bot: Bot | None = None


def load_alert_config() -> dict:
    """分层读取：先 base(alert_config.json)，再用 local(alert_config.local.json) 覆盖。

    local 不进仓库（已 gitignore），放真实密钥；base 进仓库，只留结构和占位。
    以 "_" 开头的键视为注释，忽略。
    """
    cfg: dict = {}
    for path in (ALERT_CONFIG, ALERT_CONFIG_LOCAL):
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            cfg.update({k: v for k, v in data.items() if not k.startswith("_")})
        except Exception as exc:
            logger.error(f"读取 {path.name} 失败：{exc}")
    return cfg


def webui_login_url(cfg: dict) -> str:
    base = (cfg.get("webui_url") or "").rstrip("/")
    if not base:
        return ""
    try:
        token = json.loads(WEBUI_CONFIG.read_text(encoding="utf-8")).get("token", "")
    except Exception:
        token = ""
    return f"{base}?token={token}" if token else base


def _send_email_sync(cfg: dict, subject: str, body: str, attachment: Path | None) -> None:
    msg = EmailMessage()
    msg["From"] = cfg["smtp_user"]
    msg["To"] = cfg.get("smtp_to") or cfg["smtp_user"]
    msg["Subject"] = subject
    msg.set_content(body)

    if attachment and attachment.exists():
        msg.add_attachment(
            attachment.read_bytes(),
            maintype="image",
            subtype="png",
            filename=attachment.name,
        )

    port = int(cfg.get("smtp_port", 465))
    if port == 465:
        with smtplib.SMTP_SSL(cfg["smtp_host"], port, timeout=30) as server:
            server.login(cfg["smtp_user"], cfg["smtp_pass"])
            server.send_message(msg)
    else:
        with smtplib.SMTP(cfg["smtp_host"], port, timeout=30) as server:
            server.starttls()
            server.login(cfg["smtp_user"], cfg["smtp_pass"])
            server.send_message(msg)


async def send_offline_alert(reason: str) -> None:
    cfg = load_alert_config()
    required = ("smtp_host", "smtp_user", "smtp_pass")
    if not all(cfg.get(key) for key in required):
        logger.warning(f"机器人掉线（{reason}），但未配置 alert_config.json，跳过邮件告警。")
        return

    global _last_alert_at
    async with _alert_lock:
        now = time.monotonic()
        min_interval = float(cfg.get("min_interval_seconds", 1800))
        if _last_alert_at and now - _last_alert_at < min_interval:
            logger.info(f"机器人掉线（{reason}），距上次告警过近，跳过本次邮件。")
            return
        _last_alert_at = now

    when = time.strftime("%Y-%m-%d %H:%M:%S")
    login_url = webui_login_url(cfg)
    body = (
        f"JMComic QQ 机器人掉线了，需要处理。\n\n"
        f"时间：{when}\n"
        f"原因：{reason}\n\n"
        f"重新登录方式（服务器无屏幕时）：\n"
        f"1. 浏览器打开 NapCat WebUI：\n   {login_url or '（未配置 webui_url）'}\n"
        f"2. 在 WebUI 里点重新登录，用手机 QQ 扫码。\n"
        f"3. 或在服务器上重跑 start_bot_background。\n\n"
        f"如果本邮件带有二维码附件，可用另一台设备打开后直接扫描。\n"
    )
    subject = "⚠️ JMComic QQ机器人掉线，请重新登录"
    attachment = QRCODE_PATH if QRCODE_PATH.exists() else None

    try:
        await asyncio.to_thread(_send_email_sync, cfg, subject, body, attachment)
        logger.success(f"掉线告警邮件已发送（{reason}）。")
    except Exception as exc:
        async with _alert_lock:
            _last_alert_at = 0.0  # 发送失败，允许下次重试
        logger.error(f"掉线告警邮件发送失败：{exc}")


@driver.on_bot_connect
async def _on_bot_connect(bot: Bot) -> None:
    global _current_bot, _last_alert_at
    _current_bot = bot
    _last_alert_at = 0.0  # 重连后允许下次掉线立即告警
    logger.success(f"Bot {bot.self_id} connected，掉线监控已就绪。")


@driver.on_bot_disconnect
async def _on_bot_disconnect(bot: Bot) -> None:
    global _current_bot
    _current_bot = None
    await send_offline_alert("OneBot 连接断开（NapCat 退出或反向 WS 断开）")


offline_notice = on_notice(priority=1, block=False)


@offline_notice.handle()
async def _on_offline_notice(event: NoticeEvent) -> None:
    if getattr(event, "notice_type", None) != "bot_offline":
        return
    msg = getattr(event, "message", None) or getattr(event, "tag", None) or "QQ 登录已失效"
    await send_offline_alert(f"收到 bot_offline 通知：{msg}")


@driver.on_startup
async def _start_status_monitor() -> None:
    asyncio.create_task(_status_monitor_loop())


async def _status_monitor_loop() -> None:
    cfg = load_alert_config()
    interval = float(cfg.get("poll_interval_seconds", 180))
    while True:
        await asyncio.sleep(interval)
        bot = _current_bot
        if bot is None:
            continue
        try:
            status = await bot.call_api("get_status")
        except Exception as exc:
            await send_offline_alert(f"get_status 调用异常，连接可能已断：{exc}")
            continue
        if status is not None and status.get("online") is False:
            await send_offline_alert("get_status 返回 online=False（QQ 登录态已失效）")


if __name__ == "__main__":
    nonebot.run(host="127.0.0.1", port=8080)
