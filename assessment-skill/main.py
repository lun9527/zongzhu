#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
九段总助胜任力专业测评报告生成系统
"""

import os
import sys
import re
import pandas as pd
from datetime import datetime
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入PDF生成器
from pdf_generator_v4 import PDFReportGeneratorV4 as PDFReportGenerator


class AssessmentReportGenerator:
    """测评报告生成器"""

    def __init__(self, config_path=None):
        """初始化生成器"""
        # 段位分数范围
        self.rank_ranges = {
            "一段": (0, 15.09),
            "二段": (15.1, 30.09),
            "三段": (30.1, 40.09),
            "四段": (40.1, 45.09),
            "五段": (45.1, 55.09),
            "六段": (55.1, 70.09),
            "七段": (70.1, 75.09),
            "八段": (75.1, 85.09),
            "九段": (85.1, 90)
        }

        # 能力维度配置
        self.abilities = {
            "执行力": {"max_score": 8, "group": "核心基石"},
            "协调力": {"max_score": 8, "group": "核心基石"},
            "优化力": {"max_score": 8, "group": "核心基石"},
            "统筹力": {"max_score": 10, "group": "价值引擎"},
            "预见力": {"max_score": 10, "group": "价值引擎"},
            "业务力": {"max_score": 10, "group": "价值引擎"},
            "财务力": {"max_score": 12, "group": "领导潜能"},
            "领导力": {"max_score": 12, "group": "领导潜能"},
            "决策力": {"max_score": 12, "group": "领导潜能"}
        }

        # 等级判定阈值
        self.grade_thresholds = {
            8: {"A": (7.2, 8.0), "B": (6.4, 7.1), "C": (5.6, 6.3), "D": (4.8, 5.5), "E": (0, 4.7)},
            10: {"A": (9.0, 10.0), "B": (8.0, 8.9), "C": (7.0, 7.9), "D": (6.0, 6.9), "E": (0, 5.9)},
            12: {"A": (10.8, 12.0), "B": (9.6, 10.7), "C": (8.4, 9.5), "D": (7.2, 8.3), "E": (0, 7.1)}
        }

        # 加载语料库
        self.corpus = self._load_corpus()

    def _load_corpus(self):
        """加载语料库文件"""
        corpus = {}

        # 获取语料库文件路径
        base_dir = Path(__file__).parent.parent

        # 读取综合段位语料库
        rank_corpus_path = base_dir / "综合段位语料库.txt"
        if rank_corpus_path.exists():
            with open(rank_corpus_path, 'r', encoding='utf-8') as f:
                content = f.read()
                corpus['rank'] = self._parse_rank_corpus(content)

        # 读取能力维度语料库
        ability_corpus_path = base_dir / "能力维度、等级及分数解读语料库.txt"
        if ability_corpus_path.exists():
            with open(ability_corpus_path, 'r', encoding='utf-8') as f:
                content = f.read()
                corpus['ability'] = self._parse_ability_corpus(content)

        # 读取行动计划语料库（兼容历史命名）
        action_corpus_paths = [
            base_dir / "个性化发展行动计划语料库].txt",
            base_dir / "个性化发展行动计划语料库.txt",
        ]
        for action_corpus_path in action_corpus_paths:
            if action_corpus_path.exists():
                with open(action_corpus_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    corpus['action'] = self._parse_action_corpus(content)
                break

        return corpus

    def _parse_rank_corpus(self, content):
        """解析段位语料库"""
        ranks = {}
        lines = content.strip().split('\n')

        current_rank = None
        current_content = []

        for line in lines:
            line = line.strip()
            if line.startswith('您的当前段位：'):
                if current_rank:
                    ranks[current_rank] = '\n'.join(current_content)

                current_rank = line.split('：')[1]
                current_content = []
            elif current_rank:
                if line.startswith('段位释义：'):
                    current_content.append(line)
                else:
                    current_content.append(line)

        if current_rank:
            ranks[current_rank] = '\n'.join(current_content)

        return ranks

    def _parse_ability_corpus(self, content):
        """解析能力维度语料库（兼容空格/换行/冒号差异）"""
        abilities = {}
        lines = content.strip().split('\n')

        current_ability = None
        current_grades = {}
        current_grade = None
        ability_names = '|'.join(map(re.escape, self.abilities.keys()))
        ability_line_pattern = re.compile(
            rf'^({ability_names})/A\s*[^（(]*[（(][^）)]*[）)]\s*[:：]?\s*(.*)$'
        )
        grade_line_pattern = re.compile(
            r'^([A-E])\s*[^（(]*[（(][^）)]*[）)]\s*[:：]?\s*(.*)$'
        )

        for line in lines:
            line = line.strip()
            # 跳过空行和标题行
            if (
                not line
                or line.startswith('1、')
                or line.startswith('2、')
                or line.startswith('3、')
                or line == '能力维度/等级及分数解读'
                or line.startswith('这是您职业大厦的根基')
                or line.startswith('这决定了您能否从支持者转变为价值创造者')
                or line.startswith('这预示着您未来能否进入核心管理层')
            ):
                continue

            ability_match = ability_line_pattern.match(line)
            if ability_match:
                if current_ability and current_grades:
                    abilities[current_ability] = current_grades

                current_ability = ability_match.group(1)
                current_grades = {}
                current_grade = 'A'
                description = ability_match.group(2).strip().lstrip(':：').strip()
                current_grades['A'] = {
                    'score_range': '',
                    'description': description
                }
                continue

            if not current_ability:
                continue

            grade_match = grade_line_pattern.match(line)
            if grade_match:
                current_grade = grade_match.group(1)
                description = grade_match.group(2).strip().lstrip(':：').strip()
                current_grades[current_grade] = {
                    'score_range': '',
                    'description': description
                }
                continue

            # 兼容某些等级描述换行写法（如 B 级标题在上一行）
            if current_grade:
                previous = current_grades.get(current_grade, {'score_range': '', 'description': ''})
                if previous['description']:
                    previous['description'] += ' ' + line
                else:
                    previous['description'] = line
                current_grades[current_grade] = previous

        # 保存最后一个能力
        if current_ability and current_grades:
            abilities[current_ability] = current_grades

        return abilities

    def _parse_action_corpus(self, content):
        """解析行动计划语料库（区分优势升华区和重点改善区）"""
        actions = {}
        lines = content.strip().split('\n')
        meta = {
            'development_logic': '',
            'note': ''
        }

        section = None
        current_ability = None
        last_segment = None
        ability_set = set(self.abilities.keys())
        segment_pattern = re.compile(r'^(1-3段|4-6段|1-6段|7-9段\+|7-9段)\s*[：:]\s*(.*)$')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line == '1、优势升华区':
                section = 'advantage'
                current_ability = None
                last_segment = None
                continue

            if line == '2、重点改善区':
                section = 'improvement'
                current_ability = None
                last_segment = None
                continue

            if line.startswith('基于您的测评结果'):
                continue
            if line.startswith('发展逻辑：'):
                meta['development_logic'] = line
                continue
            if line.startswith('注：'):
                meta['note'] = line
                continue

            if line in ability_set:
                current_ability = line
                last_segment = None
                if current_ability not in actions:
                    actions[current_ability] = {
                        'advantage': {},
                        'improvement': []
                    }
                continue

            if not current_ability:
                continue

            if section == 'advantage':
                segment_match = segment_pattern.match(line)
                if segment_match:
                    segment = segment_match.group(1)
                    advice = segment_match.group(2).strip()
                    if advice:
                        actions[current_ability]['advantage'].setdefault(segment, []).append(advice)
                        last_segment = segment
                    continue

                if last_segment and actions[current_ability]['advantage'].get(last_segment):
                    actions[current_ability]['advantage'][last_segment][-1] += ' ' + line
                continue

            if section == 'improvement':
                if line == '行动步骤：':
                    continue
                actions[current_ability]['improvement'].append(line)

        if meta['development_logic'] or meta['note']:
            actions['__meta__'] = meta

        return actions

    def _get_action_advice(self, action_data, rank, ability_name, grade, advantage=True):
        """获取行动建议（严格按语料可用段位降级匹配）"""
        if not isinstance(action_data, dict):
            return []

        if not advantage:
            return action_data.get('improvement', [])

        rank_numbers = {"一段": 1, "二段": 2, "三段": 3, "四段": 4, "五段": 5,
                        "六段": 6, "七段": 7, "八段": 8, "九段": 9}
        rank_num = rank_numbers.get(rank, 1)
        segment_data = action_data.get('advantage', {})

        if not segment_data:
            return []

        # 特殊能力在低段位但A级时，强制使用高阶建议
        special_abilities = {"财务力", "领导力", "决策力"}
        if rank_num <= 6 and ability_name in special_abilities and grade == 'A':
            candidates = ['7-9段+', '7-9段', '4-6段', '1-6段', '1-3段']
        elif rank_num <= 3:
            candidates = ['1-3段', '1-6段', '4-6段', '7-9段', '7-9段+']
        elif rank_num <= 6:
            candidates = ['4-6段', '1-6段', '7-9段', '7-9段+', '1-3段']
        else:
            # 七段及以上：A级优先 7-9段+，否则优先 7-9段
            if grade == 'A':
                candidates = ['7-9段+', '7-9段', '4-6段', '1-6段', '1-3段']
            else:
                candidates = ['7-9段', '7-9段+', '4-6段', '1-6段', '1-3段']

        for segment in candidates:
            advices = segment_data.get(segment, [])
            if advices:
                return advices

        return []

    def calculate_grade(self, ability_name, score):
        """计算能力等级"""
        max_score = self.abilities[ability_name]['max_score']
        thresholds = self.grade_thresholds[max_score]

        for grade, (min_score, max_grade_score) in thresholds.items():
            if min_score <= score <= max_grade_score:
                return grade
        return 'E'

    def get_rank(self, total_score):
        """根据总分获取段位"""
        for rank, (min_score, max_score) in self.rank_ranges.items():
            if min_score <= total_score <= max_score:
                return rank
        return "一段"

    def generate_report(self, excel_file, output_dir=".", output_format="pdf"):
        """生成测评报告（批量处理Excel中的所有数据）

        Args:
            excel_file: Excel测评数据文件路径
            output_dir: 输出目录
            output_format: 输出格式，'pdf' 或 'txt'（默认为pdf）
        """
        print(f"正在读取Excel文件: {excel_file}")

        # 读取Excel数据
        df = pd.read_excel(excel_file)

        if len(df) == 0:
            print("错误：Excel文件为空")
            return None

        print(f"发现 {len(df)} 条测评数据，开始批量生成报告...\n")

        generated_files = []

        # 处理每一行数据
        for idx, row in df.iterrows():
            print(f"[{idx+1}/{len(df)}] 正在处理第 {idx+1} 条数据...")

            # 提取基本信息
            user_info = {
                'seq_no': str(row.get('序号', '')),
                'nickname': str(row.get('微信昵称', '')),
                'phone': str(row.get('【职业信息】输入手机号以便我们给您发送测评报告', '')),
                'test_time': str(row.get('测评时间：', ''))
            }

            # 提取能力得分
            ability_scores = {}
            for ability in self.abilities.keys():
                score = row.get(f'【{ability}】', 0)
                ability_scores[ability] = float(score) if pd.notna(score) else 0.0

            # 计算总分
            total_score = sum(ability_scores.values())

            # 获取段位
            rank = self.get_rank(total_score)

            # 计算各能力等级
            ability_grades = {}
            for ability, score in ability_scores.items():
                ability_grades[ability] = self.calculate_grade(ability, score)

            # 获取段位释义
            rank_text = ""
            if 'rank' in self.corpus and rank in self.corpus['rank']:
                rank_text = self.corpus['rank'][rank]

            # 生成报告
            if output_format.lower() == 'pdf':
                # 使用PDF生成器
                output_file = Path(output_dir) / f"九段总助测评结果报告-NLZ100{user_info['seq_no']}-{user_info['nickname']}-{rank}.pdf"
                print(f"  正在生成PDF报告...")

                try:
                    pdf_gen = PDFReportGenerator(str(output_file))

                    # V4 版本直接调用 build 方法，传入所有必要数据
                    pdf_gen.build(
                        user_info=user_info,
                        total_score=total_score,
                        rank=rank,
                        ability_scores=ability_scores,
                        ability_grades=ability_grades,
                        rank_text=rank_text,
                        corpus=self.corpus,
                        advice_func=self._get_action_advice  # 传入建议获取函数
                    )

                    print(f"  ✅ PDF报告已生成: {output_file.name}")
                    print(f"     段位: {rank}, 总分: {total_score:.2f}")
                except Exception as e:
                    print(f"  ❌ 生成失败: {e}")
                    continue

            else:
                # 使用文本生成器（兼容旧版本）
                output_file = Path(output_dir) / f"九段总助测评结果报告-NLZ100{user_info['seq_no']}-{user_info['nickname']}-{rank}.txt"
                report_content = self._generate_report_content(
                    user_info, total_score, rank, ability_scores, ability_grades
                )

                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report_content)

                print(f"  ✅ 文本报告已生成: {output_file.name}")
                print(f"     段位: {rank}, 总分: {total_score:.2f}")

            generated_files.append(str(output_file))
            print()

        print("=" * 60)
        print(f"✨ 批处理完成！共生成 {len(generated_files)} 份报告")
        print("=" * 60)

        return generated_files

    def _generate_report_content(self, user_info, total_score, rank, ability_scores, ability_grades):
        """生成报告文本内容"""
        lines = []

        # 标题
        lines.append("=" * 80)
        lines.append("九段总助胜任力专业测评报告".center(80))
        lines.append("=" * 80)
        lines.append("")

        # 基本信息
        lines.append("【基本信息】")
        lines.append(f"序号: NLZ100{user_info['seq_no']}")
        lines.append(f"微信昵称: {user_info['nickname']}")
        lines.append(f"测评时间: {user_info['test_time']}")
        lines.append("")

        # 第一部分：核心发现与总览
        lines.append("=" * 80)
        lines.append("第一部分：核心发现与总览".center(80))
        lines.append("=" * 80)
        lines.append("")

        # 综合段位
        lines.append(f"【当前段位】{rank}".center(80))
        lines.append("")
        lines.append(f"【测评得分】{total_score:.2f}分")
        lines.append("")

        if 'rank' in self.corpus and rank in self.corpus['rank']:
            lines.append("【段位释义】")
            lines.append(self.corpus['rank'][rank])
            lines.append("")

        # 核心能力雷达图数据
        lines.append("【核心能力雷达图】")
        lines.append("一眼看清您的能力结构。面积越大、越均衡，说明能力结构越全面；")
        lines.append("突出的尖角是您的核心优势，凹陷的角落是您的待发展区。")
        lines.append("")
        for ability, score in ability_scores.items():
            grade = ability_grades[ability]
            lines.append(f"  {ability}: {score:.2f}分 ({grade}级)")
        lines.append("")

        # 第二部分：能力维度深度解析
        lines.append("=" * 80)
        lines.append("第二部分：能力维度深度解析".center(80))
        lines.append("=" * 80)
        lines.append("")

        # 核心基石
        lines.append("【核心基石】")
        lines.append("这是您职业大厦的根基，决定了您工作的稳定性和可靠性。")
        lines.append("")
        for ability in ["执行力", "协调力", "优化力"]:
            score = ability_scores[ability]
            grade = ability_grades[ability]
            lines.append(f"{ability} ({grade}级) - {score:.2f}分")
            if 'ability' in self.corpus and ability in self.corpus['ability']:
                if grade in self.corpus['ability'][ability]:
                    lines.append(self.corpus['ability'][ability][grade]['description'])
            lines.append("")

        # 价值引擎
        lines.append("【价值引擎】")
        lines.append("这决定了您能否从支持者转变为价值创造者。")
        lines.append("")
        for ability in ["统筹力", "预见力", "业务力"]:
            score = ability_scores[ability]
            grade = ability_grades[ability]
            lines.append(f"{ability} ({grade}级) - {score:.2f}分")
            if 'ability' in self.corpus and ability in self.corpus['ability']:
                if grade in self.corpus['ability'][ability]:
                    lines.append(self.corpus['ability'][ability][grade]['description'])
            lines.append("")

        # 领导潜能
        lines.append("【领导潜能】")
        lines.append("这预示着您未来能否进入核心管理层，承担更大责任。")
        lines.append("")
        for ability in ["财务力", "领导力", "决策力"]:
            score = ability_scores[ability]
            grade = ability_grades[ability]
            lines.append(f"{ability} ({grade}级) - {score:.2f}分")
            if 'ability' in self.corpus and ability in self.corpus['ability']:
                if grade in self.corpus['ability'][ability]:
                    lines.append(self.corpus['ability'][ability][grade]['description'])
            lines.append("")

        # 第三部分：个性化发展行动计划
        lines.append("=" * 80)
        lines.append("第三部分：个性化发展行动计划".center(80))
        lines.append("=" * 80)
        lines.append("")

        # 优势升华区
        lines.append("【1、优势升华区】")
        advantages = [ability for ability, grade in ability_grades.items() if grade in ['A', 'B']]
        if advantages:
            for ability in advantages:
                lines.append(f"{ability}:")
                # 根据段位选择建议
                # 这里简化处理，实际应根据段位和分数选择对应建议
                lines.append("  继续保持和提升您的优势，将个人能力转化为团队影响力。")
                lines.append("")
        else:
            lines.append("暂无明显优势")
            lines.append("")

        # 重点改善区
        lines.append("【2、重点改善区】")
        improvements = [ability for ability, grade in ability_grades.items() if grade in ['D', 'E']]
        if improvements:
            for ability in improvements:
                lines.append(f"{ability}:")
                lines.append("  系统化补课，将能力短板提升至及格线以上，消除职业发展的'致命伤'。")
                lines.append("")
        else:
            lines.append("无急需改善项")
            lines.append("")

        # 核心诊断
        lines.append("【3、核心诊断与发展建议】")
        lines.append("请把个人情况、当前困惑或期待发给老师进行详细诊断。")
        lines.append("")

        # 页脚
        lines.append("=" * 80)
        lines.append(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)

        return '\n'.join(lines)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='生成九段总助胜任力测评报告')
    parser.add_argument('excel_file', help='Excel测评数据文件路径')
    parser.add_argument('-o', '--output', default='.', help='输出目录（默认为当前目录）')

    args = parser.parse_args()

    # 创建生成器
    generator = AssessmentReportGenerator()

    # 生成报告
    output_file = generator.generate_report(args.excel_file, args.output)

    if output_file:
        print(f"\n✨ 报告生成完成！")
        print(f"📄 文件路径: {output_file}")
        return 0
    else:
        print(f"\n❌ 报告生成失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
