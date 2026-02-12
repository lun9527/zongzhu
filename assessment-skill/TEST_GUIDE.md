# 📋 测试指南

## 🚀 快速测试（3步）

### 第1步：安装依赖
```bash
cd /Users/yanzhanglun/Desktop/测评报告/assessment-skill
pip install -r requirements.txt
```

### 第2步：运行测试
```bash
python main.py "../总助九段胜任力专业测评--3.0_20260120162836.xlsx" -o "../test_output"
```

### 第3步：查看报告
```bash
open "../test_output/九段总助测评结果报告-NLZ10074-55会好运常伴💖-五段.pdf"
```

---

## 📊 完整测试步骤

### 测试1：基本功能测试

**目的**：验证能否正常生成PDF报告

```bash
# 1. 进入skill目录
cd /Users/yanzhanglun/Desktop/测评报告/assessment-skill

# 2. 运行生成命令
python main.py "../总助九段胜任力专业测评--3.0_20260120162836.xlsx" -o "../test_output"

# 3. 查看输出
# 预期输出：
# ✅ PDF报告已生成: ../test_output/九段总助测评结果报告-NLZ10074-55会好运常伴💖-五段.pdf
#    段位: 五段
#    总分: 46.26

# 4. 打开PDF
open "../test_output/九段总助测评结果报告-NLZ10074-55会好运常伴💖-五段.pdf"
```

**验证点**：
- ✅ PDF文件成功生成
- ✅ 文件大小合理（应该在150-250KB之间）
- ✅ 中文显示正常（无乱码）
- ✅ 封面显示段位（五段）
- ✅ 雷达图正常显示
- ✅ 能力分析内容完整

---

### 测试2：内容准确性测试

**目的**：验证报告内容是否正确

打开生成的PDF，对比Excel数据：

```bash
# 查看Excel数据
python3 << EOF
import pandas as pd
df = pd.read_excel('../总助九段胜任力专业测评--3.0_20260120162836.xlsx')
row = df.iloc[0]
print(f"序号: {row['序号']}")
print(f"昵称: {row['微信昵称']}")
print(f"总分: {row['测评得分']}")
print(f"\n各能力得分:")
print(f"执行力: {row['【执行力】']} (应该为D级)")
print(f"协调力: {row['【协调力】']} (应该为C级)")
print(f"优化力: {row['【优化力】']} (应该为D级)")
print(f"统筹力: {row['【统筹力】']} (应该为D级)")
print(f"预见力: {row['【预见力】']} (应该为E级)")
print(f"业务力: {row['【业务力】']} (应该为C级)")
print(f"财务力: {row['【财务力】']} (应该为D级)")
print(f"领导力: {row['【领导力】']} (应该为E级)")
print(f"决策力: {row['【决策力']} (应该为E级)")
EOF
```

**验证点**：
- ✅ 序号、昵称、时间是否正确
- ✅ 总分是否为46.26
- ✅ 段位是否为"五段"
- ✅ 9个能力得分是否正确
- ✅ 能力等级是否正确（A/B/C/D/E）

---

### 测试3：多文件测试

**目的**：测试处理Excel中多行数据的能力

```bash
# 创建测试脚本
cat > test_batch.py << 'EOF'
import pandas as pd
from main import AssessmentReportGenerator

# 读取Excel
df = pd.read_excel('../总助九段胜任力专业测评--3.0_20260120162836.xlsx')

# 创建生成器
generator = AssessmentReportGenerator()

# 处理前3行数据
for idx in range(min(3, len(df))):
    print(f"\n处理第 {idx+1} 条数据...")

    # 创建临时Excel文件（只包含一行）
    temp_df = df.iloc[idx:idx+1]
    temp_file = f'../test_output/temp_{idx}.xlsx'
    temp_df.to_excel(temp_file, index=False)

    # 生成报告
    try:
        output = generator.generate_report(temp_file, '../test_output')
        print(f"✅ 成功: {output}")
    except Exception as e:
        print(f"❌ 失败: {e}")

print("\n批处理测试完成！")
EOF

# 运行批处理测试
python test_batch.py
```

---

### 测试4：对比模板测试

**目的**：对比生成的PDF和模板PDF的差异

```bash
# 并排打开两个PDF
open "../test_output/九段总助测评结果报告-NLZ10074-55会好运常伴💖-五段.pdf"
open "../九段总助测评结果报告-NLZ10074-55会好运常伴💖-五段.pdf"
```

**对比要点**：
| 项目 | 模板 | 生成 | 备注 |
|------|------|------|------|
| 封面布局 | 有 | 有 | 对比样式 |
| 段位显示 | 大号 | 大号 | 对比大小和位置 |
| 雷达图 | 有 | 有 | 对比样式和数据 |
| 能力分析 | 有 | 有 | 对比内容和格式 |
| 行动计划 | 有 | 有 | 对比建议内容 |

---

### 测试5：错误处理测试

**目的**：测试异常情况的处理

```bash
# 测试1：文件不存在
python main.py "不存在的文件.xlsx" -o "../test_output"
# 预期：显示错误信息

# 测试2：空文件
echo "测试空文件处理"

# 测试3：格式错误的Excel
# （可以手动创建一个格式错误的Excel测试）

# 测试4：生成txt格式
python main.py "../总助九段胜任力专业测评--3.0_20260120162836.xlsx" -o "../test_output" --format txt
# 预期：生成txt文件而不是pdf
```

---

## ✅ 测试检查清单

使用这个清单逐项检查：

### 功能检查
- [ ] PDF文件成功生成
- [ ] 文件命名格式正确（NLZ100+序号+昵称+段位）
- [ ] 中文显示正常，无乱码
- [ ] 封面信息完整（序号、昵称、时间、段位）
- [ ] 三部分内容完整

### 内容检查
- [ ] 段位计算正确（46.26分 → 五段）
- [ ] 9个能力得分准确
- [ ] 能力等级判定正确
- [ ] 段位释义显示正确
- [ ] 雷达图显示正常

### 格式检查
- [ ] 字体大小合适
- [ ] 颜色搭配合理
- [ ] 表格对齐正确
- [ ] 页面布局美观

### 性能检查
- [ ] 生成速度合理（<10秒）
- [ ] 文件大小合理（150-250KB）
- [ ] 内存占用正常

---

## 🔧 常见问题排查

### 问题1：ImportError
```bash
# 解决方案：重新安装依赖
pip install --upgrade reportlab matplotlib pandas openpyxl Pillow
```

### 问题2：中文乱码
```bash
# 检查字体文件
ls -la /System/Library/Fonts/PingFang.ttc
ls -la /System/Library/Fonts/STHeiti*

# 如果字体不存在，修改pdf_generator_v2.py中的字体路径
```

### 问题3：雷达图不显示
```bash
# 检查matplotlib
python3 -c "import matplotlib; print(matplotlib.__version__)"

# 重新安装matplotlib
pip install --upgrade matplotlib
```

### 问题4：Excel读取失败
```bash
# 检查openpyxl
python3 -c "import openpyxl; print(openpyxl.__version__)"

# 重新安装
pip install --upgrade openpyxl
```

---

## 📝 测试报告模板

测试完成后，填写这个报告：

```
测试日期：____
测试人：____
Excel文件：总助九段胜任力专业测评--3.0_20260120162836.xlsx

### 测试结果
✅/❌ PDF成功生成
✅/❌ 中文显示正常
✅/❌ 内容准确无误
✅/❌ 格式符合要求

### 发现的问题
1. ____
2. ____

### 改进建议
1. ____
2. ____
```

---

## 🎯 一键测试脚本

创建一个自动化测试脚本：

```bash
#!/bin/bash
echo "========================================="
echo "  九段总助测评报告生成系统 - 自动测试"
echo "========================================="
echo ""

# 进入目录
cd /Users/yanzhanglun/Desktop/测评报告/assessment-skill

# 测试1：生成PDF
echo "【测试1】生成PDF报告..."
python main.py "../总助九段胜任力专业测评--3.0_20260120162836.xlsx" -o "../test_output"

if [ $? -eq 0 ]; then
    echo "✅ PDF生成成功"
else
    echo "❌ PDF生成失败"
    exit 1
fi

# 测试2：检查文件
echo ""
echo "【测试2】检查生成的文件..."
ls -lh "../test_output/"/*.pdf

# 测试3：打开报告
echo ""
echo "【测试3】打开PDF报告..."
open "../test_output/九段总助测评结果报告-NLZ10074-55会好运常伴💖-五段.pdf"

echo ""
echo "========================================="
echo "  测试完成！请查看生成的PDF报告"
echo "========================================="
```

保存为`test.sh`，然后运行：
```bash
chmod +x test.sh
./test.sh
```

---

**需要帮助？**
如果测试中遇到问题，请告诉我具体的错误信息，我会帮你解决！
