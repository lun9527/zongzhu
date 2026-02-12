#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF报告生成器 V4
目标：在保持业务逻辑正确的前提下，版式尽量对齐项目内参考PDF模板。
"""

import os
from io import BytesIO
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    BaseDocTemplate,
    PageTemplate,
    Frame,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


COLOR_ORANGE = HexColor('#f57c21')
COLOR_TEXT = HexColor('#222222')
COLOR_TEXT_SUB = HexColor('#666666')
COLOR_BORDER = HexColor('#9e9e9e')
COLOR_TABLE_HEAD = HexColor('#f7f7f7')
COLOR_BLUE = HexColor('#4a97f2')
COLOR_YELLOW = HexColor('#f1e35a')

GRADE_LABELS = {
    'A': '卓越',
    'B': '优良',
    'C': '合格',
    'D': '有待提高',
    'E': '急需改善',
}

ABILITY_ORDER = [
    '执行力', '协调力', '优化力',
    '统筹力', '预见力', '业务力',
    '财务力', '领导力', '决策力'
]


class PDFReportGeneratorV4:
    """参考模板风格PDF生成器"""
    _font_cache = None

    def __init__(self, output_path):
        self.output_path = output_path
        self._register_chinese_fonts()

        self.page_width, self.page_height = A4
        self.margin_top = 3.2 * cm
        self.margin_bottom = 2.45 * cm
        self.margin_left = 1.9 * cm
        self.margin_right = 1.9 * cm

        self.doc = BaseDocTemplate(
            output_path,
            pagesize=A4,
            topMargin=self.margin_top,
            bottomMargin=self.margin_bottom,
            leftMargin=self.margin_left,
            rightMargin=self.margin_right,
        )

        self.styles = getSampleStyleSheet()
        self._setup_styles()
        self.story = []

        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(base_dir)

        # 页脚日期（报告生成日期）
        self.report_date_text = self._format_report_date(datetime.now())

    def _register_chinese_fonts(self):
        """注册中文字体（兼容 macOS / Linux / 手动字体路径）。"""
        if PDFReportGeneratorV4._font_cache:
            self.font_regular, self.font_bold = PDFReportGeneratorV4._font_cache
            return

        env_font = os.getenv('PDF_FONT_PATH', '').strip()
        env_bold_font = os.getenv('PDF_FONT_BOLD_PATH', '').strip()
        font_candidates = [
            # 允许通过环境变量手动指定字体
            (env_font, env_bold_font or env_font, None, None, 'ENV_FONT'),
            # Linux 常见 Noto 字体
            ('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 0, 0, 'NotoSansCJK'),
            ('/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf', '/usr/share/fonts/opentype/noto/NotoSansCJKsc-Bold.otf', None, None, 'NotoSansCJKsc'),
            ('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc', 0, 0, 'NotoSansCJK-ttf'),
            # macOS
            ('/System/Library/Fonts/STHeiti Medium.ttc', '/System/Library/Fonts/STHeiti Medium.ttc', 0, 0, 'STHeiti'),
            ('/System/Library/Fonts/PingFang.ttc', '/System/Library/Fonts/PingFang.ttc', 1, 1, 'PingFang'),
            ('/System/Library/Fonts/Hiragino Sans GB.ttc', '/System/Library/Fonts/Hiragino Sans GB.ttc', 0, 0, 'Hiragino'),
        ]

        def _register_font(font_name, path, sub_idx):
            kwargs = {}
            if sub_idx is not None:
                kwargs['subfontIndex'] = sub_idx
            pdfmetrics.registerFont(TTFont(font_name, path, **kwargs))

        for regular_path, bold_path, regular_idx, bold_idx, label in font_candidates:
            if not regular_path:
                continue
            if not os.path.exists(regular_path):
                continue
            if not bold_path or not os.path.exists(bold_path):
                bold_path = regular_path
                bold_idx = regular_idx
            try:
                _register_font('CN-Regular', regular_path, regular_idx)
                _register_font('CN-Bold', bold_path, bold_idx)
                self.font_regular = 'CN-Regular'
                self.font_bold = 'CN-Bold'
                PDFReportGeneratorV4._font_cache = (self.font_regular, self.font_bold)
                print(f"✅ 成功注册字体: {label}")
                return
            except Exception:
                continue

        self.font_regular = 'Helvetica'
        self.font_bold = 'Helvetica-Bold'
        PDFReportGeneratorV4._font_cache = (self.font_regular, self.font_bold)
        print('⚠️ 中文字体注册失败，使用内置字体')

    def _setup_styles(self):
        """定义文档样式"""
        self.styles.add(ParagraphStyle(
            name='V4TitleMain',
            fontName=self.font_bold,
            fontSize=22,
            leading=28,
            alignment=TA_CENTER,
            textColor=colors.black,
            spaceAfter=8,
        ))
        self.styles.add(ParagraphStyle(
            name='V4PartTitleCenter',
            fontName=self.font_bold,
            fontSize=16,
            leading=24,
            alignment=TA_CENTER,
            textColor=COLOR_ORANGE,
            spaceBefore=8,
            spaceAfter=14,
        ))
        self.styles.add(ParagraphStyle(
            name='V4SubHeadingOrange',
            fontName=self.font_bold,
            fontSize=15,
            leading=20,
            alignment=TA_LEFT,
            textColor=COLOR_ORANGE,
            spaceBefore=10,
            spaceAfter=8,
        ))
        self.styles.add(ParagraphStyle(
            name='V4RankLine',
            fontName=self.font_bold,
            fontSize=14.5,
            leading=21,
            textColor=colors.black,
            spaceAfter=4,
        ))
        self.styles.add(ParagraphStyle(
            name='V4Body',
            fontName=self.font_regular,
            fontSize=10.8,
            leading=19,
            alignment=TA_JUSTIFY,
            textColor=COLOR_TEXT,
            spaceAfter=3,
        ))
        self.styles.add(ParagraphStyle(
            name='V4BodyIndent',
            parent=self.styles['V4Body'],
            fontSize=11.4,
            leading=20,
            firstLineIndent=16,
            spaceAfter=6,
        ))
        self.styles.add(ParagraphStyle(
            name='V4BodyBold',
            parent=self.styles['V4Body'],
            fontName=self.font_bold,
        ))
        self.styles.add(ParagraphStyle(
            name='V4Small',
            fontName=self.font_regular,
            fontSize=9.5,
            leading=14,
            alignment=TA_LEFT,
            textColor=COLOR_TEXT_SUB,
            spaceAfter=2,
        ))
        self.styles.add(ParagraphStyle(
            name='V4SectionOrangeCenter',
            fontName=self.font_bold,
            fontSize=17,
            leading=26,
            alignment=TA_CENTER,
            textColor=COLOR_ORANGE,
            spaceAfter=10,
        ))
        self.styles.add(ParagraphStyle(
            name='V4GroupHeading',
            fontName=self.font_bold,
            fontSize=15,
            leading=20,
            textColor=COLOR_ORANGE,
            spaceBefore=10,
            spaceAfter=4,
        ))
        self.styles.add(ParagraphStyle(
            name='V4GroupDesc',
            fontName=self.font_bold,
            fontSize=10,
            leading=14,
            textColor=COLOR_ORANGE,
            spaceAfter=6,
        ))
        self.styles.add(ParagraphStyle(
            name='V4AbilityTag',
            fontName=self.font_bold,
            fontSize=13,
            leading=18,
            textColor=colors.black,
            backColor=COLOR_YELLOW,
            leftIndent=0,
            rightIndent=0,
            spaceBefore=8,
            spaceAfter=5,
        ))
        self.styles.add(ParagraphStyle(
            name='V4Note',
            fontName=self.font_bold,
            fontSize=10.4,
            leading=16,
            textColor=COLOR_TEXT,
            spaceBefore=8,
            spaceAfter=5,
        ))

    def _format_report_date(self, dt_obj):
        weekdays = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
        weekday = weekdays[dt_obj.weekday()]
        return f"报告日期：{dt_obj.year} 年{dt_obj.month} 月{dt_obj.day} 日{weekday}"

    def _set_report_date_now(self):
        self.report_date_text = self._format_report_date(datetime.now())

    def _draw_page_header_footer(self, canvas, doc):
        """绘制固定页眉页脚（与参考模板一致）"""
        canvas.saveState()

        header_img = os.path.join(self.project_root, 'static', 'assets', 'header.jpg')
        footer_img = os.path.join(self.project_root, 'static', 'assets', 'footer.jpg')

        header_h = 2.8 * cm
        footer_h = 1.8 * cm

        if os.path.exists(header_img):
            canvas.drawImage(header_img, 0, self.page_height - header_h,
                             width=self.page_width, height=header_h)
        else:
            canvas.setFillColor(COLOR_ORANGE)
            canvas.rect(0, self.page_height - header_h, self.page_width, header_h, fill=1, stroke=0)

        if os.path.exists(footer_img):
            canvas.drawImage(footer_img, 0, 0, width=self.page_width, height=footer_h)
        else:
            canvas.setFillColor(COLOR_ORANGE)
            canvas.rect(0, 0, self.page_width, footer_h, fill=1, stroke=0)

        # 页脚日期（模板位置：右下角、footer上方）
        canvas.setFillColor(COLOR_TEXT_SUB)
        canvas.setFont(self.font_regular, 8.5)
        canvas.drawRightString(self.page_width - self.margin_right, 1.95 * cm, self.report_date_text)

        canvas.restoreState()

    def generate_radar_chart_v2(self, ability_scores):
        """生成雷达图（蓝色填充，接近参考模板）"""
        plt.rcParams['font.sans-serif'] = ['PingFang SC', 'STHeiti', 'Arial Unicode MS', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        abilities = list(ability_scores.keys())
        max_scores = {
            '执行力': 8, '协调力': 8, '优化力': 8,
            '统筹力': 10, '预见力': 10, '业务力': 10,
            '财务力': 12, '领导力': 12, '决策力': 12,
        }

        values = [ability_scores[a] / max_scores[a] for a in abilities]
        labels = [f'【{a}】' for a in abilities]

        angles = np.linspace(0, 2 * np.pi, len(abilities), endpoint=False).tolist()
        values += values[:1]
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(6.4, 6.1), subplot_kw=dict(polar=True), dpi=170)
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)

        ax.plot(angles, values, color='#4a97f2', linewidth=2)
        ax.fill(angles, values, color='#7fb6f7', alpha=0.45)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, fontsize=9.2, color='#666666')
        ax.set_ylim(0, 1)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'], fontsize=7.4, color='#b0b0b0')

        ax.grid(color='#dadada', linestyle='--', linewidth=0.7)
        ax.spines['polar'].set_color('#d6d6d6')
        ax.spines['polar'].set_linewidth(0.8)

        ax.plot([], [], marker='o', color='#4a97f2', linestyle='None', label='得分')
        ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.14), frameon=False, fontsize=8)

        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=170, bbox_inches='tight', facecolor='white')
        buf.seek(0)
        plt.close(fig)
        return buf

    def _build_underline(self):
        width = self.page_width - self.margin_left - self.margin_right
        line = Table([['']], colWidths=[width], rowHeights=[0.15 * cm])
        line.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 1.1, COLOR_ORANGE),
        ]))
        return line

    def _build_score_table(self, ability_scores):
        left = ['执行力', '协调力', '优化力', '统筹力', '预见力']
        right = ['业务力', '财务力', '领导力', '决策力']
        rows = max(len(left), len(right))

        score_style = ParagraphStyle(
            'V4ScoreItem',
            parent=self.styles['V4BodyBold'],
            fontSize=12,
            leading=18,
            spaceAfter=0,
        )

        data = []
        for i in range(rows):
            left_txt = ''
            right_txt = ''
            if i < len(left):
                a = left[i]
                left_txt = f"<b>【{escape(a)}】</b> {ability_scores.get(a, 0):.2f}"
            if i < len(right):
                a = right[i]
                right_txt = f"<b>【{escape(a)}】</b> {ability_scores.get(a, 0):.2f}"
            data.append([
                Paragraph(left_txt, score_style) if left_txt else Paragraph('', score_style),
                Paragraph(right_txt, score_style) if right_txt else Paragraph('', score_style),
            ])

        table = Table(data, colWidths=[6.8 * cm, 6.8 * cm])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        return table

    def _ability_desc(self, corpus, ability, grade):
        return corpus.get('ability', {}).get(ability, {}).get(grade, {}).get('description', '')

    def _build_dimension_table(self, abilities, ability_grades, corpus):
        content_width = self.page_width - self.margin_left - self.margin_right

        head_style = ParagraphStyle(
            'V4TableHead',
            parent=self.styles['V4BodyBold'],
            fontSize=12,
            leading=16,
        )
        cell_style = ParagraphStyle(
            'V4TableCell',
            parent=self.styles['V4Body'],
            fontSize=11,
            leading=18,
            spaceAfter=0,
        )

        data = [
            [Paragraph('<b>能力维度</b>', head_style), Paragraph('<b>等级及分数解读</b>', head_style)]
        ]

        for ability in abilities:
            grade = ability_grades.get(ability, 'E')
            grade_label = GRADE_LABELS.get(grade, '')
            desc = self._ability_desc(corpus, ability, grade)
            text = f"<b>{escape(grade)} {escape(grade_label)}</b> {escape(desc)}"
            data.append([
                Paragraph(f"<b>{escape(ability)}</b>", cell_style),
                Paragraph(text, cell_style),
            ])

        table = Table(data, colWidths=[2.8 * cm, content_width - 2.8 * cm], repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLOR_TABLE_HEAD),
            ('GRID', (0, 0), (-1, -1), 0.8, COLOR_BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        return table

    def _split_for_carryover(self, text, tail_len=18):
        """将段落末尾切一小段放到下一页，贴近参考模板的跨页效果。"""
        if not text or len(text) <= tail_len + 20:
            return text, ''
        head = text[:-tail_len]
        tail = text[-tail_len:]
        split_idx = max(head.rfind('，'), head.rfind('。'), head.rfind('；'))
        if split_idx > 30:
            return head[:split_idx + 1], head[split_idx + 1:] + tail
        return head, tail

    def _render_rank_section(self, rank, rank_text):
        self.story.append(Paragraph('九段总助测评结果报告', self.styles['V4TitleMain']))
        self.story.append(self._build_underline())
        self.story.append(Spacer(1, 0.35 * cm))

        self.story.append(Paragraph('第一部分：核心发现与总览', self.styles['V4PartTitleCenter']))
        self.story.append(Paragraph('1、综合段位：', self.styles['V4SubHeadingOrange']))
        self.story.append(Paragraph(f'您的当前段位: {escape(rank)}', self.styles['V4RankLine']))

        lines = [line.strip() for line in rank_text.split('\n') if line.strip()]
        carryover = ''
        for idx, line in enumerate(lines):
            if line.startswith('段位释义：'):
                remain = line.split('：', 1)[1].strip() if '：' in line else ''
                if remain:
                    self.story.append(Paragraph(f"<b>段位释义：</b> {escape(remain)}", self.styles['V4BodyIndent']))
                else:
                    self.story.append(Paragraph('<b>段位释义：</b>', self.styles['V4BodyIndent']))
            else:
                text_to_render = line
                if idx == len(lines) - 1:
                    text_to_render, carryover = self._split_for_carryover(line)
                self.story.append(Paragraph(escape(text_to_render), self.styles['V4BodyIndent']))
        return carryover

    def _render_radar_section(self, ability_scores, carryover=''):
        if carryover:
            self.story.append(Paragraph(escape(carryover), self.styles['V4BodyIndent']))
            self.story.append(Spacer(1, 0.1 * cm))
        self.story.append(Paragraph('2、核心能力雷达图：', self.styles['V4SubHeadingOrange']))

        chart_buf = self.generate_radar_chart_v2(ability_scores)
        chart = Image(chart_buf, width=8.8 * cm, height=8.1 * cm)
        chart.hAlign = 'CENTER'
        self.story.append(chart)
        self.story.append(Spacer(1, 0.18 * cm))

        self.story.append(self._build_score_table(ability_scores))
        self.story.append(Spacer(1, 0.15 * cm))

        interp = '解读：一眼看清您的能力结构。面积越大、越均衡，说明能力结构越全面；突出的尖角是您的核心优势，凹陷的角落是您的待发展区。'
        self.story.append(Paragraph(interp, self.styles['V4BodyBold']))

    def _render_section_two(self, ability_grades, corpus):
        self.story.append(PageBreak())
        self.story.append(Paragraph('第二部分：能力维度深度解析', self.styles['V4SectionOrangeCenter']))
        self.story.append(Paragraph('本部分将您的 9 项核心能力划分为三个层级，以便您更清晰地定位自己的发展阶段。', self.styles['V4Small']))
        self.story.append(Spacer(1, 0.2 * cm))

        groups = [
            ('1、核心基石（执行力、协调力、优化力）', '这是您职业大厦的根基，决定了您工作的稳定性和可靠性。', ['执行力', '协调力', '优化力']),
            ('2、价值引擎（统筹力、预见力、业务力）', '这决定了您能否从支持者转变为价值创造者。', ['统筹力', '预见力', '业务力']),
            ('3、领导潜能（财务力、领导力、决策力）', '这预示着您未来能否进入核心管理层，承担更大责任。', ['财务力', '领导力', '决策力']),
        ]

        for title, desc, abilities in groups:
            block = [
                Paragraph(title, self.styles['V4GroupHeading']),
                Paragraph(desc, self.styles['V4GroupDesc']),
                self._build_dimension_table(abilities, ability_grades, corpus),
                Spacer(1, 0.2 * cm),
            ]
            self.story.append(KeepTogether(block))

    def _render_section_three(self, ability_grades, rank, corpus, advice_func):
        self.story.append(PageBreak())
        self.story.append(Paragraph('第三部分：个性化发展行动计划', self.styles['V4SectionOrangeCenter']))
        self.story.append(Paragraph('基于您的测评结果，我们为您量身定制了以下行动建议：', self.styles['V4Small']))

        action_meta = corpus.get('action', {}).get('__meta__', {})
        development_logic = action_meta.get('development_logic') or '发展逻辑：系统化补课，将能力短板提升至及格线以上，消除职业发展的“致命伤”。'
        note_text = action_meta.get('note', '')

        # 1. 优势升华区
        self.story.append(Paragraph('1、优势升华区', self.styles['V4SubHeadingOrange']))
        advantages = [a for a in ABILITY_ORDER if ability_grades.get(a) in ['A', 'B']]

        if not advantages:
            self.story.append(Paragraph('暂无明显优势。', self.styles['V4BodyBold']))
        else:
            for ability in advantages:
                grade = ability_grades[ability]
                self.story.append(Paragraph(escape(ability), self.styles['V4AbilityTag']))
                advices = advice_func(corpus.get('action', {}).get(ability, {}), rank, ability, grade, True)
                if advices:
                    for line in advices:
                        self.story.append(Paragraph(escape(line), self.styles['V4Body']))
                else:
                    self.story.append(Paragraph('继续保持并将优势转化为团队影响力。', self.styles['V4Body']))

        self.story.append(Spacer(1, 0.25 * cm))

        # 2. 重点改善区
        self.story.append(Paragraph('2、重点改善区', self.styles['V4SubHeadingOrange']))
        self.story.append(Paragraph(escape(development_logic), self.styles['V4BodyBold']))

        improvements = [a for a in ABILITY_ORDER if ability_grades.get(a) in ['D', 'E']]

        if not improvements:
            self.story.append(Paragraph('无急需改善项。', self.styles['V4Body']))
        else:
            for ability in improvements:
                grade = ability_grades[ability]
                self.story.append(Paragraph(escape(ability), self.styles['V4AbilityTag']))

                lines = advice_func(corpus.get('action', {}).get(ability, {}), rank, ability, grade, False)
                if not lines:
                    self.story.append(Paragraph('核心任务：进行针对性训练。', self.styles['V4BodyBold']))
                    continue

                core_lines = [x for x in lines if x.startswith('核心任务：')]
                step_lines = [x for x in lines if not x.startswith('核心任务：')]

                if core_lines:
                    for line in core_lines:
                        self.story.append(Paragraph(escape(line), self.styles['V4BodyBold']))

                if step_lines:
                    self.story.append(Paragraph('行动步骤：', self.styles['V4BodyBold']))
                    for line in step_lines:
                        self.story.append(Paragraph(escape(line), self.styles['V4Body']))

        if note_text:
            self.story.append(Spacer(1, 0.2 * cm))
            self.story.append(Paragraph(escape(note_text), self.styles['V4Note']))

        # 3. 核心诊断与发展建议（参考模板为独立页）
        self.story.append(PageBreak())
        self.story.append(Paragraph('3、核心诊断与发展建议', self.styles['V4SubHeadingOrange']))
        self.story.append(Paragraph('请把个人情况、当前困惑或期待发给老师进行详细诊断。', self.styles['V4BodyBold']))

    def build(self, user_info, total_score, rank, ability_scores, ability_grades, rank_text, corpus, advice_func):
        """构建PDF文档"""
        self.story = []
        self._set_report_date_now()

        frame = Frame(
            self.margin_left,
            self.margin_bottom,
            self.page_width - self.margin_left - self.margin_right,
            self.page_height - self.margin_top - self.margin_bottom,
            id='body',
        )
        template = PageTemplate(id='template', frames=[frame], onPage=self._draw_page_header_footer)
        self.doc.addPageTemplates([template])

        # 第一部分
        carryover = self._render_rank_section(rank, rank_text)
        self.story.append(PageBreak())
        self._render_radar_section(ability_scores, carryover)

        # 第二部分
        self._render_section_two(ability_grades, corpus)

        # 第三部分
        self._render_section_three(ability_grades, rank, corpus, advice_func)

        self.doc.build(self.story)
