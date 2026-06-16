# jmcomic-qqbot-wrapper

这是一个基于开源项目 `hect0x7/JMComic-Crawler-Python` 的本地 QQ Bot 集成封装。

原项目地址：

```text
https://github.com/hect0x7/JMComic-Crawler-Python
```

原项目提供 `jmcomic` Python API 和命令行下载能力。本仓库没有把原项目声明为自己的作品，只是在原项目外面加了一层本地机器人调用逻辑：

- NapCat 负责登录 QQ 并提供 OneBot v11 连接
- NoneBot2 负责接收 QQ 群聊/私聊消息
- `jmcomic` 负责实际下载
- 下载完成后自动打包 zip
- 群聊触发时上传群文件
- 私聊触发时直接私聊发送 zip 文件
- 自动同意 QQ 好友申请

原项目 License 为 MIT。请继续遵守原项目许可证和原作者声明。

## 使用

启动：

```text
start_bot_background.bat
```

停止：

```text
stop_bot_background.bat
```

查看日志：

```text
tail_bot_log.bat
```

群聊或私聊发送：

```text
/jm 350234
```

## 文档

完整环境、换电脑步骤、脚本说明、常见问题见：

```text
QQBOT_SETUP.md
```

原项目 README 已保留为：

```text
README_UPSTREAM.md
```

## 目录说明

核心新增文件：

```text
qqbot_jm.py
requirements-qqbot.txt
option_zip.yml
docker-compose.napcat.yml
start_bot_background.bat
stop_bot_background.bat
tail_bot_log.bat
QQBOT_SETUP.md
```

运行产物不会提交：

```text
.venv
downloads
logs
tools
napcat-qrcode.png
jmcomic-bot.pid
```

## 免责声明

本仓库仅用于本地自动化与学习用途。原项目核心代码、接口封装和文档主体来自 `hect0x7/JMComic-Crawler-Python`，本仓库主要维护 QQ Bot wrapper 相关脚本与配置。
