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

### 下载和打包配置

```text
option_zip.yml
```

作用：

- 指定下载目录为 `downloads`
- 下载完成后压缩到 `downloads\zip`
- 删除原图片目录，只保留 zip

### NapCat / Docker 配置

```text
docker-compose.napcat.yml
configure_napcat_onebot.ps1
configure_napcat_onebot.bat
```

作用：

- 用 Docker 启动 NapCat
- 把 `downloads\zip` 挂载到容器内 `/app/napcat/shared`
- 配置 NapCat 反向 WebSocket 连接到 NoneBot：

```text
ws://host.docker.internal:8080/onebot/v11/ws
```

### 启动/停止/日志脚本

```text
start_bot_background.ps1
start_bot_background.bat
start_all_qqbot.ps1
start_all_qqbot.bat
stop_bot_background.ps1
stop_bot_background.bat
tail_bot_log.ps1
tail_bot_log.bat
open_napcat_qrcode.bat
```

其中最常用的是：

```text
start_bot_background.bat
stop_bot_background.bat
tail_bot_log.bat
```

`start_all_qqbot.*` 目前只是兼容旧名字，内部调用同一套后台启动逻辑。

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
jmcomic-bot.pid
napcat-qrcode.png
```

说明：

- `.venv` 是 Python 虚拟环境，可以重新创建
- `downloads` 是下载产物，可以删除
- `logs` 是机器人日志，可以删除
- `tools\napcat-docker` 是 NapCat 配置、QQ 登录数据和挂载目录
- `jmcomic-bot.pid` 是后台进程 pid 文件，可以删除
- `napcat-qrcode.png` 是登录二维码临时图片，登录成功后会自动删除

换电脑时，如果想保留 QQ 登录态，可以尝试一起复制：

```text
tools\napcat-docker
```

但 QQ 登录态不一定能跨机器复用。更稳的方式是在新电脑重新扫码登录。

## Git/提交建议

如果要提交代码，建议提交：

```text
QQBOT_SETUP.md
qqbot_jm.py
requirements-qqbot.txt
option_zip.yml
docker-compose.napcat.yml
*.bat
*.ps1
```

不建议提交：

```text
.venv
downloads
logs
tools\napcat-docker
jmcomic-bot.pid
napcat-qrcode.png
```

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
docker-compose.napcat.yml
```

机器人代码：

```text
qqbot_jm.py
```

JMComic 下载和 zip 配置：

```text
option_zip.yml
```

NapCat OneBot 自动配置脚本：

```text
configure_napcat_onebot.ps1
```

## 启动

双击：

```text
start_bot_background.bat
```

它会自动：

- 启动 NapCat Docker 容器
- 如果 QQ 未登录，生成并打开根目录下的二维码图片：

```text
napcat-qrcode.png
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

## Docker 挂载

`docker-compose.napcat.yml` 把本机 zip 目录挂进容器：

```text
./downloads/zip:/app/napcat/shared
```

机器人上传文件时使用容器内路径：

```text
/app/napcat/shared/xxx.zip
```

这是必须的，因为 NapCat 在 Docker 里，不能直接识别 Windows 路径。

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
docker-compose.napcat.yml
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
napcat-qrcode.png
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
