from flask import Flask, render_template, request, send_from_directory, jsonify
import os
import re
import sys
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import pandas as pd
from werkzeug.utils import secure_filename

# 添加assessment-skill到路径以导入PDF生成器
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assessment-skill'))
from main import AssessmentReportGenerator

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_ROOT = BASE_DIR / 'uploads' / 'jobs'
OUTPUT_ROOT = BASE_DIR / 'outputs' / 'jobs'
MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH_MB', '16')) * 1024 * 1024
JOB_RETENTION_HOURS = int(os.getenv('JOB_RETENTION_HOURS', '24'))
MAX_KEPT_JOBS = int(os.getenv('MAX_KEPT_JOBS', '300'))

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
JOB_ID_PATTERN = re.compile(r'^[A-Za-z0-9_-]+$')
REQUIRED_COLUMNS = {
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
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def cleanup_old_jobs():
    """清理过期任务目录，并限制最大保留数量。"""
    expiry_ts = (datetime.now() - timedelta(hours=JOB_RETENTION_HOURS)).timestamp()

    for root in (UPLOAD_ROOT, OUTPUT_ROOT):
        job_dirs = [p for p in root.iterdir() if p.is_dir()]
        for job_dir in job_dirs:
            if job_dir.stat().st_mtime < expiry_ts:
                shutil.rmtree(job_dir, ignore_errors=True)

        kept = sorted(
            [p for p in root.iterdir() if p.is_dir()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for stale in kept[MAX_KEPT_JOBS:]:
            shutil.rmtree(stale, ignore_errors=True)


def check_excel_columns(excel_path):
    """仅读取表头，校验关键字段是否存在。"""
    columns = set(pd.read_excel(excel_path, nrows=0).columns)
    missing = sorted(REQUIRED_COLUMNS - columns)
    return missing


def make_job_id():
    return f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/healthz')
def healthz():
    return jsonify({
        'status': 'ok',
        'time': datetime.now().isoformat(timespec='seconds'),
    })


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件部分'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400

    if file and allowed_file(file.filename):
        cleanup_old_jobs()

        suffix = Path(file.filename).suffix.lower() or '.xlsx'
        filename = secure_filename(file.filename)
        if not filename:
            filename = f'upload{suffix}'

        job_id = make_job_id()
        upload_dir = UPLOAD_ROOT / job_id
        output_dir = OUTPUT_ROOT / job_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = upload_dir / filename
        file.save(filepath)

        try:
            missing_columns = check_excel_columns(filepath)
            if missing_columns:
                return jsonify({
                    'error': f'Excel缺少关键列: {", ".join(missing_columns)}'
                }), 400

            app.logger.info("job=%s 初始化生成器", job_id)
            generator = AssessmentReportGenerator()

            app.logger.info("job=%s 开始处理文件: %s", job_id, filepath)
            generated_files = generator.generate_report(str(filepath), str(output_dir))
            app.logger.info(
                "job=%s 生成完成, 文件数: %s",
                job_id,
                len(generated_files) if generated_files else 0,
            )

            if not generated_files:
                return jsonify({'error': '未能生成报告，请检查Excel文件格式'}), 500

            report_files = []
            for f in generated_files:
                output_name = os.path.basename(f)
                report_files.append({
                    'name': output_name,
                    'url': f'/download/{job_id}/{quote(output_name)}'
                })

            return jsonify({
                'message': '报告生成成功',
                'job_id': job_id,
                'files': report_files
            })

        except Exception as e:
            app.logger.exception("job=%s 处理失败: %s", job_id, str(e))
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': '不支持的文件类型'}), 400


@app.route('/preview_assets')
def preview_assets():
    return render_template('asset_preview.html')


@app.route('/download/<job_id>/<path:filename>')
def download_file(job_id, filename):
    if not JOB_ID_PATTERN.match(job_id):
        return jsonify({'error': '非法任务ID'}), 400

    output_dir = OUTPUT_ROOT / job_id
    if not output_dir.exists():
        return jsonify({'error': '任务不存在或已过期'}), 404

    file_path = output_dir / filename
    if not file_path.exists():
        return jsonify({'error': '文件不存在'}), 404

    return send_from_directory(output_dir, filename, as_attachment=True)


if __name__ == '__main__':
    host = os.getenv('APP_HOST', '0.0.0.0')
    port = int(os.getenv('APP_PORT', '5001'))
    debug = os.getenv('FLASK_DEBUG', '0') == '1'
    app.run(host=host, port=port, debug=debug, threaded=False)
