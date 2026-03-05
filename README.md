# MySkills

个人技能库,包含 Claude Skills 和 Codex Skills。

## 目录结构

```
MySkills/
├── ClaudeSkills/          # Claude AI 技能集合
│   ├── docker-nvml-monitor/    # Docker 容器 GPU 监控自动重启
│   ├── docx-template-reformatter/
│   ├── midscene/
│   └── omo-skills/
├── CodexSkills/           # Codex 技能集合
│   ├── do/
│   ├── remotion-best-practices/
│   ├── skill-creator/
│   └── skill-installer/
```

## Claude Skills

### docker-nvml-monitor
Docker 容器 NVML 错误监控和自动重启工具。

**功能特点:**
- 使用 `docker exec nvidia-smi` 实时检测容器内 GPU 状态
- 检测到 NVML 错误时,等待 GPU 进程完成后再重启容器
- 支持多容器监控
- 自动记录日志

**使用场景:**
- GPU 容器出现 NVML ERROR
- 需要自动化监控和恢复 GPU 容器
- 避免实验中断

## Codex Skills

包含多个 Codex 相关的技能工具。

## 贡献

欢迎提交 Issue 和 Pull Request。

## 许可证

MIT License
