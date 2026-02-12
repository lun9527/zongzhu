#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF报告生成器
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

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


class PDFReportGenerator:
    """PDF报告生成器"""

    def __init__(self, output_path):
        """初始化PDF生成器"""
        self.output_path = output_path

        # 注册中文字体
        self._register_chinese_fonts()

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
        """注册中文字体"""
        try:
            # 尝试注册PingFang SC（macOS系统字体）
            pdfmetrics.registerFont(TTFont('ChineseFont', '/System/Library/Fonts/PingFang.ttc', subfontIndex=1))
            self.chinese_font = 'ChineseFont'
        except:
            try:
                # 尝试注册STHeiti（华文黑体）
                pdfmetrics.registerFont(TTFont('ChineseFont', '/System/Library/Fonts/STHeiti Medium.ttc'))
                self.chinese_font = 'ChineseFont'
            except:
                # 如果都失败，使用默认字体
                self.chinese_font = 'Helvetica'

    def _setup_styles(self):
        """设置自定义样式"""
        # 一级标题（先创建基础样式）
        if 'MyHeading1' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='MyHeading1',
                fontName=self.chinese_font,
                fontSize=16,
                spaceAfter=12,
                spaceBefore=12,
                textColor=colors.HexColor('#2C3E50')
            ))

        # 二级标题
        if 'MyHeading2' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='MyHeading2',
                fontName=self.chinese_font,
                fontSize=14,
                spaceAfter=10,
                spaceBefore=10,
                textColor=colors.HexColor('#34495E')
            ))

        # 正文样式
        if 'MyBodyText' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='MyBodyText',
                fontName=self.chinese_font,
                fontSize=10,
                spaceAfter=8,
                alignment=TA_JUSTIFY,
                textColor=colors.HexColor('#2C3E50')
            ))

        # 小标题
        if 'MySmallHeading' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='MySmallHeading',
                fontName=self.chinese_font,
                fontSize=11,
                spaceAfter=6,
                spaceBefore=6,
                textColor=colors.HexColor('#2C3E50')
            ))

        # 主标题样式（继承MyHeading1）
        if 'ChineseTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='ChineseTitle',
                parent=self.styles['MyHeading1'],
                fontName=self.chinese_font,
                fontSize=24,
                alignment=TA_CENTER,
                spaceAfter=20,
                textColor=colors.HexColor('#2C3E50')
            ))

        # 段位标题样式（继承MyHeading1）
        if 'RankTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='RankTitle',
                parent=self.styles['MyHeading1'],
                fontName=self.chinese_font,
                fontSize=18,
                alignment=TA_CENTER,
                spaceAfter=12,
                textColor=colors.HexColor('#E74C3C')
            ))

    def generate_radar_chart(self, ability_scores, ability_grades):
        """生成能力雷达图"""
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['PingFang SC', 'STHeiti', 'Arial Unicode MS', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        # 准备数据
        abilities = list(ability_scores.keys())
        scores = list(ability_scores.values())
        grades = list(ability_grades.values())

        # 归一化分数（转换为百分比）
        max_scores = {
            "执行力": 8, "协调力": 8, "优化力": 8,
            "统筹力": 10, "预见力": 10, "业务力": 10,
            "财务力": 12, "领导力": 12, "决策力": 12
        }

        normalized_scores = [ability_scores[ability] / max_scores[ability] * 100 for ability in abilities]

        # 计算角度
        angles = np.linspace(0, 2 * np.pi, len(abilities), endpoint=False).tolist()
        normalized_scores += normalized_scores[:1]
        angles += angles[:1]

        # 创建图形
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))

        # 绘制雷达图
        ax.plot(angles, normalized_scores, 'o-', linewidth=2, color='#E74C3C', label='能力得分')
        ax.fill(angles, normalized_scores, alpha=0.25, color='#E74C3C')

        # 设置刻度
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(abilities, fontsize=10)
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'], fontsize=8)
        ax.grid(True, linestyle='--', alpha=0.7)

        # 添加标题
        plt.title('核心能力雷达图', fontsize=16, fontweight='bold', pad=20)

        # 保存到内存
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close()

        return buf

    def add_cover_page(self, user_info, total_score, rank):
        """添加封面页"""
        # 主标题
        self.story.append(Paragraph("九段总助胜任力专业测评报告", self.styles['ChineseTitle']))
        self.story.append(Spacer(1, 2*cm))

        # 创建信息表格
        data = [
            ['序号', f"NLZ100{user_info['seq_no']}"],
            ['微信昵称', user_info['nickname']],
            ['测评时间', user_info['test_time']],
            ['', ''],
            ['【当前段位】', rank],
            ['【测评得分】', f"{total_score:.2f}分"]
        ]

        table = Table(data, colWidths=[5*cm, 8*cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
            ('SPAN', (0, 4), (1, 4)),  # 段位行
            ('SPAN', (0, 5), (1, 5)),  # 得分行
        ]))

        # 特殊样式：段位行
        table.setStyle(TableStyle([
            ('TEXTCOLOR', (0, 4), (1, 4), colors.HexColor('#E74C3C')),
            ('FONTSIZE', (0, 4), (1, 4), 16),
            ('ALIGN', (0, 4), (1, 4), 'CENTER'),
            ('BACKGROUND', (0, 4), (1, 4), colors.HexColor('#FADBD8')),
        ]))

        self.story.append(table)
        self.story.append(Spacer(1, 2*cm))

    def add_rank_description(self, rank_text):
        """添加段位释义"""
        self.story.append(Paragraph("【段位释义】", self.styles['MyHeading1']))

        # 分段处理段位释义
        lines = rank_text.split('\n')
        for line in lines:
            if line.strip():
                self.story.append(Paragraph(line.strip(), self.styles['MyBodyText']))

        self.story.append(Spacer(1, 1*cm))

    def add_radar_chart(self, ability_scores, ability_grades):
        """添加雷达图"""
        self.story.append(Paragraph("【核心能力雷达图】", self.styles['MyHeading1']))

        # 生成雷达图
        chart_buf = self.generate_radar_chart(ability_scores, ability_grades)
        img = Image(chart_buf, width=12*cm, height=12*cm)
        self.story.append(img)
        self.story.append(Spacer(1, 0.5*cm))

        # 解读说明
        interpretation = """一眼看清您的能力结构。面积越大、越均衡，说明能力结构越全面；
突出的尖角是您的核心优势，凹陷的角落是您的待发展区。"""
        self.story.append(Paragraph(interpretation, self.styles['MyBodyText']))

        # 能力得分明细表格
        self.story.append(Spacer(1, 0.5*cm))
        self.story.append(Paragraph("【能力得分明细】", self.styles['MySmallHeading']))

        data = [['能力维度', '得分', '等级']]
        for ability, score in ability_scores.items():
            grade = ability_grades[ability]
            data.append([ability, f"{score:.2f}", f"{grade}级"])

        table = Table(data, colWidths=[5*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ]))

        self.story.append(table)
        self.story.append(Spacer(1, 1*cm))

    def add_ability_analysis(self, ability_scores, ability_grades, corpus):
        """添加能力维度深度解析"""
        self.story.append(PageBreak())
        self.story.append(Paragraph("第二部分：能力维度深度解析", self.styles['ChineseTitle']))
        self.story.append(Spacer(1, 1*cm))

        # 核心基石
        self.story.append(Paragraph("【核心基石】", self.styles['MyHeading1']))
        self.story.append(Paragraph("这是您职业大厦的根基，决定了您工作的稳定性和可靠性。",
                                    self.styles['MyBodyText']))
        self.story.append(Spacer(1, 0.5*cm))

        for ability in ["执行力", "协调力", "优化力"]:
            score = ability_scores[ability]
            grade = ability_grades[ability]

            self.story.append(Paragraph(f"{ability} ({grade}级) - {score:.2f}分",
                                        self.styles['MySmallHeading']))

            if 'ability' in corpus and ability in corpus['ability']:
                if grade in corpus['ability'][ability]:
                    desc = corpus['ability'][ability][grade].get('description', '')
                    self.story.append(Paragraph(desc, self.styles['MyBodyText']))

            self.story.append(Spacer(1, 0.5*cm))

        # 价值引擎
        self.story.append(Paragraph("【价值引擎】", self.styles['MyHeading1']))
        self.story.append(Paragraph("这决定了您能否从支持者转变为价值创造者。",
                                    self.styles['MyBodyText']))
        self.story.append(Spacer(1, 0.5*cm))

        for ability in ["统筹力", "预见力", "业务力"]:
            score = ability_scores[ability]
            grade = ability_grades[ability]

            self.story.append(Paragraph(f"{ability} ({grade}级) - {score:.2f}分",
                                        self.styles['MySmallHeading']))

            if 'ability' in corpus and ability in corpus['ability']:
                if grade in corpus['ability'][ability]:
                    desc = corpus['ability'][ability][grade].get('description', '')
                    self.story.append(Paragraph(desc, self.styles['MyBodyText']))

            self.story.append(Spacer(1, 0.5*cm))

        # 领导潜能
        self.story.append(Paragraph("【领导潜能】", self.styles['MyHeading1']))
        self.story.append(Paragraph("这预示着您未来能否进入核心管理层，承担更大责任。",
                                    self.styles['MyBodyText']))
        self.story.append(Spacer(1, 0.5*cm))

        for ability in ["财务力", "领导力", "决策力"]:
            score = ability_scores[ability]
            grade = ability_grades[ability]

            self.story.append(Paragraph(f"{ability} ({grade}级) - {score:.2f}分",
                                        self.styles['MySmallHeading']))

            if 'ability' in corpus and ability in corpus['ability']:
                if grade in corpus['ability'][ability]:
                    desc = corpus['ability'][ability][grade].get('description', '')
                    self.story.append(Paragraph(desc, self.styles['MyBodyText']))

            self.story.append(Spacer(1, 0.5*cm))

    def add_action_plan(self, ability_grades, rank, corpus):
        """添加个性化发展行动计划"""
        self.story.append(PageBreak())
        self.story.append(Paragraph("第三部分：个性化发展行动计划", self.styles['ChineseTitle']))
        self.story.append(Spacer(1, 1*cm))

        # 优势升华区
        self.story.append(Paragraph("【1、优势升华区】", self.styles['MyHeading1']))
        advantages = [ability for ability, grade in ability_grades.items() if grade in ['A', 'B']]

        if advantages:
            for ability in advantages:
                self.story.append(Paragraph(f"{ability}：", self.styles['MySmallHeading']))
                self.story.append(Paragraph(
                    "继续保持和提升您的优势，将个人能力转化为团队影响力。",
                    self.styles['MyBodyText']
                ))
                self.story.append(Spacer(1, 0.3*cm))
        else:
            self.story.append(Paragraph("暂无明显优势", self.styles['MyBodyText']))

        self.story.append(Spacer(1, 0.8*cm))

        # 重点改善区
        self.story.append(Paragraph("【2、重点改善区】", self.styles['MyHeading1']))
        improvements = [ability for ability, grade in ability_grades.items() if grade in ['D', 'E']]

        if improvements:
            for ability in improvements:
                self.story.append(Paragraph(f"{ability}：", self.styles['MySmallHeading']))
                self.story.append(Paragraph(
                    "系统化补课，将能力短板提升至及格线以上，消除职业发展的'致命伤'。",
                    self.styles['MyBodyText']
                ))
                self.story.append(Spacer(1, 0.3*cm))
        else:
            self.story.append(Paragraph("无急需改善项", self.styles['MyBodyText']))

        self.story.append(Spacer(1, 0.8*cm))

        # 核心诊断
        self.story.append(Paragraph("【3、核心诊断与发展建议】", self.styles['MyHeading1']))
        self.story.append(Paragraph(
            "请把个人情况、当前困惑或期待发给老师进行详细诊断。",
            self.styles['MyBodyText']
        ))
        self.story.append(Spacer(1, 2*cm))

        # 页脚
        footer = f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        self.story.append(Paragraph(footer, self.styles['MyBodyText']))

    def build(self):
        """构建PDF文档"""
        self.doc.build(self.story)
        return self.output_path
