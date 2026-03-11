#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Flask 接口回归测试。"""

import io
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

import pandas as pd


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SKILL_DIR)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, SKILL_DIR)

import app as app_module  # noqa: E402


REQUIRED_COLUMNS = [
    '序号',
    '微信昵称',
    '【执行力】',
    '【协调力】',
    '【优化力】',
    '【统筹力】',
    '【预见力】',
    '【业务力】',
    '【财务力】',
    '【领导力】',
    '【决策力】',
]


class AppWorkflowTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix='app-test-'))
        self.upload_root = self.temp_dir / 'uploads'
        self.output_root = self.temp_dir / 'outputs'
        self.upload_root.mkdir(parents=True, exist_ok=True)
        self.output_root.mkdir(parents=True, exist_ok=True)

        self.original_upload_root = app_module.UPLOAD_ROOT
        self.original_output_root = app_module.OUTPUT_ROOT
        app_module.UPLOAD_ROOT = self.upload_root
        app_module.OUTPUT_ROOT = self.output_root
        app_module.JOBS.clear()

        self.client = app_module.app.test_client()

    def tearDown(self):
        app_module.JOBS.clear()
        app_module.UPLOAD_ROOT = self.original_upload_root
        app_module.OUTPUT_ROOT = self.original_output_root
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _make_excel(self, rows):
        excel_path = self.temp_dir / 'input.xlsx'
        pd.DataFrame(rows, columns=REQUIRED_COLUMNS).to_excel(excel_path, index=False)
        return excel_path

    def _post_excel(self, endpoint, excel_path):
        with excel_path.open('rb') as fp:
            return self.client.post(
                endpoint,
                data={'file': (io.BytesIO(fp.read()), 'BATCH.XLSX')},
                content_type='multipart/form-data',
            )

    def test_sync_upload_returns_partial_success_when_one_row_is_invalid(self):
        excel_path = self._make_excel([
            ['60001', '正常用户', 6.0, 6.0, 6.0, 7.0, 7.0, 7.0, 8.0, 8.0, 8.0],
            ['60002', '异常用户', 'abc', 6.0, 6.0, 7.0, 7.0, 7.0, 8.0, 8.0, 8.0],
        ])

        response = self._post_excel('/upload', excel_path)
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'partial_success')
        self.assertEqual(len(data['files']), 1)
        self.assertEqual(data['summary']['generated_count'], 1)
        self.assertEqual(data['summary']['failed_count'], 1)
        self.assertEqual(len(data['failed_items']), 1)

    def test_async_job_state_can_be_restored_from_disk(self):
        excel_path = self._make_excel([
            ['60011', '坏/名字', 6.0, 6.0, 6.0, 7.0, 7.0, 7.0, 8.0, 8.0, 8.0],
        ])

        response = self._post_excel('/jobs', excel_path)
        data = response.get_json()
        self.assertEqual(response.status_code, 202)
        job_id = data['job_id']

        terminal = None
        for _ in range(80):
            status_response = self.client.get(f'/jobs/{job_id}')
            status_data = status_response.get_json()
            if status_data['status'] in {'success', 'partial_success', 'failed'}:
                terminal = status_data
                break
            time.sleep(0.1)

        self.assertIsNotNone(terminal)
        self.assertEqual(terminal['status'], 'success')
        app_module.JOBS.clear()

        restored = self.client.get(f'/jobs/{job_id}')
        restored_data = restored.get_json()
        self.assertEqual(restored.status_code, 200)
        self.assertEqual(restored_data['status'], 'success')

        files_response = self.client.get(f'/jobs/{job_id}/files')
        files_data = files_response.get_json()
        self.assertEqual(files_response.status_code, 200)
        self.assertEqual(files_data['count'], 1)


if __name__ == '__main__':
    unittest.main()
