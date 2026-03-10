#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核心判读逻辑回归测试（基于三份txt语料）。"""

import os
import sys
import unittest


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, SKILL_DIR)

from main import AssessmentReportGenerator  # noqa: E402


class LogicRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator = AssessmentReportGenerator()

    def test_ability_corpus_has_full_grades(self):
        corpus = self.generator.corpus.get('ability', {})
        self.assertEqual(set(corpus.keys()), set(self.generator.abilities.keys()))

        for ability, grade_map in corpus.items():
            self.assertEqual(
                set(grade_map.keys()),
                {'A', 'B', 'C', 'D', 'E'},
                msg=f"{ability} 未完整解析 A-E 等级"
            )
            for grade in ['A', 'B', 'C', 'D', 'E']:
                self.assertTrue(
                    grade_map[grade]['description'].strip(),
                    msg=f"{ability} {grade} 级描述为空"
                )

    def test_action_corpus_supports_1_6_segment(self):
        action = self.generator.corpus.get('action', {})
        self.assertIn('统筹力', action)
        self.assertIn('1-6段', action['统筹力'].get('advantage', {}))
        self.assertGreater(len(action['统筹力']['advantage']['1-6段']), 0)

    def test_rank_three_prefers_1_6_when_1_3_absent(self):
        action_data = self.generator.corpus['action']['统筹力']
        advices = self.generator._get_action_advice(
            action_data=action_data,
            rank='三段',
            ability_name='统筹力',
            grade='B',
            advantage=True
        )
        self.assertTrue(advices)
        self.assertIn('可视化的进度看板', advices[0])

    def test_low_rank_special_ability_a_uses_7_9_plus(self):
        action_data = self.generator.corpus['action']['财务力']
        advices = self.generator._get_action_advice(
            action_data=action_data,
            rank='五段',
            ability_name='财务力',
            grade='A',
            advantage=True
        )
        self.assertTrue(advices)
        self.assertTrue(
            any('财务模型' in item or '降本增效' in item for item in advices),
            msg='低段位特殊能力A级未命中 7-9段+ 建议'
        )

    def test_improvement_zone_returns_core_task_and_steps(self):
        action_data = self.generator.corpus['action']['执行力']
        advices = self.generator._get_action_advice(
            action_data=action_data,
            rank='三段',
            ability_name='执行力',
            grade='E',
            advantage=False
        )
        self.assertTrue(advices)
        self.assertTrue(any(item.startswith('核心任务：') for item in advices))
        self.assertTrue(any('核对清单' in item for item in advices))

    def test_rank_boundary_handles_float_precision(self):
        # 历史回归：55.1 因浮点误差变成 55.099999999999994 时不能误判为一段
        self.assertEqual(self.generator.get_rank(55.099999999999994), '六段')


if __name__ == '__main__':
    unittest.main()
