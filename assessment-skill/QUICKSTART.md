# 快速开始指南

## 🚀 30秒快速上手

### 第一步：安装依赖
```bash
cd assessment-skill
pip install -r requirements.txt
```

### 第二步：运行测试
```bash
python main.py ../总助九段胜任力专业测评--3.0_20260120162836.xlsx -o ../test_output
```

### 第三步：查看报告
打开生成的 `.txt` 文件查看测评报告！

---

## 📋 使用说明

### 基本用法

```bash
python main.py <Excel文件路径> [-o 输出目录]
```

### 参数说明

| 参数 | 说明 | 是否必填 | 默认值 |
|------|------|----------|--------|
| Excel文件路径 | 测评数据Excel文件的完整路径 | 是 | - |
| -o, --output | 报告输出目录 | 否 | 当前目录 |

### 使用示例

**示例1：生成报告到当前目录**
```bash
python main.py 测评数据.xlsx
```

**示例2：生成报告到指定目录**
```bash
python main.py 测评数据.xlsx -o ./reports
```

**示例3：使用绝对路径**
```bash
python main.py /Users/data/test.xlsx -o /Users/output/
```

---

## 📊 Excel数据格式要求

Excel文件必须包含以下列：

### 基本信息（必需）
- `序号`：测评者序号
- `微信昵称`：测评者昵称
- `测评时间：`：测评时间

### 能力得分（必需）
- `【执行力】`
- `【协调力】`
- `【优化力】`
- `【统筹力】`
- `【预见力】`
- `【业务力】`
- `【财务力】`
- `【领导力】`
- `【决策力】`

---

## 📁 语料库文件位置

确保以下文件存在于 `assessment-skill` 目录的**父目录**中：

```
测评报告/
├── assessment-skill/          ← skill目录
│   ├── main.py
│   ├── skill.json
│   └── README.md
├── 综合段位语料库.txt          ← 语料库文件（在这里）
├── 能力维度、等级及分数解读语料库.txt  ← 语料库文件（在这里）
└── 个性化发展行动计划语料库].txt     ← 语料库文件（在这里）
```

---

## 📄 输出文件命名规则

生成的报告文件名格式：

```
九段总助测评结果报告-NLZ100{序号}-{微信昵称}-{段位}.txt
```

**示例**：
```
九段总助测评结果报告-NLZ10074-55会好运常伴💖-五段.txt
```

---

## ⚙️ 系统配置

### 修改段位分数范围

编辑 `main.py` 中的 `rank_ranges`：

```python
self.rank_ranges = {
    "一段": (0, 15.09),
    "二段": (15.1, 30.09),
    # ... 修改其他段位范围
}
```

### 修改等级评分标准

编辑 `main.py` 中的 `grade_thresholds`：

```python
self.grade_thresholds = {
    8: {"A": (7.2, 8.0), "B": (6.4, 7.1), ...},
    10: {"A": (9.0, 10.0), "B": (8.0, 8.9), ...},
    12: {"A": (10.8, 12.0), "B": (9.6, 10.7), ...}
}
```

---

## 🔧 常见问题

### Q1: 提示找不到语料库文件？
**A**: 确保语料库文件放在 `assessment-skill` 目录的父目录中。

### Q2: 报告中缺少详细描述？
**A**: 检查语料库文件格式是否正确，确保每项能力的等级描述完整。

### Q3: 如何批量处理多个Excel？
**A**: 编写一个简单的循环脚本：
```python
from main import AssessmentReportGenerator
import glob

generator = AssessmentReportGenerator()
for excel_file in glob.glob("*.xlsx"):
    generator.generate_report(excel_file, "./reports")
```

---

## 💡 提示

- ✅ 确保Excel文件中的能力得分列为数字格式
- ✅ 总分计算是所有9个能力得分之和
- ✅ 段位和等级都是自动计算的，无需手动输入
- ✅ 报告生成后会显示文件路径和基本信息

---

**需要帮助？** 查看 `README.md` 获取详细文档
