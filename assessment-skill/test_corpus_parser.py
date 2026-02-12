#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试语料库解析
"""
import re

def parse_ability_corpus_test(content):
    """解析能力维度语料库 - 修复版本"""
    abilities = {}
    lines = content.strip().split('\n')

    current_ability = None
    current_grades = {}

    for line in lines:
        line = line.strip()
        # 跳过空行和分组标题
        if not line or line.startswith('1、') or line.startswith('2、') or line.startswith('3、'):
            continue

        # 检测新能力开始（如：执行力/A 卓越）
        is_new_ability = False
        for ability in ['执行力', '协调力', '优化力', '统筹力', '预见力', '业务力', '财务力', '领导力', '决策力']:
            if line.startswith(f'{ability}/'):
                # 保存前一个能力
                if current_ability and current_grades:
                    abilities[current_ability] = current_grades

                # 开始新能力
                current_ability = ability
                current_grades = {}

                # 使用正则表达式提取
                # 格式：执行力/A 卓越（7.2 - 8.0分）描述...
                pattern = r'{ability}/A\s*\u5353\u8d8a\uff08\u5206\u6570\u8303\u56f4\uff09.*?\uff09(.*)'
                # 简化：直接用字符串操作
                if '（' in line and '）' in line:
                    # 找到第一个）的位置
                    idx = line.find('）')
                    if idx > 0:
                        description = line[idx+1:].strip()
                        current_grades['A'] = {
                            'score_range': '',
                            'description': description
                        }
                is_new_ability = True
                break

        # 如果不是新能力行，且已有当前能力，解析B/C/D/E等级
        if not is_new_ability and current_ability:
            for grade in ['A', 'B', 'C', 'D', 'E']:
                # 格式：B 优良（6.4 - 7.1分）描述...
                # 或：C 合格（5.6 - 6.3分）描述...
                if line.startswith(f'{grade} ') or line.startswith(f'{grade}\u6709'):
                    if '（' in line and '）' in line:
                        idx = line.find('）')
                        if idx > 0:
                            description = line[idx+1:].strip()
                            # 去掉可能的冒号
                            if description.startswith(':'):
                                description = description[1:].strip()
                            current_grades[grade] = {
                                'score_range': '',
                                'description': description
                            }
                    break

    # 保存最后一个能力
    if current_ability and current_grades:
        abilities[current_ability] = current_grades

    return abilities

# 读取并测试
with open('/Users/yanzhanglun/Desktop/测评报告/能力维度、等级及分数解读语料库.txt', 'r', encoding='utf-8') as f:
    content = f.read()

result = parse_ability_corpus_test(content)

print(f"成功解析 {len(result)} 个能力")
for ability, grades in result.items():
    print(f"\n{ability}: {len(grades)} 个等级")
    for grade, data in grades.items():
        desc_preview = data['description'][:40] + '...'
        print(f"  {grade}级: {desc_preview}")
