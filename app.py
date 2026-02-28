from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from urllib.parse import quote
from uuid import uuid4
import os
import re
import shutil
import sys
import zipfile

import pandas as pd
from flask import Flask, jsonify, render_template, request, send_from_directory
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
JOB_WORKERS = int(os.getenv('JOB_WORKERS', '1'))

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

JOBS = {}
JOBS_LOCK = Lock()
JOB_EXECUTOR = ThreadPoolExecutor(max_workers=JOB_WORKERS)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def now_iso():
    return datetime.now().isoformat(timespec='seconds')


def make_job_id():
    return f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"


def check_excel_columns(excel_path):
    """仅读取表头，校验关键字段是否存在。"""
    columns = set(pd.read_excel(excel_path, nrows=0).columns)
    missing = sorted(REQUIRED_COLUMNS - columns)
    return missing


def build_report_files(job_id, generated_files):
    report_files = []
    for file_path in generated_files:
        output_name = os.path.basename(file_path)
        report_files.append({
            'name': output_name,
            'url': f'/download/{job_id}/{quote(output_name)}',
        })
    return report_files


def cleanup_old_jobs():
    """清理过期任务目录，并限制最大保留数量。"""
    expiry_ts = (datetime.now() - timedelta(hours=JOB_RETENTION_HOURS)).timestamp()
    removed_job_ids = set()

    for root in (UPLOAD_ROOT, OUTPUT_ROOT):
        job_dirs = [p for p in root.iterdir() if p.is_dir()]
        for job_dir in job_dirs:
            if job_dir.stat().st_mtime < expiry_ts:
                removed_job_ids.add(job_dir.name)
                shutil.rmtree(job_dir, ignore_errors=True)

        kept = sorted(
            [p for p in root.iterdir() if p.is_dir()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for stale in kept[MAX_KEPT_JOBS:]:
            removed_job_ids.add(stale.name)
            shutil.rmtree(stale, ignore_errors=True)

    if removed_job_ids:
        with JOBS_LOCK:
            for job_id in removed_job_ids:
                JOBS.pop(job_id, None)


def save_upload_to_job_dirs(file_storage):
    suffix = Path(file_storage.filename).suffix.lower() or '.xlsx'
    filename = secure_filename(file_storage.filename)
    if not filename:
        filename = f'upload{suffix}'

    job_id = make_job_id()
    upload_dir = UPLOAD_ROOT / job_id
    output_dir = OUTPUT_ROOT / job_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    excel_path = upload_dir / filename
    file_storage.save(excel_path)
    return job_id, excel_path, output_dir


def init_job_state(job_id, excel_path, output_dir):
    with JOBS_LOCK:
        JOBS[job_id] = {
            'job_id': job_id,
            'status': 'queued',
            'message': '任务已创建，等待执行。',
            'error': None,
            'excel_path': str(excel_path),
            'output_dir': str(output_dir),
            'created_at': now_iso(),
            'started_at': None,
            'finished_at': None,
            'progress': {
                'total': 0,
                'completed': 0,
                'percent': 0.0,
                'current_index': 0,
                'current_seq': '',
                'current_name': '',
            },
            'files': [],
            'zip_name': None,
        }


def update_job_state(job_id, **updates):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job:
            return None
        job.update(updates)
        return job


def update_job_progress(job_id, payload):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job:
            return

        progress = job['progress']
        for key in ('total', 'completed', 'percent', 'current_index', 'current_seq', 'current_name'):
            if key in payload and payload[key] is not None:
                progress[key] = payload[key]

        event = payload.get('event', '')
        if event == 'started':
            job['message'] = '正在初始化生成器...'
        elif event == 'item_started':
            progress['percent'] = round(
                (progress['completed'] * 100.0 / progress['total']) if progress['total'] else 0.0, 2
            )
            job['message'] = f"正在生成第 {progress['current_index']}/{progress['total']} 份报告..."
        elif event == 'item_completed':
            job['message'] = (
                f"已完成 {progress['completed']}/{progress['total']}，"
                f"当前：NLZ100{progress['current_seq']} {progress['current_name']}"
            )
        elif event == 'completed':
            job['message'] = f"生成完成，共 {progress['completed']} 份报告。"


def serialize_job_state(job):
    return {
        'job_id': job['job_id'],
        'status': job['status'],
        'message': job['message'],
        'error': job['error'],
        'created_at': job['created_at'],
        'started_at': job['started_at'],
        'finished_at': job['finished_at'],
        'progress': job['progress'],
    }


def run_generation_job(job_id, excel_path, output_dir):
    update_job_state(
        job_id,
        status='running',
        message='任务开始执行...',
        started_at=now_iso(),
        error=None,
    )

    try:
        generator = AssessmentReportGenerator()
        generated_files = generator.generate_report(
            str(excel_path),
            str(output_dir),
            progress_callback=lambda payload: update_job_progress(job_id, payload),
        )

        if not generated_files:
            raise RuntimeError('未能生成报告，请检查Excel文件格式。')

        report_files = build_report_files(job_id, generated_files)
        update_job_state(
            job_id,
            status='success',
            message=f'报告生成成功，共 {len(report_files)} 份。',
            finished_at=now_iso(),
            files=report_files,
        )
    except Exception as exc:
        app.logger.exception("job=%s 处理失败: %s", job_id, exc)
        update_job_state(
            job_id,
            status='failed',
            message='任务执行失败，请查看错误信息。',
            error=str(exc),
            finished_at=now_iso(),
        )


def get_valid_job(job_id):
    if not JOB_ID_PATTERN.match(job_id):
        return None, (jsonify({'error': '非法任务ID'}), 400)

    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if not job:
        return None, (jsonify({'error': '任务不存在或已过期'}), 404)
    return job, None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/healthz')
def healthz():
    return jsonify({
        'status': 'ok',
        'time': now_iso(),
    })


@app.route('/jobs', methods=['POST'])
def create_job():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件部分'}), 400

    file_storage = request.files['file']
    if file_storage.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    if not allowed_file(file_storage.filename):
        return jsonify({'error': '不支持的文件类型'}), 400

    cleanup_old_jobs()
    job_id, excel_path, output_dir = save_upload_to_job_dirs(file_storage)

    try:
        missing_columns = check_excel_columns(excel_path)
        if missing_columns:
            shutil.rmtree(excel_path.parent, ignore_errors=True)
            shutil.rmtree(output_dir, ignore_errors=True)
            return jsonify({'error': f'Excel缺少关键列: {", ".join(missing_columns)}'}), 400
    except Exception as exc:
        shutil.rmtree(excel_path.parent, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)
        return jsonify({'error': f'Excel解析失败: {exc}'}), 400

    init_job_state(job_id, excel_path, output_dir)
    JOB_EXECUTOR.submit(run_generation_job, job_id, excel_path, output_dir)

    return jsonify({
        'job_id': job_id,
        'status': 'queued',
        'created_at': now_iso(),
        'poll_url': f'/jobs/{job_id}',
        'files_url': f'/jobs/{job_id}/files',
        'zip_url': f'/jobs/{job_id}/archive',
    }), 202


@app.route('/jobs/<job_id>')
def get_job_status(job_id):
    job, err = get_valid_job(job_id)
    if err:
        return err
    return jsonify(serialize_job_state(job))


@app.route('/jobs/<job_id>/files')
def get_job_files(job_id):
    job, err = get_valid_job(job_id)
    if err:
        return err

    status = job['status']
    if status == 'success':
        return jsonify({
            'job_id': job_id,
            'count': len(job['files']),
            'files': job['files'],
        })
    if status == 'failed':
        return jsonify({
            'error': job['error'] or '任务失败',
            'status': status,
        }), 409

    return jsonify({
        'error': '任务尚未完成',
        'status': status,
    }), 409


@app.route('/jobs/<job_id>/archive')
def download_job_archive(job_id):
    job, err = get_valid_job(job_id)
    if err:
        return err

    if job['status'] != 'success':
        return jsonify({'error': '任务尚未完成，无法打包下载'}), 409

    output_dir = Path(job['output_dir'])
    if not output_dir.exists():
        return jsonify({'error': '输出目录不存在或已过期'}), 404

    zip_name = job.get('zip_name') or f'{job_id}-reports.zip'
    zip_path = output_dir / zip_name

    if not zip_path.exists():
        pdf_files = sorted(output_dir.glob('*.pdf'))
        if not pdf_files:
            return jsonify({'error': '未找到可打包的PDF文件'}), 404
        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zip_file:
            for pdf_path in pdf_files:
                zip_file.write(pdf_path, arcname=pdf_path.name)
        update_job_state(job_id, zip_name=zip_name)

    return send_from_directory(str(output_dir), zip_name, as_attachment=True)


@app.route('/upload', methods=['POST'])
def upload_file():
    """兼容旧前端的同步接口。"""
    if 'file' not in request.files:
        return jsonify({'error': '没有文件部分'}), 400

    file_storage = request.files['file']
    if file_storage.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    if not allowed_file(file_storage.filename):
        return jsonify({'error': '不支持的文件类型'}), 400

    cleanup_old_jobs()
    job_id, excel_path, output_dir = save_upload_to_job_dirs(file_storage)

    try:
        missing_columns = check_excel_columns(excel_path)
        if missing_columns:
            shutil.rmtree(excel_path.parent, ignore_errors=True)
            shutil.rmtree(output_dir, ignore_errors=True)
            return jsonify({'error': f'Excel缺少关键列: {", ".join(missing_columns)}'}), 400

        app.logger.info("job=%s 初始化生成器", job_id)
        generator = AssessmentReportGenerator()
        generated_files = generator.generate_report(str(excel_path), str(output_dir))
        app.logger.info(
            "job=%s 生成完成, 文件数: %s",
            job_id,
            len(generated_files) if generated_files else 0,
        )

        if not generated_files:
            return jsonify({'error': '未能生成报告，请检查Excel文件格式'}), 500

        return jsonify({
            'message': '报告生成成功',
            'job_id': job_id,
            'files': build_report_files(job_id, generated_files),
        })
    except Exception as exc:
        app.logger.exception("job=%s 处理失败: %s", job_id, exc)
        shutil.rmtree(excel_path.parent, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)
        return jsonify({'error': str(exc)}), 500


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

    return send_from_directory(str(output_dir), filename, as_attachment=True)


if __name__ == '__main__':
    host = os.getenv('APP_HOST', '0.0.0.0')
    port = int(os.getenv('APP_PORT', '5001'))
    debug = os.getenv('FLASK_DEBUG', '0') == '1'
    app.run(host=host, port=port, debug=debug, threaded=False)
