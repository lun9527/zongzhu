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
    CondPageBreak,
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

# 模板雷达图顺时针顺序（从12点方向开始）
RADAR_ABILITY_ORDER = [
    '执行力', '决策力', '领导力',
    '财务力', '业务力', '预见力',
    '统筹力', '优化力', '协调力',
]


class PDFReportGeneratorV4:
    """参考模板风格PDF生成器"""
    _font_cache = None

    def __init__(self, output_path):
        self.output_path = output_path
        self._register_chinese_fonts()

        self.page_width, self.page_height = A4
        # 按模板坐标下移版心，同时保持分页稳定
        self.margin_top = 4.35 * cm
        self.margin_bottom = 1.9 * cm
        # 模板版心更窄，正文起点更靠内
        self.margin_left = 3.0 * cm
        self.margin_right = 3.0 * cm

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
            if len(PDFReportGeneratorV4._font_cache) == 3:
                self.font_regular, self.font_bold, self.font_small = PDFReportGeneratorV4._font_cache
            else:
                self.font_regular, self.font_bold = PDFReportGeneratorV4._font_cache
                self.font_small = self.font_regular
            return

        base_dir = os.path.dirname(os.path.abspath(__file__))
        template_font_dir = os.path.join(base_dir, 'fonts', 'template')
        template_regular = os.path.join(template_font_dir, 'MicrosoftYaHei-Regular.ttf')
        template_bold = os.path.join(template_font_dir, 'MicrosoftYaHei-Bold.ttf')
        office_font_dir = os.path.expanduser(
            '~/Library/Group Containers/UBF8T346G9.Office/FontCache/4/CloudFonts/Microsoft YaHei UI'
        )
        office_regular = os.path.join(office_font_dir, '48046837801.ttf')
        office_bold = os.path.join(office_font_dir, '47005771285.ttf')

        env_font = os.getenv('PDF_FONT_PATH', '').strip()
        env_bold_font = os.getenv('PDF_FONT_BOLD_PATH', '').strip()
        font_candidates = [
            # 允许通过环境变量手动指定字体
            (env_font, env_bold_font or env_font, None, None, 'ENV_FONT'),
            # Office 云字体缓存（完整字形，优先保证 A-E 等级不丢字）
            (office_regular, office_bold, None, None, 'Office-YaHeiUI'),
            # 项目内模板字体（从案例模板提取，作为高相似度回退）
            (template_regular, template_bold, None, None, 'Template-YaHei'),
            # Microsoft YaHei（模板同款优先）
            (os.path.expanduser('~/Library/Fonts/Microsoft YaHei.ttf'),
             os.path.expanduser('~/Library/Fonts/Microsoft YaHei Bold.ttf'), None, None, 'YaHei-User'),
            ('/Library/Fonts/Microsoft YaHei.ttf', '/Library/Fonts/Microsoft YaHei Bold.ttf', None, None, 'YaHei-Library'),
            ('/Library/Fonts/msyh.ttf', '/Library/Fonts/msyhbd.ttf', None, None, 'YaHei-msyh'),
            (r'C:\Windows\Fonts\msyh.ttc', r'C:\Windows\Fonts\msyhbd.ttc', 0, 0, 'YaHei-Windows'),
            (r'C:\Windows\Fonts\msyh.ttf', r'C:\Windows\Fonts\msyhbd.ttf', None, None, 'YaHei-Windows-ttf'),
            # Linux 常见 Noto 字体
            ('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 0, 0, 'NotoSansCJK'),
            ('/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf', '/usr/share/fonts/opentype/noto/NotoSansCJKsc-Bold.otf', None, None, 'NotoSansCJKsc'),
            ('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc', 0, 0, 'NotoSansCJK-ttf'),
            # macOS 备用（Songti 支持真实粗体，最后再退回 STHeiti）
            ('/System/Library/Fonts/Supplemental/Songti.ttc', '/System/Library/Fonts/Supplemental/Songti.ttc', 6, 1, 'Songti-RegularBold'),
            # macOS 兜底
            ('/System/Library/Fonts/STHeiti Medium.ttc', '/System/Library/Fonts/STHeiti Medium.ttc', 0, 0, 'STHeiti'),
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
                # 小号文字统一沿用主中文字体，避免模板子集字体缺字
                self.font_small = self.font_regular
                PDFReportGeneratorV4._font_cache = (self.font_regular, self.font_bold, self.font_small)
                print(f"✅ 成功注册字体: {label}")
                return
            except Exception:
                continue

        self.font_regular = 'Helvetica'
        self.font_bold = 'Helvetica-Bold'
        self.font_small = self.font_regular
        PDFReportGeneratorV4._font_cache = (self.font_regular, self.font_bold, self.font_small)
        print('⚠️ 中文字体注册失败，使用内置字体')

    def _setup_styles(self):
        """定义文档样式"""
        self.styles.add(ParagraphStyle(
            name='V4TitleMain',
            fontName=self.font_bold,
            fontSize=21.96,
            leading=28,
            alignment=TA_CENTER,
            textColor=colors.black,
            spaceAfter=8,
        ))
        self.styles.add(ParagraphStyle(
            name='V4PartTitleCenter',
            fontName=self.font_bold,
            fontSize=18,
            leading=26,
            alignment=TA_CENTER,
            textColor=COLOR_ORANGE,
            spaceBefore=8,
            spaceAfter=16,
        ))
        self.styles.add(ParagraphStyle(
            name='V4SubHeadingOrange',
            fontName=self.font_bold,
            fontSize=15.96,
            leading=22,
            alignment=TA_LEFT,
            textColor=COLOR_ORANGE,
            spaceBefore=10,
            spaceAfter=8,
            wordWrap='CJK',
        ))
        self.styles.add(ParagraphStyle(
            name='V4SubHeadingOrangeCompact',
            parent=self.styles['V4SubHeadingOrange'],
            fontSize=15.0,
            leading=20.5,
            spaceBefore=2,
            spaceAfter=4,
        ))
        self.styles.add(ParagraphStyle(
            name='V4RankLine',
            fontName=self.font_bold,
            fontSize=15,
            leading=20,
            textColor=colors.black,
            spaceAfter=4,
            wordWrap='CJK',
        ))
        self.styles.add(ParagraphStyle(
            name='V4Body',
            fontName=self.font_regular,
            fontSize=14.04,
            leading=22.5,
            alignment=TA_LEFT,
            textColor=COLOR_TEXT,
            spaceAfter=2,
            wordWrap='CJK',
            splitLongWords=False,
            allowWidows=0,
            allowOrphans=0,
        ))
        self.styles.add(ParagraphStyle(
            name='V4BodyIndent',
            parent=self.styles['V4Body'],
            fontSize=15.0,
            leading=31.2,
            firstLineIndent=30,
            spaceAfter=0,
        ))
        self.styles.add(ParagraphStyle(
            name='V4BodyBold',
            parent=self.styles['V4Body'],
            fontName=self.font_bold,
        ))
        self.styles.add(ParagraphStyle(
            name='V4Small',
            fontName=self.font_small,
            fontSize=10.56,
            leading=15.84,
            alignment=TA_LEFT,
            textColor=COLOR_TEXT_SUB,
            spaceAfter=2,
            wordWrap='CJK',
        ))
        self.styles.add(ParagraphStyle(
            name='V4SectionOrangeCenterLarge',
            fontName=self.font_bold,
            fontSize=18,
            leading=26,
            alignment=TA_CENTER,
            textColor=COLOR_ORANGE,
            spaceAfter=10,
        ))
        self.styles.add(ParagraphStyle(
            name='V4SectionOrangeCenterMedium',
            fontName=self.font_bold,
            fontSize=15.0,
            leading=21.5,
            alignment=TA_CENTER,
            textColor=COLOR_ORANGE,
            spaceAfter=8,
        ))
        self.styles.add(ParagraphStyle(
            name='V4GroupHeading',
            fontName=self.font_bold,
            fontSize=15.96,
            leading=22,
            textColor=COLOR_ORANGE,
            spaceBefore=10,
            spaceAfter=4,
            wordWrap='CJK',
        ))
        self.styles.add(ParagraphStyle(
            name='V4GroupDesc',
            fontName=self.font_bold,
            fontSize=10.56,
            leading=14.8,
            textColor=COLOR_ORANGE,
            spaceAfter=6,
            wordWrap='CJK',
        ))
        self.styles.add(ParagraphStyle(
            name='V4AbilityTag',
            fontName=self.font_bold,
            fontSize=14.04,
            leading=20,
            textColor=colors.black,
            backColor=COLOR_YELLOW,
            leftIndent=0,
            rightIndent=0,
            spaceBefore=5,
            spaceAfter=3,
        ))
        self.styles.add(ParagraphStyle(
            name='V4Note',
            fontName=self.font_bold,
            fontSize=14.04,
            leading=22.5,
            textColor=COLOR_TEXT,
            spaceBefore=2,
            spaceAfter=2,
            wordWrap='CJK',
        ))
        self.styles.add(ParagraphStyle(
            name='V4ActionBody',
            parent=self.styles['V4Body'],
            leading=20.2,
            spaceAfter=1,
        ))
        self.styles.add(ParagraphStyle(
            name='V4ActionBodyBold',
            parent=self.styles['V4ActionBody'],
            fontName=self.font_bold,
        ))
        self.styles.add(ParagraphStyle(
            name='V4ActionNote',
            parent=self.styles['V4ActionBodyBold'],
            leading=19.8,
        ))

    def _format_report_date(self, dt_obj):
        weekdays = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
        weekday = weekdays[dt_obj.weekday()]
        return f"报告日期：{dt_obj.year} 年{dt_obj.month} 月{dt_obj.day} 日{weekday}"

    def _set_report_date_now(self):
        self.report_date_text = self._format_report_date(datetime.now())

    def _inline_bold(self, text):
        return f"<font name='{self.font_bold}'>{escape(text)}</font>"

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
        canvas.setFont(self.font_small, 8.5)
        canvas.drawRightString(self.page_width - self.margin_right, 1.95 * cm, self.report_date_text)

        canvas.restoreState()

    def generate_radar_chart_v2(self, ability_scores):
        """生成雷达图（蓝色填充，接近参考模板）"""
        plt.rcParams['font.sans-serif'] = [
            'Microsoft YaHei', 'Microsoft YaHei UI',
            'PingFang SC', 'STHeiti', 'Noto Sans CJK SC',
            'Arial Unicode MS', 'SimHei', 'DejaVu Sans'
        ]
        plt.rcParams['axes.unicode_minus'] = False

        # 固定雷达图能力顺序，避免字典顺序导致的错位
        abilities = [a for a in RADAR_ABILITY_ORDER if a in ability_scores]
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

    def _build_score_table(self, ability_scores, ability_grades):
        left = ['执行力', '协调力', '优化力', '统筹力', '预见力']
        right = ['业务力', '财务力', '领导力', '决策力']
        rows = max(len(left), len(right))

        score_style = ParagraphStyle(
            'V4ScoreItem',
            parent=self.styles['V4Body'],
            fontSize=14.04,
            leading=22.5,
            spaceAfter=0,
        )

        data = []
        for i in range(rows):
            left_txt = ''
            right_txt = ''
            if i < len(left):
                a = left[i]
                grade = ability_grades.get(a, self._grade_for_score(a, ability_scores.get(a, 0)))
                left_txt = f"【{escape(a)}】 {escape(grade)}"
            if i < len(right):
                a = right[i]
                grade = ability_grades.get(a, self._grade_for_score(a, ability_scores.get(a, 0)))
                right_txt = f"【{escape(a)}】 {escape(grade)}"
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

    def _grade_for_score(self, ability, score):
        """按能力满分区间返回 A-E 等级（与主逻辑一致）。"""
        max_scores = {
            '执行力': 8, '协调力': 8, '优化力': 8,
            '统筹力': 10, '预见力': 10, '业务力': 10,
            '财务力': 12, '领导力': 12, '决策力': 12,
        }
        thresholds = {
            8: {'A': (7.2, 8.0), 'B': (6.4, 7.1), 'C': (5.6, 6.3), 'D': (4.8, 5.5), 'E': (0, 4.7)},
            10: {'A': (9.0, 10.0), 'B': (8.0, 8.9), 'C': (7.0, 7.9), 'D': (6.0, 6.9), 'E': (0, 5.9)},
            12: {'A': (10.8, 12.0), 'B': (9.6, 10.7), 'C': (8.4, 9.5), 'D': (7.2, 8.3), 'E': (0, 7.1)},
        }

        max_score = max_scores.get(ability, 10)
        score = round(float(score), 1)
        for grade, (min_score, max_score) in thresholds[max_score].items():
            if min_score <= score <= max_score:
                return grade
        return 'E'

    def _build_dimension_table(self, abilities, ability_grades, corpus):
        content_width = self.page_width - self.margin_left - self.margin_right

        head_style = ParagraphStyle(
            'V4TableHead',
            parent=self.styles['V4BodyBold'],
            fontSize=14.04,
            leading=22.5,
        )
        cell_style = ParagraphStyle(
            'V4TableCell',
            parent=self.styles['V4Body'],
            fontSize=14.04,
            leading=22.5,
            spaceAfter=0,
        )
        cell_style_bold = ParagraphStyle(
            'V4TableCellBold',
            parent=cell_style,
            fontName=self.font_bold,
        )

        data = [
            [Paragraph('<b>能力维度</b>', head_style), Paragraph('<b>等级及分数解读</b>', head_style)]
        ]

        for ability in abilities:
            grade = ability_grades.get(ability, 'E')
            grade_label = GRADE_LABELS.get(grade, '')
            desc = self._ability_desc(corpus, ability, grade)
            text = f"{self._inline_bold(f'{grade} {grade_label}')} {escape(desc)}"
            data.append([
                Paragraph(escape(ability), cell_style_bold),
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

    def _render_rank_section(self, rank, rank_text):
        self.story.append(Spacer(1, 0.28 * cm))
        self.story.append(Paragraph('九段总助测评结果报告', self.styles['V4TitleMain']))
        self.story.append(self._build_underline())
        self.story.append(Spacer(1, 0.35 * cm))

        self.story.append(Paragraph('第一部分：核心发现与总览', self.styles['V4PartTitleCenter']))
        self.story.append(Paragraph('1、综合段位：', self.styles['V4SubHeadingOrange']))
        self.story.append(Paragraph(f'您的当前段位：{escape(rank)}', self.styles['V4RankLine']))
        self.story.append(Spacer(1, 0.35 * cm))

        lines = [line.strip() for line in rank_text.split('\n') if line.strip()]
        for line in lines:
            if line.startswith('段位释义：'):
                remain = line.split('：', 1)[1].strip() if '：' in line else ''
                if remain:
                    self.story.append(Paragraph(
                        f"{self._inline_bold('段位释义：')} {escape(remain)}",
                        self.styles['V4BodyIndent']
                    ))
                else:
                    self.story.append(Paragraph(self._inline_bold('段位释义：'), self.styles['V4BodyIndent']))
            else:
                self.story.append(Paragraph(escape(line), self.styles['V4BodyIndent']))

    def _render_radar_section(self, ability_scores, ability_grades):
        self.story.append(Spacer(1, 0.18 * cm))
        self.story.append(Paragraph('2、核心能力雷达图：', self.styles['V4SubHeadingOrange']))

        chart_buf = self.generate_radar_chart_v2(ability_scores)
        chart = Image(chart_buf, width=8.8 * cm, height=8.1 * cm)
        chart.hAlign = 'CENTER'
        self.story.append(chart)
        self.story.append(Spacer(1, 0.18 * cm))

        self.story.append(self._build_score_table(ability_scores, ability_grades))
        self.story.append(Spacer(1, 0.15 * cm))

        interp = f"{self._inline_bold('解读：')}一眼看清您的能力结构。面积越大、越均衡，说明能力结构越全面；突出的尖角是您的核心优势，凹陷的角落是您的待发展区。"
        self.story.append(Paragraph(interp, self.styles['V4Body']))

    def _render_section_two(self, ability_grades, corpus):
        self.story.append(PageBreak())
        self.story.append(Spacer(1, 0.22 * cm))
        self.story.append(Paragraph('第二部分：能力维度深度解析', self.styles['V4SectionOrangeCenterLarge']))
        self.story.append(Paragraph('本部分将您的9项核心能力划分为三个层级，以便您更清晰地定位自己的发展阶段。', self.styles['V4Small']))
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
        # 第三部分固定从新页开始（与第一、二部分一致）
        self.story.append(PageBreak())
        self.story.append(Spacer(1, 0.12 * cm))
        self.story.append(Paragraph('第三部分：个性化发展行动计划', self.styles['V4SectionOrangeCenterMedium']))
        self.story.append(Paragraph('基于您的测评结果，我们为您量身定制了以下行动建议。', self.styles['V4Small']))

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
                block = [Paragraph(escape(ability), self.styles['V4AbilityTag'])]
                advices = advice_func(corpus.get('action', {}).get(ability, {}), rank, ability, grade, True)
                if advices:
                    for line in advices:
                        block.append(Paragraph(escape(line), self.styles['V4ActionBody']))
                else:
                    block.append(Paragraph('继续保持并将优势转化为团队影响力。', self.styles['V4ActionBody']))
                # 第三部分按自然流式排版，避免末页只剩零碎段落
                self.story.extend(block)

        self.story.append(Spacer(1, 0.25 * cm))

        # 2. 重点改善区
        self.story.append(Paragraph('2、重点改善区', self.styles['V4SubHeadingOrange']))
        self.story.append(Paragraph(escape(development_logic), self.styles['V4ActionBodyBold']))

        improvements = [a for a in ABILITY_ORDER if ability_grades.get(a) in ['D', 'E']]

        if not improvements:
            self.story.append(Paragraph('无急需改善项。', self.styles['V4ActionBody']))
        else:
            for ability in improvements:
                grade = ability_grades[ability]
                block = [Paragraph(escape(ability), self.styles['V4AbilityTag'])]

                lines = advice_func(corpus.get('action', {}).get(ability, {}), rank, ability, grade, False)
                if not lines:
                    block.append(Paragraph('核心任务：进行针对性训练。', self.styles['V4ActionBodyBold']))
                    self.story.extend(block)
                    continue

                core_lines = [x for x in lines if x.startswith('核心任务：')]
                step_lines = [x for x in lines if not x.startswith('核心任务：')]

                if core_lines:
                    for line in core_lines:
                        block.append(Paragraph(escape(line), self.styles['V4ActionBodyBold']))

                if step_lines:
                    block.append(Paragraph('行动步骤：', self.styles['V4ActionBodyBold']))
                    for line in step_lines:
                        block.append(Paragraph(escape(line), self.styles['V4ActionBody']))

                self.story.extend(block)

        if note_text:
            self.story.append(Paragraph(escape(note_text), self.styles['V4ActionNote']))

        # 3. 核心诊断与发展建议（紧接上一段，完全自然续排）
        self.story.append(Paragraph('3、核心诊断与发展建议', self.styles['V4SubHeadingOrangeCompact']))
        self.story.append(Paragraph('请把个人情况、当前困惑或期待发给老师进行详细诊断。', self.styles['V4ActionBodyBold']))

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
        self._render_rank_section(rank, rank_text)
        self.story.append(CondPageBreak(13.6 * cm))
        self._render_radar_section(ability_scores, ability_grades)

        # 第二部分
        self._render_section_two(ability_grades, corpus)

        # 第三部分
        self._render_section_three(ability_grades, rank, corpus, advice_func)

        self.doc.build(self.story)
