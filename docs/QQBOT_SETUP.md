# JMComic QQ Bot Setup

本文档记录在原项目基础上追加 QQ Bot 集成后的运行环境、依赖、启动方式和使用方式，方便换电脑或开启新对话时快速接手。

## 版权与归属说明

原项目不是我们写的，是开源项目：

```text
hect0x7/JMComic-Crawler-Python
```

项目地址：

```text
https://github.com/hect0x7/JMComic-Crawler-Python
```

原项目描述：

```text
Python API for JMComic | 提供Python API访问禁漫天堂，同时支持网页端和移动端 | 禁漫天堂GitHub Actions下载器
```

原项目信息：

```text
Author/Repo: hect0x7/JMComic-Crawler-Python
Language: Python
License: MIT
Stars/Forks/Issues: 1182/2673/3
Last pushed: 2025-03-19T00:17:38
```

本地这次做的事情只是：在原项目外面额外加了一套 QQ Bot/NapCat/NoneBot 的调用层，让 QQ 消息可以触发原项目的 `jmcomic` 下载能力。

也就是说：

- 原项目 `JMComic-Crawler-Python` 的核心功能和版权归原作者/原仓库
- 我们没有把原项目声明成自己的作品
- 我们只是做了本地二次集成：QQ Bot、启动脚本、Docker/NapCat 配置、zip 下载配置和这份说明文档
- 原项目使用 MIT License，继续遵守原许可证

## 原项目说明

这个仓库原本是 `JMComic-Crawler-Python`，核心是 Python 包 `jmcomic`。

原项目主要能力：

- 通过 Python API 下载 JMComic album/photo
- 提供命令行工具 `jmcomic`
- 提供查看详情命令 `jmv`
- 支持 option 配置文件
- 支持插件，例如 zip、pdf、long image、登录、浏览器 cookies 等

原项目核心代码在：

```text
src\jmcomic
```

本次接入 QQ 机器人时，没有修改 `src\jmcomic` 里的核心库代码。当前改动主要是新增外围脚本、配置和文档，让 QQ 消息可以调用本地 `jmcomic` 下载并打包。

## 功能

- QQ 群聊或私聊发送 `/jm 车号`
- 本机下载 JMComic
- 下载完成后自动打包为 zip
- 下载新任务前自动清理上一次的 `downloads`，避免磁盘空间持续增长
- 群聊触发：上传 zip 到群文件
- 私聊触发：直接私聊发送 zip 文件；失败时回复本机文件路径
- 自动同意 QQ 好友申请
- 多个下载任务自动排队、串行执行（详见下文“并发与排队”）

## 本次新增/修改内容

### QQ 机器人相关

```text
qqbot_jm.py
requirements-qqbot.txt
```

`qqbot_jm.py` 是 NoneBot2 机器人入口。

它负责：

- 接收 QQ 消息
- 识别 `/jm 350234`
- 调用 `.venv\Scripts\jmcomic.exe`
- 使用 `option_zip.yml` 下载并打包
- 群聊上传群文件
- 私聊发送文件
- 收到 QQ 好友申请时自动同意
- 机器人掉线时发邮件告警（详见下文“掉线告警”）

### 掉线告警配置

```text
config\alert_config.json
config\alert_config.local.json
```

- `alert_config.json`：进仓库的基础配置，只放结构和默认值，不填真实密钥
- `alert_config.local.json`：放真实邮箱密钥，已被 `.gitignore` 忽略，不进仓库

详见下文“掉线告警（邮件）”。

### 下载和打包配置

```text
config\option_zip.yml
```

作用：

- 指定下载目录为 `downloads`
- 下载完成后压缩到 `downloads\zip`
- 删除原图片目录，只保留 zip

### NapCat / Docker 配置

```text
config\docker-compose.napcat.yml
scripts\configure_napcat_onebot.ps1
scripts\configure_napcat_onebot.bat
```

作用：

- 用 Docker 启动 NapCat
- 把 `downloads\zip` 挂载到容器内 `/app/napcat/shared`
- 配置 NapCat 反向 WebSocket 连接到 NoneBot：

```text
ws://host.docker.internal:8080/onebot/v11/ws
```

### 启动/停止/日志脚本

为保持根目录整洁，**根目录只放 3 个常用的双击入口 `.bat`**：

```text
start_bot_background.bat
stop_bot_background.bat
tail_bot_log.bat
```

它们的具体实现（`.ps1`）和次要脚本都收在 `scripts\` 目录里：

```text
scripts\start_bot_background.ps1
scripts\stop_bot_background.ps1
scripts\tail_bot_log.ps1
scripts\configure_napcat_onebot.ps1
scripts\configure_napcat_onebot.bat
scripts\open_napcat_qrcode.bat
```

平时只需双击根目录那 3 个 `.bat`，不用进 `scripts\`。`.bat` 会自动调用 `scripts\` 下对应的 `.ps1`。

### 文档

```text
QQBOT_SETUP.md
```

就是当前这份文档。

## 运行产物

这些是运行过程中生成的，不属于原项目核心代码：

```text
.venv
downloads
logs
tools\napcat-docker
```

说明：

- `.venv` 是 Python 虚拟环境，可以重新创建
- `downloads` 是下载产物，可以删除
- `logs` 是机器人日志和运行时文件，可以删除
- `tools\napcat-docker` 是 NapCat 配置、QQ 登录数据和挂载目录

运行时产物都集中在 `logs\` 里，根目录不再散落这些文件：

- `logs\jmcomic-bot.pid` 是后台进程 pid 文件，可以删除
- `logs\napcat-qrcode.png` 是登录二维码临时图片，登录成功后会自动删除

换电脑时，如果想保留 QQ 登录态，可以尝试一起复制：

```text
tools\napcat-docker
```

但 QQ 登录态不一定能跨机器复用。更稳的方式是在新电脑重新扫码登录。

## Git/提交建议

如果要提交代码，建议提交：

```text
README.md
qqbot_jm.py
requirements-qqbot.txt
config\option_zip.yml
config\docker-compose.napcat.yml
config\alert_config.json
docs\
scripts\
*.bat
```

不建议提交：

```text
.venv
downloads
logs
tools\napcat-docker
config\alert_config.local.json
```

`alert_config.json` 是不含密钥的基础配置，可以提交；`alert_config.local.json` 含真实邮箱授权码，已在 `.gitignore`，不要提交。

如果仓库要长期维护，建议把这些运行产物加入 `.gitignore`。

## 目录

本文档中的路径默认都相对于“项目根目录”。项目放在哪里都可以，例如：

```text
C:\Users\xxx\JMComic-Crawler-Python-master
D:\cms1\JMComic-Crawler-Python-master
```

下载输出目录：

```text
downloads\zip
```

机器人日志：

```text
logs\jmcomic-bot.log
logs\jmcomic-bot.err.log
```

所有 PowerShell 命令都建议先进入项目根目录再执行。

## 需要的软件

### 必需

- Windows
- Python 3.12+
- Docker Desktop
- Node.js/npm：当前机器有，但此方案主要依赖 Docker，不强依赖 npm
- QQ 账号一个，用于登录 NapCat

### 当前已用版本

- Python `3.12.10`
- Docker Desktop 可用
- NapCat Docker 镜像：

```text
mlikiowa/napcat-docker:latest
```

Python 虚拟环境：

```text
.venv
```

## Python 依赖

项目本体：

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

QQ 机器人依赖：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-qqbot.txt
```

主要依赖：

- `jmcomic`
- `nonebot2`
- `nonebot-adapter-onebot`

## 关键文件

启动后台机器人：

```text
start_bot_background.bat
```

一键全停：

```text
stop_bot_background.bat
```

查看实时日志：

```text
tail_bot_log.bat
```

NapCat Docker 配置：

```text
config\docker-compose.napcat.yml
```

机器人代码：

```text
qqbot_jm.py
```

JMComic 下载和 zip 配置：

```text
config\option_zip.yml
```

NapCat OneBot 自动配置脚本：

```text
scripts\configure_napcat_onebot.ps1
```

## 启动

双击：

```text
start_bot_background.bat
```

它会自动：

- 启动 NapCat Docker 容器
- 如果 QQ 未登录，生成并打开二维码图片：

```text
logs\napcat-qrcode.png
```

- 等扫码登录成功后删除二维码图片
- 配置 NapCat 反向 WebSocket 到 NoneBot
- 启动后台 Python 机器人

如果需要看运行情况，双击：

```text
tail_bot_log.bat
```

看到类似下面内容表示连接成功：

```text
Bot 3431188215 connected
connection open
```

## 停止

双击：

```text
stop_bot_background.bat
```

会停止：

- 后台 Python 机器人
- NapCat Docker 容器

## 使用

### 好友申请

机器人收到 QQ 好友申请会自动同意，不需要手动确认。

### 群聊

在群里发送：

```text
/jm 350234
```

效果：

- 下载
- 打包 zip
- 上传群文件

### 私聊

私聊机器人发送：

```text
/jm 350234
```

效果：

- 下载
- 打包 zip
- 私聊发送 zip 文件
- 如果私聊文件发送失败，会回复运行机器人的电脑上的文件路径

注意：下载和打包发生在运行机器人的电脑上，不是在发消息的电脑上。

## 下载配置

当前 `option_zip.yml` 会：

- 使用 `api` 客户端
- 下载到 `downloads`
- 下载完成后打包到 `downloads\zip`
- 删除原图片文件夹，只保留 zip

zip 文件名示例：

```text
JM350234-董卓 上+下.zip
```

## 并发与排队

所有下载任务**共用同一个 `downloads` 目录**，且每个任务开始时会先清空它（省磁盘）。为避免多个任务同时跑时互相删文件、或把 zip 发错人，机器人用一把全局锁（`qqbot_jm.py` 里的 `download_lock`）把**整个“下载 + 上传”过程串行化**：

- 同一时间只有一个任务在下载/上传
- 后到的 `/jm` 请求会**自动排队**，按先来后到依次执行
- 排队中的请求会先收到提示：`前面有任务在下载，已排队，请稍候…`

注意锁会持有到**上传完成**才释放——因为上传读取的是 `downloads\zip` 里的文件，必须等它发完，否则下一个任务的清空会把 zip 删掉。所以单个任务较慢时，后面的人需要多等一会，这是正常现象。

> 不建议为了“加速”改成并行下载：下载是网络/磁盘密集型，并行快不了多少，反而会因为短时间大量请求放大被 QQ 风控的概率。

## Docker 挂载

`config\docker-compose.napcat.yml` 把本机 zip 目录挂进容器（compose 在 `config\` 子目录里，所以是 `../`）：

```text
../downloads/zip:/app/napcat/shared
```

机器人上传文件时使用容器内路径：

```text
/app/napcat/shared/xxx.zip
```

这是必须的，因为 NapCat 在 Docker 里，不能直接识别 Windows 路径。

## 掉线告警（邮件）

机器人在服务器上无人值守时，QQ 登录态被踢、或 NapCat 挂掉都不会有人立刻发现。为此加了一套**邮件告警**：检测到掉线就给你发邮件，并附上重新登录用的 WebUI 地址和二维码。

### 触发条件（三重检测）

1. 收到 NapCat 转发的 `bot_offline` 通知（QQ 账号被服务端踢，最常见）
2. OneBot 反向 WebSocket 断开（NapCat 进程退出 / 容器停了）
3. 定时轮询 `get_status` 兜底（默认每 180 秒，发现 `online=false` 即告警）

任一触发都会发一封邮件，并带 30 分钟防抖（`min_interval_seconds`），避免短时间内重复轰炸；机器人重新连上后防抖自动复位，下次掉线可立即告警。

### 配置方式（base + local 分层，类似 .env / .env.local 概念）

> 注意：这里的 base/local 是本功能自带的两个 JSON 文件，和 NoneBot 自己的 `.env` 无关。

- `alert_config.json`（base）：**进仓库**。只放结构、注释和非密钥默认值（SMTP 端口、轮询间隔等）。迁移到新机器后看这个文件就知道要配什么。
- `alert_config.local.json`（local）：**不进仓库**（已在 `.gitignore`）。放真实邮箱密钥。

读取规则：先读 base，再用 local **覆盖同名字段**。local 里只需填你要改的字段（一般就是邮箱几项），其余继承 base。两个文件里 `smtp_user`/`smtp_pass` 都为空时，掉线只记日志、**不发邮件**（功能等于关闭，不会报错）。

以 `_` 开头的键是注释，程序会忽略。

### 启用步骤

1. 打开 `config\alert_config.local.json`，填写：

```json
{
  "smtp_user": "你的发件邮箱@qq.com",
  "smtp_pass": "邮箱SMTP授权码(不是登录密码)",
  "smtp_to": "接收告警的邮箱@qq.com",
  "webui_url": "http://服务器能被你访问到的IP:6099/webui"
}
```

2. 如果用的不是 QQ 邮箱，再去 `alert_config.json` 里改 `smtp_host` / `smtp_port`（或同样写进 local 覆盖）。常见：QQ `smtp.qq.com:465`、163 `smtp.163.com:465`、Gmail `smtp.gmail.com:587`。
3. 重启机器人（`stop_bot_background.bat` → `start_bot_background.bat`）生效。

授权码说明：QQ/163 邮箱要先在邮箱设置里**开启 SMTP 服务并生成授权码**，填授权码而不是邮箱登录密码。

### 收到告警后怎么重新登录（服务器无屏幕）

邮件里会给出 NapCat WebUI 地址（自动拼好 token，形如 `http://IP:6099/webui?token=xxxx`）：

1. 在任意一台能上网的设备用浏览器打开这个地址
2. 在 WebUI 里点重新登录，用**手机 QQ 扫码**
3. 或者直接在服务器上重跑 `start_bot_background`

如果掉线时 `logs\` 目录已有 `napcat-qrcode.png`，邮件会把它作为附件一起发出，可用另一台设备打开后直接扫。

## 常见问题

### 双击 ps1 变成记事本

不要双击 `.ps1`。

双击 `.bat`：

```text
start_bot_background.bat
stop_bot_background.bat
tail_bot_log.bat
```

### 发消息没反应

先看日志：

```text
tail_bot_log.bat
```

确认有：

```text
Bot ... connected
connection open
```

如果没有，重新双击：

```text
start_bot_background.bat
```

如果弹二维码，扫码登录。

### 上传失败，提示识别 URL 失败

说明 NapCat 收到了 Windows 路径而不是容器路径。

当前代码已经修为 `/app/napcat/shared/xxx.zip`。如果换电脑后出现，检查：

```text
config\docker-compose.napcat.yml
qqbot_jm.py
```

### 私聊只返回本机路径

说明 `upload_private_file` 接口失败。文件仍在：

```text
downloads\zip
```

### 群文件上传失败

检查机器人账号是否有该群上传文件权限，或者文件是否过大。

### 重新登录

如果 QQ 登录掉了，启动脚本会自动打开：

```text
logs\napcat-qrcode.png
```

扫码后继续。

## 换电脑步骤

1. 安装 Python 3.12+
2. 安装 Docker Desktop 并启动
3. 进入项目根目录
4. 创建虚拟环境：

```powershell
python -m venv .venv
```

5. 安装依赖：

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m pip install -r requirements-qqbot.txt
```

6. 拉取 NapCat 镜像：

```powershell
docker pull mlikiowa/napcat-docker:latest
```

7. 双击启动：

```text
start_bot_background.bat
```

8. 扫码登录 QQ
9. 群聊或私聊发送：

```text
/jm 350234
```
