
# 🎵 MP3-to-Winsound Converter

## 🚀 项目概述

将 MP3 音频文件转换为 Windows 系统蜂鸣音效 (`winsound.Beep`) 的 Python 工具，通过分析音频频谱特征，实现主板蜂鸣器播放音乐。

## ✨ 核心功能

### 🎛️ 音频处理引擎
| 功能 | 描述 |
|------|------|
| 频谱分析 | 采用 STFT 算法 (帧长 2048) |
| 多模式处理 | 固定/动态/自动三种模式 |
| 智能优化 | 自动合并短音调 |

### 📊 可视化界面
- ✅ 实时频谱曲线
- ✅ 音符持续时间分布
- ✅ 带时间戳的日志系统

## 🛠️ 安装使用

### 1. 安装依赖
```bash
pip install librosa numpy soundfile matplotlib
```

### 2. 运行程序
```bash
python main.py
```

### 3. 界面操作
1. 选择 MP3 文件
2. 设置处理参数
3. 生成播放代码

## 📦 版本演进

### v4.0 (当前版本)
```mermaid
graph LR
    A[MP3输入] --> B{自动检测}
    B -->|低频| C[Sleep静音]
    B -->|有效音频| D[Beep生成]
```

**新增特性：**
- 智能静音检测 (阈值 400Hz)
- 三合一处理算法
- 集成代码预览面板

### v3.0
```python
# 动态处理核心
def process_dynamic():
    freq_avg = sum(freq*dt)/sum(dt)  # 加权平均
    if diff(freq) < 20Hz:            # 可调阈值
        merge_segments()
```

### v2.0
- 实时进度条
- 动态频率处理

### v1.0
- 基础转换功能

## 📜 技术规格

| 组件 | 要求 |
|------|------|
| Python | ≥ 3.7 |
| Librosa | ≥ 0.8.0 |
| 内存 | ≥ 512MB |

## 📁 项目结构

```
mp3-2-winsound/
├── main4.1/           # 最新版本
│   ├── main.py        # 主程序
│   ├── function.py    # 核心功能
│   └── favicon.ico    # 图标
├── main4.0.py         # v4.0版本
├── main3.0.py         # v3.0版本
├── main2.0.py         # v2.0版本
├── main1.0.py         # v1.0版本
└── README.md          # 说明文档
```

---

*由AI生成*
```
