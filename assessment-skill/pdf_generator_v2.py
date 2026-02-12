#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF报告生成器 - 重新设计版本，更接近模板样式
"""

import os
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


class PDFReportGeneratorV2:
    """PDF报告生成器V2 - 更接近模板样式"""

    def __init__(self, output_path):
        """初始化PDF生成器"""
        self.output_path = output_path

        # 定义颜色（在_setup_styles之前）
        self.colors = {
            'primary': HexColor('#2C3E50'),
            'accent': HexColor('#E74C3C'),
            'success': HexColor('#27AE60'),
            'warning': HexColor('#F39C12'),
            'info': HexColor('#3498DB'),
            'light_gray': HexColor('#ECF0F1'),
            'medium_gray': HexColor('#95A5A6'),
            'rank_bg': HexColor('#FFF5E6'),
            'rank_border': HexColor('#F39C12'),
        }

        # 注册中文字体
        self._register_chinese_fonts()

        # 创建文档
        self.doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )

        # 设置样式
        self.styles = getSampleStyleSheet()
        self._setup_styles()

        # 存储PDF元素
        self.story = []

    def _register_chinese_fonts(self):
        """注册中文字体"""
        try:
            pdfmetrics.registerFont(TTFont('ChineseFont', '/System/Library/Fonts/PingFang.ttc', subfontIndex=1))
            self.chinese_font = 'ChineseFont'
            self.chinese_font_bold = 'ChineseFont'
        except:
            try:
                pdfmetrics.registerFont(TTFont('ChineseFont', '/System/Library/Fonts/STHeiti Medium.ttc'))
                self.chinese_font = 'ChineseFont'
                self.chinese_font_bold = 'ChineseFont'
            except:
                self.chinese_font = 'Helvetica'
                self.chinese_font_bold = 'Helvetica-Bold'

    def _setup_styles(self):
        """设置自定义样式"""
        # 主标题
        if 'MainTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='MainTitle',
                fontName=self.chinese_font_bold,
                fontSize=28,
                alignment=TA_CENTER,
                spaceAfter=30,
                textColor=self.colors['primary'],
                leading=36
            ))

        # 大号段位标题
        if 'RankTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='RankTitle',
                fontName=self.chinese_font_bold,
                fontSize=72,
                alignment=TA_CENTER,
                spaceAfter=20,
                textColor=self.colors['accent'],
                leading=80
            ))

        # 章节标题
        if 'ChapterTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='ChapterTitle',
                fontName=self.chinese_font_bold,
                fontSize=18,
                spaceAfter=15,
                spaceBefore=20,
                textColor=self.colors['primary'],
                leading=24
            ))

        # 小节标题
        if 'SectionTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SectionTitle',
                fontName=self.chinese_font_bold,
                fontSize=14,
                spaceAfter=10,
                spaceBefore=10,
                textColor=self.colors['primary'],
                leading=20
            ))

        # 正文
        if 'BodyTextCN' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='BodyTextCN',
                fontName=self.chinese_font,
                fontSize=10,
                spaceAfter=8,
                alignment=TA_JUSTIFY,
                textColor=self.colors['primary'],
                leading=16
            ))

        # 小字说明
        if 'SmallText' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SmallText',
                fontName=self.chinese_font,
                fontSize=9,
                spaceAfter=6,
                alignment=TA_JUSTIFY,
                textColor=HexColor('#7F8C8D'),
                leading=14
            ))

    def generate_radar_chart(self, ability_scores, ability_grades):
        """生成能力雷达图 - 匹配模板蓝色样式"""
        plt.rcParams['font.sans-serif'] = ['PingFang SC', 'STHeiti', 'Arial Unicode MS', 'SimHei']
        plt.rcParams['axes.unicode_minus'] = False

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

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))

        # 使用蓝色填充，匹配模板
        ax.plot(angles, normalized_scores, 'o-', linewidth=2, color='#3498DB', label='能力得分')
        ax.fill(angles, normalized_scores, alpha=0.25, color='#3498DB')

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(abilities, fontsize=10, fontweight='bold')
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'], fontsize=8)
        ax.grid(True, linestyle='--', alpha=0.5, color='#95A5A6')

        plt.title('核心能力雷达图', fontsize=14, fontweight='bold', pad=20,
                 color='#2C3E50', fontfamily='sans-serif')

        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
        buf.seek(0)
        plt.close()

        return buf

    def add_cover_page(self, user_info, total_score, rank):
        """添加封面页 - 匹配模板样式"""
        # 主标题
        self.story.append(Paragraph("九段总助胜任力专业测评报告", self.styles['MainTitle']))
        self.story.append(Spacer(1, 0.8*cm))

        # 段位显示 - 使用带背景色的表格模拟橙红色框
        rank_data = [[f"{rank}"]]

        rank_table = Table(rank_data, colWidths=[16*cm], rowHeights=[2.5*cm])
        rank_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#FFF5E6')),
            ('GRID', (0, 0), (-1, 0), 2, HexColor('#F39C12')),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), self.chinese_font_bold),
            ('FONTSIZE', (0, 0), (-1, 0), 36),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#E74C3C')),
        ]))

        self.story.append(rank_table)
        self.story.append(Spacer(1, 0.8*cm))

        # 信息表格
        data = [
            ['序号', f"NLZ100{user_info['seq_no']}", '测评得分', f"{total_score:.2f}分"],
            ['微信昵称', user_info['nickname'], '测评时间', user_info['test_time']],
        ]

        table = Table(data, colWidths=[3.5*cm, 5.5*cm, 3.5*cm, 5.5*cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.colors['primary']),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, self.colors['light_gray']),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, self.colors['light_gray']]),
            ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#7F8C8D')),  # 标签列灰色
            ('TEXTCOLOR', (2, 0), (2, -1), HexColor('#7F8C8D')),  # 标签列灰色
        ]))

        self.story.append(table)
        self.story.append(Spacer(1, 2*cm))

    def add_section_one(self, rank_text, ability_scores, ability_grades):
        """添加第一部分：核心发现与总览"""
        self.story.append(PageBreak())

        # 章节标题
        self.story.append(Paragraph("第一部分", self.styles['SectionTitle']))
        self.story.append(Paragraph("核心发现与总览", self.styles['ChapterTitle']))
        self.story.append(Spacer(1, 0.5*cm))

        # 段位释义
        lines = rank_text.split('\n')
        for line in lines:
            if line.strip() and not line.startswith('段位释义：'):
                self.story.append(Paragraph(line.strip(), self.styles['BodyTextCN']))
            elif '段位释义：' in line:
                self.story.append(Paragraph(line.strip(), self.styles['SectionTitle']))

        self.story.append(Spacer(1, 0.8*cm))

        # 雷达图
        self.story.append(Paragraph("核心能力雷达图", self.styles['SectionTitle']))
        chart_buf = self.generate_radar_chart(ability_scores, ability_grades)
        img = Image(chart_buf, width=14*cm, height=14*cm)
        img.hAlign = 'CENTER'
        self.story.append(img)
        self.story.append(Spacer(1, 0.5*cm))

        # 雷达图解读
        interpretation = "一眼看清您的能力结构。面积越大、越均衡，说明能力结构越全面；突出的尖角是您的核心优势，凹陷的角落是您的待发展区。"
        self.story.append(Paragraph(interpretation, self.styles['SmallText']))
        self.story.append(Spacer(1, 0.8*cm))

        # 能力得分明细
        self.story.append(Paragraph("能力得分明细", self.styles['SectionTitle']))

        for ability, score in ability_scores.items():
            grade = ability_grades[ability]

            # 能力名称和分数
            data = [
                [f"  {ability}", f"{score:.2f}分  ", f"{grade}级"],
            ]

            table = Table(data, colWidths=[10*cm, 3*cm, 2*cm])
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, 0), self.chinese_font_bold),
                ('FONTNAME', (1, 0), (-1, 0), self.chinese_font),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('TEXTCOLOR', (0, 0), (0, 0), self.colors['primary']),
                ('TEXTCOLOR', (1, 0), (1, 0), HexColor('#3498DB')),
                ('TEXTCOLOR', (2, 0), (2, 0), self._get_grade_color(grade)),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (2, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                ('BACKGROUND', (0, 0), (-1, 0), self.colors['light_gray']),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ]))

            self.story.append(table)
            self.story.append(Spacer(1, 0.2*cm))

        self.story.append(Spacer(1, 0.5*cm))

    def _get_grade_color(self, grade):
        """根据等级获取颜色"""
        grade_colors = {
            'A': HexColor('#27AE60'),  # 绿色
            'B': HexColor('#3498DB'),  # 蓝色
            'C': HexColor('#F39C12'),  # 橙色
            'D': HexColor('#E67E22'),  # 深橙色
            'E': HexColor('#E74C3C'),  # 红色
        }
        return grade_colors.get(grade, HexColor('#95A5A6'))

    def add_section_two(self, ability_scores, ability_grades, corpus):
        """添加第二部分：能力维度深度解析"""
        self.story.append(PageBreak())

        # 章节标题
        self.story.append(Paragraph("第二部分", self.styles['SectionTitle']))
        self.story.append(Paragraph("能力维度深度解析", self.styles['ChapterTitle']))
        self.story.append(Spacer(1, 0.5*cm))

        # 核心基石
        self.story.append(Paragraph("【核心基石】", self.styles['ChapterTitle']))
        self.story.append(Paragraph("这是您职业大厦的根基，决定了您工作的稳定性和可靠性。", self.styles['SmallText']))
        self.story.append(Spacer(1, 0.3*cm))

        for ability in ["执行力", "协调力", "优化力"]:
            self._add_ability_item(ability, ability_scores[ability], ability_grades[ability], corpus)

        # 价值引擎
        self.story.append(Spacer(1, 0.5*cm))
        self.story.append(Paragraph("【价值引擎】", self.styles['ChapterTitle']))
        self.story.append(Paragraph("这决定了您能否从支持者转变为价值创造者。", self.styles['SmallText']))
        self.story.append(Spacer(1, 0.3*cm))

        for ability in ["统筹力", "预见力", "业务力"]:
            self._add_ability_item(ability, ability_scores[ability], ability_grades[ability], corpus)

        # 领导潜能
        self.story.append(Spacer(1, 0.5*cm))
        self.story.append(Paragraph("【领导潜能】", self.styles['ChapterTitle']))
        self.story.append(Paragraph("这预示着您未来能否进入核心管理层，承担更大责任。", self.styles['SmallText']))
        self.story.append(Spacer(1, 0.3*cm))

        for ability in ["财务力", "领导力", "决策力"]:
            self._add_ability_item(ability, ability_scores[ability], ability_grades[ability], corpus)

    def _add_ability_item(self, ability, score, grade, corpus):
        """添加单个能力项目"""
        # 能力标题（带等级标识）
        grade_color = self._get_grade_color(grade)

        data = [
            [f"{ability}", f"{grade}级", f"{score:.2f}分"],
        ]

        table = Table(data, colWidths=[8*cm, 2*cm, 3*cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), self.chinese_font_bold),
            ('FONTSIZE', (0, 0), (0, 0), 13),
            ('FONTSIZE', (1, 0), (-1, 0), 12),
            ('TEXTCOLOR', (0, 0), (0, 0), self.colors['primary']),
            ('TEXTCOLOR', (1, 0), (1, 0), grade_color),
            ('TEXTCOLOR', (2, 0), (2, 0), HexColor('#7F8C8D')),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (2, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['light_gray']),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ]))

        self.story.append(table)

        # 能力描述
        if 'ability' in corpus and ability in corpus['ability']:
            if grade in corpus['ability'][ability]:
                desc = corpus['ability'][ability][grade].get('description', '')
                self.story.append(Paragraph(desc, self.styles['BodyTextCN']))

        self.story.append(Spacer(1, 0.5*cm))

    def add_section_three(self, ability_grades, rank, corpus):
        """添加第三部分：个性化发展行动计划"""
        self.story.append(PageBreak())

        # 章节标题
        self.story.append(Paragraph("第三部分", self.styles['SectionTitle']))
        self.story.append(Paragraph("个性化发展行动计划", self.styles['ChapterTitle']))
        self.story.append(Spacer(1, 0.5*cm))

        # 优势升华区
        self.story.append(Paragraph("1. 优势升华区", self.styles['SectionTitle']))
        advantages = [ability for ability, grade in ability_grades.items() if grade in ['A', 'B']]

        if advantages:
            for ability in advantages:
                grade = ability_grades[ability]
                grade_color = self._get_grade_color(grade)

                # 能力标题
                data = [[f"  {ability}  ", f"{grade}级  "]]
                table = Table(data, colWidths=[11*cm, 3*cm])
                table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), self.chinese_font_bold),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('TEXTCOLOR', (0, 0), (0, 0), self.colors['primary']),
                    ('TEXTCOLOR', (1, 0), (1, 0), grade_color),
                    ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                    ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                    ('BACKGROUND', (0, 0), (-1, 0), self.colors['light_gray']),
                    ('TOPPADDING', (0, 0), (-1, 0), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ]))
                self.story.append(table)

                # 从语料库提取建议
                if 'action' in corpus and ability in corpus['action']:
                    advice_list = self._get_action_advice(corpus['action'][ability], rank, advantage=True)
                    if advice_list:
                        for advice in advice_list:
                            self.story.append(Paragraph(f"• {advice}", self.styles['BodyTextCN']))
                        self.story.append(Spacer(1, 0.3*cm))
                    else:
                        # 如果语料库没有，使用默认提示
                        self.story.append(Paragraph(f"建议：继续保持{ability}的优势，将个人能力转化为团队影响力。", self.styles['BodyTextCN']))
                        self.story.append(Spacer(1, 0.3*cm))
                else:
                    self.story.append(Paragraph(f"建议：继续保持{ability}的优势，将个人能力转化为团队影响力。", self.styles['BodyTextCN']))
                    self.story.append(Spacer(1, 0.3*cm))
        else:
            self.story.append(Paragraph("暂无明显优势", self.styles['BodyTextCN']))

        self.story.append(Spacer(1, 0.8*cm))

        # 重点改善区
        self.story.append(Paragraph("2. 重点改善区", self.styles['SectionTitle']))
        improvements = [ability for ability, grade in ability_grades.items() if grade in ['D', 'E']]

        if improvements:
            for ability in improvements:
                grade = ability_grades[ability]
                grade_color = self._get_grade_color(grade)

                # 能力标题
                data = [[f"  {ability}  ", f"{grade}级  "]]
                table = Table(data, colWidths=[11*cm, 3*cm])
                table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), self.chinese_font_bold),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('TEXTCOLOR', (0, 0), (0, 0), self.colors['primary']),
                    ('TEXTCOLOR', (1, 0), (1, 0), grade_color),
                    ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                    ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                    ('BACKGROUND', (0, 0), (-1, 0), self.colors['light_gray']),
                    ('TOPPADDING', (0, 0), (-1, 0), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ]))
                self.story.append(table)

                # 从语料库提取建议
                if 'action' in corpus and ability in corpus['action']:
                    advice_list = self._get_action_advice(corpus['action'][ability], rank, advantage=False)
                    if advice_list:
                        for advice in advice_list:
                            self.story.append(Paragraph(f"• {advice}", self.styles['BodyTextCN']))
                        self.story.append(Spacer(1, 0.3*cm))
                    else:
                        # 如果语料库没有，使用默认提示
                        self.story.append(Paragraph(f"建议：系统化补课，将{ability}短板提升至及格线以上，消除职业发展的'致命伤'。", self.styles['BodyTextCN']))
                        self.story.append(Spacer(1, 0.3*cm))
                else:
                    self.story.append(Paragraph(f"建议：系统化补课，将{ability}短板提升至及格线以上，消除职业发展的'致命伤'。", self.styles['BodyTextCN']))
                    self.story.append(Spacer(1, 0.3*cm))
        else:
            self.story.append(Paragraph("无急需改善项", self.styles['BodyTextCN']))

        self.story.append(Spacer(1, 0.8*cm))

        # 核心诊断
        self.story.append(Paragraph("3. 核心诊断与发展建议", self.styles['SectionTitle']))
        self.story.append(Paragraph("请把个人情况、当前困惑或期待发给老师进行详细诊断。", self.styles['BodyTextCN']))
        self.story.append(Spacer(1, 2*cm))

        # 页脚
        footer = f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        self.story.append(Paragraph(footer, self.styles['SmallText']))

    def _get_action_advice(self, action_data, rank, advantage=True):
        """根据段位和优势/改善情况，从语料库提取对应建议

        Args:
            action_data: 该能力的行动建议数据
            rank: 当前段位
            advantage: True表示优势升华区，False表示重点改善区
        """
        advice_list = []

        # 段位到数字映射
        rank_numbers = {
            "一段": 1, "二段": 2, "三段": 3,
            "四段": 4, "五段": 5, "六段": 6,
            "七段": 7, "八段": 8, "九段": 9
        }
        rank_num = rank_numbers.get(rank, 1)

        # 确定要查找的段位范围
        segments_to_check = []

        if rank_num <= 3:
            segments_to_check = ['1-3段']
        elif rank_num <= 6:
            segments_to_check = ['4-6段', '1-3段']  # 向下兼容
        else:
            # 7-9段：检查是否有7-9段+，优先使用7-9段+
            segments_to_check = ['7-9段+', '7-9段']

        # 从语料库中提取建议
        for segment in segments_to_check:
            if segment in action_data:
                advice_list = action_data[segment]
                break

        return advice_list

    def build(self):
        """构建PDF文档"""
        self.doc.build(self.story)
        return self.output_path
