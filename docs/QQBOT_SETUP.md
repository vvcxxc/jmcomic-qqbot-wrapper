# JMComic QQ Bot Setup

本文档记录在原项目基础上追加 QQ Bot 集成后的运行环境、依赖、启动方式和使用方式，方便换电脑或开启新对话时快速接手。

> **当前运行方案：NapCatQQ-Desktop（Windows 原生 GUI），不使用 Docker。** 本文档已按原生方案为准，Docker 相关内容已移除。

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

本地这次做的事情只是：在原项目外面额外加了一套 QQ Bot / NapCat / NoneBot 的调用层，让 QQ 消息可以触发原项目的 `jmcomic` 下载能力。

也就是说：

- 原项目 `JMComic-Crawler-Python` 的核心功能和版权归原作者/原仓库
- 我们没有把原项目声明成自己的作品
- 我们只是做了本地二次集成：QQ Bot、启动脚本、NapCat 配置、zip 下载配置和这份说明文档
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
- 机器人掉线时发邮件告警（详见下文“掉线告警”）

## 运行架构

| 部件 | 跑在哪 | 谁来管 |
|---|---|---|
| **NapCat**（QQ 协议端，负责登录 + 反向 WebSocket） | NapCatQQ-Desktop 原生程序 | Desktop GUI 自己（起停、定时重启都在它界面里） |
| **Python 机器人**（`qqbot_jm.py`，接消息、调下载、发文件） | 本机 `.venv` 后台进程 | 本仓库的 `.bat` 脚本 |

两者在**同一台 Windows** 上，NapCat 通过反向 WebSocket 主动连到 Python：

```text
ws://127.0.0.1:8080/onebot/v11/ws
```

机器人端口、token 由 `.env` 决定：

```text
HOST=127.0.0.1
PORT=8080
DRIVER=~fastapi
ONEBOT_ACCESS_TOKEN=jmcomic_local_bot
```

## 首次配置（换电脑时做一次）

### 1. 安装并运行 NapCatQQ-Desktop

安装包已随项目保存在 `installers\`（如 `installers\NapCatQQ-Desktop-2.2.8-x64.msi`，直接双击安装即可，省得重新下载——官方下载偶尔被拦/报风险）。

- 官方地址备用：<https://github.com/NapNeko/NapCatQQ-Desktop>
- `installers\` 已 gitignore（不进仓库），换电脑时随项目文件夹一起拷贝。

### 2. 启动 NapCat 实例并登录 QQ

在 Desktop 里创建/启动一个 NapCat 实例，**扫码登录 QQ**（正常只登这一次；登录较频繁有被风控的风险，能不重登就不重登）。

### 3. 配置反向 WebSocket（连到机器人）

打开 NapCat WebUI：

```text
http://127.0.0.1:6099/webui
```

进入 **网络配置 → 新建 → WebSocket 客户端**，启用并填写（**以下值照抄**）：

| 字段 | 值 |
|---|---|
| URL | `ws://127.0.0.1:8080/onebot/v11/ws` |
| **Token** | **`jmcomic_local_bot`**（必须与 `.env` 里 `ONEBOT_ACCESS_TOKEN` 完全一致，否则机器人返回 403） |
| messagePostFormat | `array` |
| reportSelfMessage | `true`（开启） |

保存。配置会写进 Desktop 自己的实例配置文件（形如 `onebot11_<QQ号>.json`），下次开机自动生效。

### 4.（可选）开机自启 / 定时重启

在 Desktop 界面里可开启“开机自启”“定时重启”，无人值守时更稳。

## 启动

确认 NapCatQQ-Desktop 已运行且 QQ 已登录，然后双击根目录的：

```text
start_bot_background.bat
```

它**只启动后台 Python 机器人**（不碰 NapCat）。看日志：双击 `tail_bot_log.bat`，出现下面内容即连接成功（NapCat 约 30 秒内反向连上）：

```text
Bot 3431188215 connected
connection open
```

## 停止

双击：

```text
stop_bot_background.bat
```

只停后台 Python 机器人。NapCat 不受影响（要停 NapCat 去 Desktop 界面操作）。

## 热重启（改了代码后用）

改了 `qqbot_jm.py` 等 Python 代码后，双击：

```text
reload_bot.bat
```

它**只杀掉并重启 Python 进程，完全不碰 NapCat**。所以 **QQ 登录态不受影响、不会弹二维码、不会增加登录次数**（频繁登录有被风控的风险）。NapCat 会在约 30 秒内自动反向重连。

> 启动/热重启脚本都会先按命令行特征杀掉所有残留的 `qqbot_jm` Python 进程，再启动新进程——避免出现僵尸进程占着 8080 端口导致 403 的情况。

## 根目录脚本与实现

为保持根目录整洁，**根目录只放几个常用的双击入口 `.bat`**：

```text
start_bot_background.bat   启动后台 Python 机器人
stop_bot_background.bat    停止后台 Python 机器人
reload_bot.bat             热重启：只重启 Python
tail_bot_log.bat           查看实时日志
```

它们的具体实现（`.ps1`）收在 `scripts\` 目录里：

```text
scripts\start_bot_background.ps1
scripts\stop_bot_background.ps1
scripts\reload_bot.ps1
scripts\tail_bot_log.ps1
```

平时只需双击根目录那几个 `.bat`，不用进 `scripts\`。`.bat` 会自动调用 `scripts\` 下对应的 `.ps1`。

> 不要双击 `.ps1`（会被当记事本打开）。一律双击 `.bat`。

## 使用

### 好友申请

机器人收到 QQ 好友申请会自动同意，不需要手动确认。

### 群聊

在群里发送：

```text
/jm 350234
```

效果：下载 → 打包 zip → 上传群文件。

### 私聊

私聊机器人发送：

```text
/jm 350234
```

效果：下载 → 打包 zip → 私聊发送 zip 文件；如果私聊文件发送失败，会回复运行机器人的电脑上的文件路径。

> 注意：下载和打包发生在运行机器人的电脑上，不是在发消息的电脑上。

## 下载与打包配置

下载/打包行为由 `config\option_zip.yml` 控制，当前会：

- 使用 `api` 客户端
- 下载到 `downloads`
- 下载完成后打包到 `downloads\zip`
- 删除原图片文件夹，只保留 zip

zip 文件名示例：

```text
JM350234-董卓 上+下.zip
```

## 文件上传与文件名处理

NapCat 与机器人在同一台 Windows 上，上传时机器人直接把 zip 的**本机真实路径**转成 `file://` URI 交给 NapCat：

```text
file:///D:/.../downloads/zip/xxx.zip
```

之所以用 `file://` 而不是裸路径：NapCat 对 `file` 字段做 `new URL()` 解析，裸路径会报 `识别URL失败 (retcode=1200)`。`shared_file_uri()` 用 `Path.as_uri()` 生成带百分号编码的合法 URI。

上传前 `sanitize_zip_name()` 还会清洗文件名：

1. **过滤特殊字符**：去掉 `♥ 〜 （） ○ ・` 等符号（替换成空格再合并），保留中日文、字母数字、空格和 `[]()-_.`。让文件名更干净，避开个别字符引发的问题。
2. **按字节截断保险**：整个文件名（含 `.zip`）截断到 **200 字节**以内（车号开头和 `.zip` 一定保留，只截标题尾部），防止超长路径出问题。原生 Windows 下其实很宽松，但留着无妨。

## 并发与排队

所有下载任务**共用同一个 `downloads` 目录**，且每个任务开始时会先清空它（省磁盘）。为避免多个任务同时跑时互相删文件、或把 zip 发错人，机器人用一把全局锁（`qqbot_jm.py` 里的 `download_lock`）把**整个“下载 + 上传”过程串行化**：

- 同一时间只有一个任务在下载/上传
- 后到的 `/jm` 请求会**自动排队**，按先来后到依次执行
- 排队中的请求会先收到提示：`前面有任务在下载，已排队，请稍候…`

注意锁会持有到**上传完成**才释放——因为上传读取的是 `downloads\zip` 里的文件，必须等它发完，否则下一个任务的清空会把 zip 删掉。所以单个任务较慢时，后面的人需要多等一会，这是正常现象。

> 不建议为了“加速”改成并行下载：下载是网络/磁盘密集型，并行快不了多少，反而会因为短时间大量请求放大被 QQ 风控的概率。

## 掉线告警（邮件）

机器人在服务器上无人值守时，QQ 登录态被踢、或 NapCat 挂掉都不会有人立刻发现。为此加了一套**邮件告警**：检测到掉线就给你发邮件。

### 触发条件（三重检测）

1. 收到 NapCat 转发的 `bot_offline` 通知（QQ 账号被服务端踢，最常见）
2. OneBot 反向 WebSocket 断开（NapCat 退出）
3. 定时轮询 `get_status` 兜底（默认每 180 秒，发现 `online=false` 即告警）

任一触发都会发一封邮件，并带 30 分钟防抖（`min_interval_seconds`），避免短时间内重复轰炸；机器人重新连上后防抖自动复位，下次掉线可立即告警。

### 配置方式（base + local 分层，类似 .env / .env.local 概念）

> 这里的 base/local 是本功能自带的两个 JSON 文件，和 NoneBot 自己的 `.env` 无关。

```text
config\alert_config.json         base：进仓库，只放结构和非密钥默认值
config\alert_config.local.json   local：不进仓库（已 gitignore），放真实邮箱密钥
```

读取规则：先读 base，再用 local **覆盖同名字段**。local 里只需填你要改的字段（一般就是邮箱几项），其余继承 base。两个文件里 `smtp_user`/`smtp_pass` 都为空时，掉线只记日志、**不发邮件**（等于关闭，不报错）。以 `_` 开头的键是注释，程序忽略。

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
3. 热重启机器人（`reload_bot.bat`）生效。

授权码说明：QQ/163 邮箱要先在邮箱设置里**开启 SMTP 服务并生成授权码**，填授权码而不是邮箱登录密码。

### 收到告警后怎么重新登录

1. 在 NapCatQQ-Desktop 界面里重新登录，用**手机 QQ 扫码**；
2. 或打开 NapCat WebUI（`http://IP:6099/webui`）点重新登录扫码。

## 关键文件

```text
qqbot_jm.py                      机器人代码（入口）
.env                             机器人端口 + token（ONEBOT_ACCESS_TOKEN=jmcomic_local_bot）
config\option_zip.yml            JMComic 下载和 zip 配置
config\alert_config.json         掉线告警 base 配置
config\alert_config.local.json   掉线告警密钥（gitignore）
requirements-qqbot.txt           QQ 机器人 Python 依赖
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

主要依赖：`jmcomic`、`nonebot2`、`nonebot-adapter-onebot`。当前 Python 版本 `3.12.10`，虚拟环境在 `.venv`。

## 运行产物

这些是运行过程中生成的，不属于原项目核心代码，可删除/可重建：

```text
.venv         Python 虚拟环境，可重建
downloads     下载产物，可删
logs          机器人日志和运行时文件，可删
```

`logs\jmcomic-bot.pid` 是后台进程 pid 文件；机器人日志在 `logs\jmcomic-bot.log` / `logs\jmcomic-bot.err.log`。

## 换电脑步骤

1. 安装 Python 3.12+
2. 拷贝整个项目文件夹（含 `installers\`）到新电脑
3. 进入项目根目录，创建虚拟环境并装依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m pip install -r requirements-qqbot.txt
```

4. 安装并配置 NapCatQQ-Desktop（见上文“首次配置”：装 `installers\` 里的安装包 → 扫码登录 → 配反向 WS，token 填 `jmcomic_local_bot`）
5. 双击 `start_bot_background.bat`
6. 群聊或私聊发 `/jm 350234` 测试

## 常见问题

### 发消息没反应

先看日志 `tail_bot_log.bat`，确认有 `Bot ... connected` 和 `connection open`。没有就：

- 确认 NapCatQQ-Desktop 在运行且 QQ 在线；
- 确认 WebUI 里反向 WS 客户端是“已连接”状态、token 是 `jmcomic_local_bot`；
- 双击 `reload_bot.bat` 重启 Python。

### 返回 403

机器人和 NapCat 的 token 不一致。检查 `.env` 的 `ONEBOT_ACCESS_TOKEN` 与 Desktop WebUI 里反向 WS 的 token 是否都为 `jmcomic_local_bot`。也可能是残留的旧 Python 进程占着 8080——`reload_bot.bat` 会清掉再重启。

### 上传失败 / 识别 URL 失败

当前代码用 `file://` URI 上传（`shared_file_uri`）。若换电脑后出现，检查 `qqbot_jm.py` 中 `shared_file_uri` 是否仍返回 `(DOWNLOAD_DIR/"zip"/name).as_uri()`，以及 zip 是否真的在 `downloads\zip` 下。

### 私聊只返回本机路径

说明 `upload_private_file` 接口失败。文件仍在 `downloads\zip`。

### 群文件上传失败

检查机器人账号是否有该群上传文件权限，或文件是否过大。
