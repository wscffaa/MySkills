# Antigravity Proxy Skill

自动配置 Antigravity 使用 mihomo 代理，解决 AI 聊天连接失败问题。

**使用场景**：Mac 本地使用 Antigravity，远程连接 Docker 容器服务器开发，通过代理访问 AI 大模型。

## 功能

- 自动检测环境（mihomo、graftcp、Antigravity）
- 安装并编译 graftcp（如果需要）
- 配置 Antigravity 劫持脚本
- **自动检测版本更新**：每 5 分钟自动检测 Antigravity 新版本并应用代理配置
- 验证代理连接

## 使用方法

```bash
/antigravity-proxy
```

## 工作原理

1. **mihomo**：提供 SOCKS5 代理（端口 7891）
2. **graftcp**：劫持 TCP 连接
3. **劫持脚本**：替换 `language_server_linux_x64`，强制所有连接走代理
4. **cron 自动更新**：每 5 分钟检测 Antigravity 版本更新并自动应用配置

## 自动化特性

- ✅ **mihomo**：通过 supervisor 自动启动
- ✅ **graftcp-local**：通过劫持脚本自动启动
- ✅ **版本检测**：cron 任务每 5 分钟自动检测并应用到新版本
- ✅ **容器重启**：所有组件自动恢复

## 注意事项

- 需要 mihomo 已经运行
- 无需 sudo 权限
- 首次运行后无需手动干预，Antigravity 更新会自动处理
- 日志文件：`/tmp/antigravity-proxy.log`
