# develoip-copilot CLI 工具规范

## 设计原则

1. **每个工具首先是独立 Python CLI**，不依赖 OMP
2. 通过 `argparse` 接受参数，支持 `--json` 输出
3. 文件不存在时返回非零退出码
4. 可脱离 OMP 独立运行和测试

## 调用规范

```bash
python tools/<category>/<tool>.py <args>
python tools/<category>/<tool>.py <args> --json
```

## 目录组织

```
tools/
├── rtl/          # RTL 解析工具
├── simulation/   # 仿真运行和日志解析
├── waveform/     # 波形提取
├── timing/       # 时序报告解析
├── model_compare/# 模型对比
├── firmware/     # 固件分析
└── workspace/    # 工作区辅助
```
