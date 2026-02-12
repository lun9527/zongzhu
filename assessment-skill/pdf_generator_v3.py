#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF报告生成器 - 精美样式版本
"""

import os
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


class PDFReportGeneratorV3:
    """PDF报告生成器V3 - 精美样式"""

    def __init__(self, output_path):
        """初始化PDF生成器"""
        self.output_path = output_path

        # 注册中文字体
        self._register_chinese_fonts()

        # 创建文档
        self.doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        # 设置样式
        self.styles = getSampleStyleSheet()
        self._setup_styles()

        # 存储PDF元素
        self.story = []

    def _register_chinese_fonts(self):
        """注册中文字体 - 优化版本"""
        # 尝试多个字体路径和subfontIndex
        font_configs = [
            # PingFang SC (推荐)
            ('/System/Library/Fonts/PingFang.ttc', 1, 0),  # (Regular, Bold)
            # STHeiti
            ('/System/Library/Fonts/STHeiti Medium.ttc', 0, 0),
            # Hiragino Sans GB
            ('/System/Library/Fonts/Hiragino Sans GB.ttc', 0, 0),
            # Heiti SC
            ('/System/Library/Fonts/STHeiti Light.ttc', 0, 0),
        ]

        for regular_path, sub_idx, bold_idx in font_configs:
            try:
                # 注册常规字体
                pdfmetrics.registerFont(TTFont('CN', regular_path, subfontIndex=sub_idx))
                # 注册粗体（使用相同路径，不同subfontIndex）
                pdfmetrics.registerFont(TTFont('CN-Bold', regular_path, subfontIndex=sub_idx+1 if sub_idx < 2 else sub_idx))

                self.font = 'CN'
                self.font_bold = 'CN-Bold'
                print(f"✅ 成功注册中文字体: {regular_path} (subfontIndex={sub_idx})")
                return
            except Exception as e:
                print(f"⚠️  尝试字体失败 {regular_path}: {e}")
                continue

        # 如果所有尝试都失败，使用默认
        print("❌ 所有中文字体注册失败，使用Helvetica")
        self.font = 'Helvetica'
        self.font_bold = 'Helvetica-Bold'

    def _setup_styles(self):
        """设置自定义样式"""
        # 主标题
        if 'TitleMain' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='TitleMain',
                fontName=self.font_bold,
                fontSize=26,
                alignment=TA_CENTER,
                spaceAfter=25,
                textColor=HexColor('#2C3E50'),
                leading=34
            ))

        # 章节编号
        if 'SectionNum' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SectionNum',
                fontName=self.font_bold,
                fontSize=11,
                textColor=HexColor('#3498DB'),
                spaceAfter=2,
                leading=14
            ))

        # 章节标题
        if 'SectionTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SectionTitle',
                fontName=self.font_bold,
                fontSize=18,
                textColor=HexColor('#2C3E50'),
                spaceAfter=15,
                leading=24
            ))

        # 小节标题
        if 'SubSectionTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SubSectionTitle',
                fontName=self.font_bold,
                fontSize=14,
                textColor=HexColor('#34495E'),
                spaceBefore=10,
                spaceAfter=8,
                leading=18
            ))

        # 能力标题
        if 'AbilityTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='AbilityTitle',
                fontName=self.font_bold,
                fontSize=12,
                textColor=HexColor('#2C3E50'),
                spaceBefore=8,
                spaceAfter=6,
                leading=16
            ))

        # 正文 - 关键修复：使用中文字体
        if 'BodyText' in self.styles:
            # 修改已存在的BodyText样式
            self.styles['BodyText'].fontName = self.font
        else:
            self.styles.add(ParagraphStyle(
                name='BodyText',
                fontName=self.font,
                fontSize=10,
                spaceAfter=6,
                leading=14,
                textColor=HexColor('#2C3E50'),
                alignment=TA_JUSTIFY
            ))

        # 说明文字 - 使用中文字体
        if 'NoteText' in self.styles:
            # 修改已存在的NoteText样式
            self.styles['NoteText'].fontName = self.font
        else:
            self.styles.add(ParagraphStyle(
                name='NoteText',
                fontName=self.font,
                fontSize=9,
                spaceAfter=6,
                leading=12,
                textColor=HexColor('#7F8C8D'),
                alignment=TA_JUSTIFY
            ))

    def generate_radar_chart(self, ability_scores, ability_grades):
        """生成能力雷达图 - 使用PIL绘制中文标签"""
        from PIL import Image, ImageDraw, ImageFont
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np

        abilities = list(ability_scores.keys())

        max_scores = {
            "执行力": 8, "协调力": 8, "优化力": 8,
            "统筹力": 10, "预见力": 10, "业务力": 10,
            "财务力": 12, "领导力": 12, "决策力": 12
        }

        normalized_scores = [ability_scores[ability] / max_scores[ability] * 100 for ability in abilities]

        angles = np.linspace(0, 2 * np.pi, len(abilities), endpoint=False).tolist()
        normalized_scores += normalized_scores[:1]
        angles += angles[:1]

        # 创建更大的图形以便添加中文标签
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'), dpi=150)

        # 蓝色主题
        ax.plot(angles, normalized_scores, 'o-', linewidth=2.5, color='#3498DB', markersize=6)
        ax.fill(angles, normalized_scores, alpha=0.25, color='#3498DB')

        # 先用数字标签
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([str(i+1) for i in range(len(abilities))], fontsize=11, fontweight='bold', color='#2C3E50')
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'], fontsize=9, color='#7F8C8D')
        ax.grid(True, linestyle='--', alpha=0.7, color='#BDC3C7', linewidth=1)
        ax.spines['polar'].set_visible(False)
        ax.set_facecolor('#FFFFFF')

        # 保存matplotlib图像到临时buffer
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
        buf.seek(0)
        plt.close()

        # 用PIL打开图像并添加中文标签
        img = Image.open(buf)
        draw = ImageDraw.Draw(img)

        # 尝试加载中文字体
        font_paths = [
            '/System/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/STHeiti Medium.ttc',
            '/System/Library/Fonts/Hiragino Sans GB.ttc',
        ]

        font = None
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, 20)
                break
            except:
                continue

        if font is None:
            font = ImageFont.load_default()

        # 计算标签位置（基于极坐标）
        width, height = img.size
        center_x, center_y = width // 2, height // 2
        radius = min(width, height) // 2 - 60

        # 添加中文标签
        for i, (angle, ability) in enumerate(zip(angles[:-1], abilities)):
            import math
            # 将角度转换为弧度
            angle_rad = angle
            # 计算标签位置（稍微向外偏移）
            label_radius = radius * 1.18
            label_x = center_x + label_radius * math.cos(angle_rad) - len(ability) * 6
            label_y = center_y + label_radius * math.sin(angle_rad) - 10

            # 绘制文字
            draw.text((label_x, label_y), ability, fill='#2C3E50', font=font)

        # 保存最终图像
        final_buf = BytesIO()
        img.save(final_buf, format='PNG', dpi=(200, 200))
        final_buf.seek(0)

        return final_buf

    def add_cover_page(self, user_info, total_score, rank):
        """添加封面页 - 优化布局"""
        # 主标题
        self.story.append(Paragraph("九段总助胜任力专业测评报告", self.styles['TitleMain']))
        self.story.append(Spacer(1, 1.5*cm))

        # 段位显示框 - 更精致的样式
        rank_table = Table([[f"  {rank}  "]], colWidths=[13*cm], rowHeights=[2.5*cm])
        rank_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#FFF8E1')),
            ('GRID', (0, 0), (-1, 0), 3, HexColor('#FFB74D')),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), self.font_bold),
            ('FONTSIZE', (0, 0), (-1, 0), 48),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#E65100')),
        ]))
        self.story.append(rank_table)
        self.story.append(Spacer(1, 1.2*cm))

        # 信息表格 - 更简洁的设计
        data = [
            ['序号', f"NLZ100{user_info['seq_no']}", '测评得分', f"{total_score:.2f}分"],
            ['微信昵称', user_info['nickname'], '测评时间', user_info['test_time']],
        ]

        table = Table(data, colWidths=[3.2*cm, 5.8*cm, 3.2*cm, 5.8*cm], rowHeights=[0.9*cm, 0.9*cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.font),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#E0E0E0')),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, HexColor('#FAFAFA')]),
            ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#616161')),  # 标签列
            ('TEXTCOLOR', (2, 0), (2, -1), HexColor('#616161')),  # 标签列
            ('TEXTCOLOR', (1, 0), (1, -1), HexColor('#212121')),  # 值列
            ('TEXTCOLOR', (3, 0), (3, -1), HexColor('#212121')),  # 值列
        ]))
        self.story.append(table)
        self.story.append(Spacer(1, 2.5*cm))

    def add_section_one(self, rank_text, ability_scores, ability_grades):
        """添加第一部分：核心发现与总览 - 优化布局"""
        self.story.append(PageBreak())

        # 章节标题
        self.story.append(Paragraph("第一部分", self.styles['SectionNum']))
        self.story.append(Paragraph("核心发现与总览", self.styles['SectionTitle']))
        self.story.append(Spacer(1, 0.6*cm))

        # 段位释义
        lines = rank_text.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                if '段位释义：' in line:
                    self.story.append(Paragraph("段位释义", self.styles['SubSectionTitle']))
                    self.story.append(Spacer(1, 0.2*cm))
                else:
                    self.story.append(Paragraph(line, self.styles['BodyText']))

        self.story.append(Spacer(1, 1*cm))

        # 雷达图
        self.story.append(Paragraph("核心能力雷达图", self.styles['SubSectionTitle']))
        self.story.append(Spacer(1, 0.3*cm))
        chart_buf = self.generate_radar_chart(ability_scores, ability_grades)
        img = Image(chart_buf, width=14*cm, height=14*cm)
        img.hAlign = 'CENTER'
        self.story.append(img)
        self.story.append(Spacer(1, 0.5*cm))

        # 解读说明
        interpretation = "一眼看清您的能力结构。面积越大、越均衡，说明能力结构越全面；突出的尖角是您的核心优势，凹陷的角落是您的待发展区。"
        self.story.append(Paragraph(interpretation, self.styles['NoteText']))
        self.story.append(Spacer(1, 1*cm))

        # 能力得分明细表格
        self.story.append(Paragraph("能力得分明细", self.styles['SubSectionTitle']))
        self.story.append(Spacer(1, 0.3*cm))

        data = [['能力维度', '得分', '等级']]
        for ability, score in ability_scores.items():
            grade = ability_grades[ability]
            grade_color = self._get_grade_color(grade)
            data.append([ability, f"{score:.2f}", grade])

        table = Table(data, colWidths=[6.5*cm, 3*cm, 2.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1976D2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), self.font_bold),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#E0E0E0')),
            ('FONTNAME', (0, 1), (-1, -1), self.font),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#F5F5F5')]),
            ('TEXTCOLOR', (0, 1), (0, -1), HexColor('#424242')),
            ('TEXTCOLOR', (1, 1), (1, -1), HexColor('#212121')),
        ]))

        # 为等级列添加颜色
        for i, grade in enumerate(ability_grades.values(), start=1):
            grade_color = self._get_grade_color(grade)
            table.setStyle(TableStyle([
                ('TEXTCOLOR', (2, i), (2, i), grade_color),
                ('FONTNAME', (2, i), (2, i), self.font_bold),
                ('FONTSIZE', (2, i), (2, i), 11),
            ]))

        self.story.append(table)

    def _get_grade_color(self, grade):
        """获取等级对应的颜色"""
        colors_map = {
            'A': HexColor('#27AE60'),
            'B': HexColor('#2ECC71'),
            'C': HexColor('#F39C12'),
            'D': HexColor('#E67E22'),
            'E': HexColor('#E74C3C')
        }
        return colors_map.get(grade, HexColor('#7F8C8D'))

    def add_section_two(self, ability_scores, ability_grades, corpus):
        """添加第二部分：能力维度深度解析 - 优化布局"""
        self.story.append(PageBreak())

        # 章节标题
        self.story.append(Paragraph("第二部分", self.styles['SectionNum']))
        self.story.append(Paragraph("能力维度深度解析", self.styles['SectionTitle']))
        self.story.append(Spacer(1, 0.6*cm))

        # 核心基石
        self.story.append(Paragraph("核心基石", self.styles['SubSectionTitle']))
        self.story.append(Paragraph("这是您职业大厦的根基，决定了您工作的稳定性和可靠性。", self.styles['NoteText']))
        self.story.append(Spacer(1, 0.4*cm))

        for ability in ["执行力", "协调力", "优化力"]:
            self._add_ability_item(ability, ability_scores, ability_grades, corpus)

        # 价值引擎
        self.story.append(Spacer(1, 0.8*cm))
        self.story.append(Paragraph("价值引擎", self.styles['SubSectionTitle']))
        self.story.append(Paragraph("这决定了您能否从支持者转变为价值创造者。", self.styles['NoteText']))
        self.story.append(Spacer(1, 0.4*cm))

        for ability in ["统筹力", "预见力", "业务力"]:
            self._add_ability_item(ability, ability_scores, ability_grades, corpus)

        # 领导潜能
        self.story.append(Spacer(1, 0.8*cm))
        self.story.append(Paragraph("领导潜能", self.styles['SubSectionTitle']))
        self.story.append(Paragraph("这预示着您未来能否进入核心管理层，承担更大责任。", self.styles['NoteText']))
        self.story.append(Spacer(1, 0.4*cm))

        for ability in ["财务力", "领导力", "决策力"]:
            self._add_ability_item(ability, ability_scores, ability_grades, corpus)

    def _add_ability_item(self, ability, ability_scores, ability_grades, corpus):
        """添加单个能力项 - 优化布局"""
        score = ability_scores[ability]
        grade = ability_grades[ability]
        grade_color = self._get_grade_color(grade)

        # 能力标题
        title = f"{ability} ({grade}级) - {score:.2f}分"
        self.story.append(Paragraph(title, self.styles['AbilityTitle']))
        self.story.append(Spacer(1, 0.2*cm))

        # 从语料库获取描述
        if 'ability' in corpus and ability in corpus['ability']:
            if grade in corpus['ability'][ability]:
                desc = corpus['ability'][ability][grade].get('description', '')
                self.story.append(Paragraph(desc, self.styles['BodyText']))

        self.story.append(Spacer(1, 0.5*cm))

    def add_section_three(self, ability_grades, rank, corpus):
        """添加第三部分：个性化发展行动计划 - 简化优化版本"""
        self.story.append(PageBreak())

        # 章节标题
        self.story.append(Paragraph("第三部分", self.styles['SectionNum']))
        self.story.append(Paragraph("个性化发展行动计划", self.styles['SectionTitle']))
        self.story.append(Spacer(1, 0.8*cm))

        # 优势升华区
        self.story.append(Paragraph("1. 优势升华区", self.styles['SubSectionTitle']))
        self.story.append(Spacer(1, 0.4*cm))

        advantages = [ability for ability, grade in ability_grades.items() if grade in ['A', 'B']]

        if advantages:
            for ability in advantages:
                grade = ability_grades[ability]
                grade_color = self._get_grade_color(grade)

                # 能力标题行 - 简化样式
                title = f"<b>{ability}</b> - {grade}级"
                self.story.append(Paragraph(title, self.styles['AbilityTitle']))

                # 从语料库提取建议
                advice_found = False
                if 'action' in corpus and ability in corpus['action']:
                    action_data = corpus['action'][ability]
                    # 获取建议
                    advice_list = self._get_action_advice(action_data, rank, ability, grade, advantage=True)
                    if advice_list and len(advice_list) > 0:
                        advice_found = True
                        # 处理建议（可能是列表）
                        for advice in advice_list:
                            if advice:
                                self.story.append(Paragraph(f"• {advice}", self.styles['BodyText']))
                        self.story.append(Spacer(1, 0.4*cm))

                # 如果没找到建议，使用默认文本
                if not advice_found:
                    self.story.append(Paragraph("继续保持您的优势，将个人能力转化为团队影响力。", self.styles['BodyText']))
                    self.story.append(Spacer(1, 0.4*cm))
        else:
            self.story.append(Paragraph("暂无明显优势", self.styles['NoteText']))

        self.story.append(Spacer(1, 0.8*cm))

        # 重点改善区
        self.story.append(Paragraph("2. 重点改善区", self.styles['SubSectionTitle']))
        self.story.append(Spacer(1, 0.4*cm))

        improvements = [ability for ability, grade in ability_grades.items() if grade in ['D', 'E']]

        if improvements:
            for ability in improvements:
                grade = ability_grades[ability]
                grade_color = self._get_grade_color(grade)

                # 能力标题行 - 简化样式
                title = f"<b>{ability}</b> - {grade}级"
                self.story.append(Paragraph(title, self.styles['AbilityTitle']))

                # 从语料库提取建议
                advice_found = False
                if 'action' in corpus and ability in corpus['action']:
                    action_data = corpus['action'][ability]
                    # 获取建议
                    advice_list = self._get_action_advice(action_data, rank, ability, grade, advantage=False)
                    if advice_list and len(advice_list) > 0:
                        advice_found = True
                        # 处理建议
                        for advice in advice_list:
                            if advice:
                                self.story.append(Paragraph(f"• {advice}", self.styles['BodyText']))
                        self.story.append(Spacer(1, 0.4*cm))

                # 如果没找到建议，使用默认文本
                if not advice_found:
                    self.story.append(Paragraph("系统化补课，将能力短板提升至及格线以上，消除职业发展的'致命伤'。", self.styles['BodyText']))
                    self.story.append(Spacer(1, 0.4*cm))
        else:
            self.story.append(Paragraph("无急需改善项", self.styles['NoteText']))

        self.story.append(Spacer(1, 0.8*cm))

        # 核心诊断
        self.story.append(Paragraph("3. 核心诊断与发展建议", self.styles['SubSectionTitle']))
        self.story.append(Spacer(1, 0.3*cm))
        self.story.append(Paragraph("请把个人情况、当前困惑或期待发给老师进行详细诊断。", self.styles['BodyText']))
        self.story.append(Spacer(1, 2*cm))

        # 页脚
        footer = f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        self.story.append(Paragraph(footer, self.styles['NoteText']))

    def _get_action_advice(self, action_data, rank, ability_name, grade, advantage=True):
        """获取行动建议 - 包含特殊逻辑修复"""
        rank_numbers = {"一段": 1, "二段": 2, "三段": 3, "四段": 4, "五段": 5,
                        "六段": 6, "七段": 7, "八段": 8, "九段": 9}
        rank_num = rank_numbers.get(rank, 1)

        # 特殊逻辑：若综合段位为一~六段，但财务力、领导力、决策力分值达到A级能力
        # 则这三项选“7-9段+”；若综合段位为六段且这些能力达到A级，按原逻辑也应选高阶
        special_abilities = ["财务力", "领导力", "决策力"]
        is_special_case = (rank_num <= 6) and (ability_name in special_abilities) and (grade == 'A')

        if is_special_case:
            # 强制使用最高阶建议
            segments_to_check = ['7-9段+', '7-9段']
        else:
            # 常规逻辑
            if rank_num <= 3:
                segments_to_check = ['1-3段', '4-6段', '7-9段']
            elif rank_num <= 6:
                segments_to_check = ['4-6段', '7-9段', '1-3段']
            else:
                segments_to_check = ['7-9段+', '7-9段', '4-6段']

        advice_list = []
        for segment in segments_to_check:
            if segment in action_data and action_data[segment]:
                advice_list = action_data[segment]
                if advice_list:  # 确保不是空列表
                    break
        
        return advice_list

    def build(self):
        """构建PDF文档"""
        self.doc.build(self.story)
        return self.output_path
