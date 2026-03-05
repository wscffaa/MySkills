---
name: docker-nvml-monitor
description: Docker 容器 GPU 监控自动重启。当用户提到"Docker 容器 NVML 错误"、"GPU 容器自动重启"、"nvidia-smi 监控"、"容器 GPU 检测"时使用。
---

# Docker NVML 监控和自动重启

## 核心脚本

直接使用 `scripts/check_nvml_restart_docker.sh` 模板,该脚本通过 `docker exec nvidia-smi` 实时检测容器内 GPU 状态。

## 执行流程

1. 读取 `scripts/check_nvml_restart_docker.sh`
2. 将 `CONTAINER_PLACEHOLDER` 替换为实际容器名(如 `"feifan" "zhq"`)
3. 部署到服务器 `/root/check_nvml_restart_docker.sh`
4. 设置权限: `chmod +x`
5. 配置 crontab: `*/5 * * * * /root/check_nvml_restart_docker.sh`
6. 测试并查看日志

## 输出格式

```
A100 服务器上已给 <容器名> 容器配置对应脚本,目前已经配置的容器有:<列表>

脚本位置: /root/check_nvml_restart_docker.sh
日志位置: /var/log/nvml_check.log
检查频率: 每 5 分钟
查看日志: ssh <server> "sudo tail -f /var/log/nvml_check.log"
```
