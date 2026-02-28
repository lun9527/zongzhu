#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量校验生成报告是否符合关键规则。"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional, Set

import pandas as pd

try:
    import pdfplumber
except Exception as exc:  # pragma: no cover
    print(f"[ERROR] 缺少 pdfplumber 依赖: {exc}")
    sys.exit(2)


ABILITY_ORDER = [
    "执行力", "协调力", "优化力",
    "统筹力", "预见力", "业务力",
    "财务力", "领导力", "决策力",
]

ABILITY_MAX = {
    "执行力": 8, "协调力": 8, "优化力": 8,
    "统筹力": 10, "预见力": 10, "业务力": 10,
    "财务力": 12, "领导力": 12, "决策力": 12,
}

THRESHOLDS = {
    8: {"A": (7.2, 8.0), "B": (6.4, 7.1), "C": (5.6, 6.3), "D": (4.8, 5.5), "E": (0, 4.7)},
    10: {"A": (9.0, 10.0), "B": (8.0, 8.9), "C": (7.0, 7.9), "D": (6.0, 6.9), "E": (0, 5.9)},
    12: {"A": (10.8, 12.0), "B": (9.6, 10.7), "C": (8.4, 9.5), "D": (7.2, 8.3), "E": (0, 7.1)},
}


def calc_grade(ability: str, raw_score: float) -> str:
    score = round(float(raw_score), 1)
    max_score = ABILITY_MAX[ability]
    for grade, (min_score, max_score_bound) in THRESHOLDS[max_score].items():
        if min_score <= score <= max_score_bound:
            return grade
    return "E"


def read_pdf_pages(pdf_path: Path) -> list[str]:
    with pdfplumber.open(str(pdf_path)) as pdf:
        return [(p.extract_text() or "") for p in pdf.pages]


def find_pdf_by_seq(report_dir: Path, seq_no: str) -> Optional[Path]:
    seq_no = str(seq_no).strip()
    candidates = sorted(report_dir.glob(f"*NLZ100{seq_no}-*.pdf"))
    return candidates[0] if candidates else None


def check_radar_block(pages: list[str], expected_grades: dict[str, str]) -> list[str]:
    failures = []
    full = "\n".join(pages)
    radar_idx = full.find("2、核心能力雷达图：")
    if radar_idx < 0:
        return ["缺少“2、核心能力雷达图：”标题"]

    after = full[radar_idx:]
    end_idx = after.find("解读：")
    block = after[:end_idx] if end_idx >= 0 else after[:1200]

    # 雷达分值区必须是 A-E，不能是数值
    if re.search(r"【[^】]+】\s*\d", block):
        failures.append("雷达分值区仍出现数字（应为A-E）")

    for ability in ABILITY_ORDER:
        expected = expected_grades[ability]
        pattern = rf"【{re.escape(ability)}】\s*([A-E])"
        match = re.search(pattern, block)
        if not match:
            failures.append(f"雷达分值区缺少 {ability} 等级")
            continue
        actual = match.group(1)
        if actual != expected:
            failures.append(f"{ability} 等级不匹配: 期望 {expected}, 实际 {actual}")
    return failures


def check_note_before_diag(pages: list[str]) -> list[str]:
    failures = []
    full = "\n".join(pages)
    diag_idx = full.find("3、核心诊断与发展建议")
    note_idx = full.find("注：")
    if diag_idx < 0:
        failures.append("缺少“3、核心诊断与发展建议”")
    if note_idx >= 0 and diag_idx >= 0 and note_idx > diag_idx:
        failures.append("“注：”出现在“核心诊断与发展建议”之后")
    return failures


def check_first_section_fragment(pages: list[str]) -> list[str]:
    """检测第一页末句断裂到下一页页首的模式（启发式）。"""
    failures = []
    radar_page = None
    for i, text in enumerate(pages):
        if "2、核心能力雷达图：" in text:
            radar_page = i
            break
    if radar_page is None:
        return failures

    if radar_page > 0:
        page_text = pages[radar_page]
        prefix = page_text.split("2、核心能力雷达图：", 1)[0].strip()
        if prefix:
            compact = re.sub(r"\s+", "", prefix)
            # 仅当是很短残句时判定为断裂问题
            if len(compact) <= 40:
                failures.append("雷达图页标题前疑似存在短句残片（第一页跨页断裂）")
    return failures


def run_checks(excel_path: Path, report_dir: Path, only_seq: Optional[Set[str]]) -> int:
    df = pd.read_excel(str(excel_path))
    total_rows = len(df)
    checked = 0
    fail_count = 0
    details: list[str] = []

    for _, row in df.iterrows():
        seq = str(row.get("序号", "")).strip()
        if only_seq and seq not in only_seq:
            continue

        pdf_file = find_pdf_by_seq(report_dir, seq)
        if not pdf_file:
            fail_count += 1
            details.append(f"[NLZ100{seq}] 缺少PDF文件")
            continue

        expected = {}
        for ability in ABILITY_ORDER:
            col = f"【{ability}】"
            score = row.get(col, 0)
            score = float(score) if pd.notna(score) else 0.0
            expected[ability] = calc_grade(ability, score)

        pages = read_pdf_pages(pdf_file)
        item_failures = []
        item_failures.extend(check_radar_block(pages, expected))
        item_failures.extend(check_note_before_diag(pages))
        item_failures.extend(check_first_section_fragment(pages))

        checked += 1
        if item_failures:
            fail_count += 1
            details.append(f"[NLZ100{seq}] " + "；".join(item_failures))

    print(f"总行数: {total_rows}")
    print(f"已校验: {checked}")
    print(f"失败数: {fail_count}")
    if details:
        print("---- 失败详情 ----")
        for line in details[:200]:
            print(line)
    return 1 if fail_count else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="批量校验PDF报告质量")
    parser.add_argument("--excel", required=True, help="Excel 文件路径")
    parser.add_argument("--reports-dir", required=True, help="报告目录")
    parser.add_argument("--seq", nargs="*", help="仅校验指定序号，如 84 76")
    args = parser.parse_args()

    excel_path = Path(args.excel).expanduser().resolve()
    report_dir = Path(args.reports_dir).expanduser().resolve()

    if not excel_path.exists():
        print(f"[ERROR] Excel 不存在: {excel_path}")
        return 2
    if not report_dir.exists():
        print(f"[ERROR] 报告目录不存在: {report_dir}")
        return 2

    seq_set = {str(x).strip() for x in args.seq} if args.seq else None
    return run_checks(excel_path, report_dir, seq_set)


if __name__ == "__main__":
    sys.exit(main())
