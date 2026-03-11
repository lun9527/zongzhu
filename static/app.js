const POLL_INTERVAL_MS = 1000;
const MAX_POLL_ERROR_RETRIES = 5;
const REQUEST_TIMEOUT_MS = 30000;

const elements = {
    stateUpload: document.getElementById('state-upload'),
    stateRunning: document.getElementById('state-running'),
    stateResult: document.getElementById('state-result'),
    stateError: document.getElementById('state-error'),
    dropZone: document.getElementById('drop-zone'),
    fileInput: document.getElementById('file-input'),
    selectedFile: document.getElementById('selected-file'),
    pickFileBtn: document.getElementById('pick-file-btn'),
    statusText: document.getElementById('status-text'),
    progressFill: document.getElementById('progress-fill'),
    statJobId: document.getElementById('stat-job-id'),
    statProgress: document.getElementById('stat-progress'),
    statPercent: document.getElementById('stat-percent'),
    statCurrent: document.getElementById('stat-current'),
    resultSummary: document.getElementById('result-summary'),
    resultNotice: document.getElementById('result-notice'),
    filesTbody: document.getElementById('files-tbody'),
    searchInput: document.getElementById('file-search-input'),
    zipDownloadBtn: document.getElementById('zip-download-btn'),
    newTaskBtn: document.getElementById('new-task-btn'),
    retryBtn: document.getElementById('retry-btn'),
    cancelViewBtn: document.getElementById('cancel-view-btn'),
    errorMessage: document.getElementById('error-message'),
};

const appState = {
    jobId: null,
    files: [],
    zipUrl: null,
    summary: null,
    failedItems: [],
    pollTimer: null,
    isRunning: false,
    pollErrorCount: 0,
};

function setSection(section) {
    elements.stateUpload.classList.add('hidden');
    elements.stateRunning.classList.add('hidden');
    elements.stateResult.classList.add('hidden');
    elements.stateError.classList.add('hidden');

    if (section === 'upload') elements.stateUpload.classList.remove('hidden');
    if (section === 'running') elements.stateRunning.classList.remove('hidden');
    if (section === 'result') elements.stateResult.classList.remove('hidden');
    if (section === 'error') elements.stateError.classList.remove('hidden');
}

function resetToUpload() {
    stopPolling();
    appState.jobId = null;
    appState.files = [];
    appState.zipUrl = null;
    appState.summary = null;
    appState.failedItems = [];
    appState.isRunning = false;
    appState.pollErrorCount = 0;
    window.onbeforeunload = null;
    elements.fileInput.value = '';
    elements.selectedFile.classList.add('hidden');
    elements.selectedFile.textContent = '';
    elements.searchInput.value = '';
    elements.filesTbody.innerHTML = '';
    elements.resultNotice.classList.add('hidden');
    elements.resultNotice.innerHTML = '';
    setSection('upload');
}

function stopPolling() {
    if (!appState.pollTimer) return;
    clearInterval(appState.pollTimer);
    appState.pollTimer = null;
}

async function fetchJson(url, options = {}) {
    let response;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
    try {
        response = await fetch(url, {
            ...options,
            signal: controller.signal,
        });
    } catch (error) {
        if (error?.name === 'AbortError') {
            throw new Error('请求超时，请稍后重试');
        }
        throw new Error(`无法连接服务端（${window.location.origin}）`);
    } finally {
        clearTimeout(timeoutId);
    }
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(data.error || `请求失败（${response.status}）`);
    }
    return data;
}

function isExcelFile(fileName) {
    return /\.(xlsx|xls)$/i.test(fileName);
}

function renderResultNotice() {
    const summary = appState.summary || {};
    const failedItems = appState.failedItems || [];
    const failedCount = Number(summary.failed_count || 0);

    if (!failedCount) {
        elements.resultNotice.classList.add('hidden');
        elements.resultNotice.innerHTML = '';
        return;
    }

    const preview = failedItems.slice(0, 3).map((item) => {
        const seq = item.seq_no ? `NLZ100${item.seq_no}` : `第${item.index}行`;
        const name = item.nickname ? ` ${item.nickname}` : '';
        return `${seq}${name}：${item.error}`;
    });

    const title = document.createElement('strong');
    title.textContent = '本次批量生成存在失败项';

    const detail = document.createElement('p');
    detail.textContent = `成功 ${summary.generated_count || 0} 份，失败 ${failedCount} 份。${preview.join('；')}`;

    elements.resultNotice.innerHTML = '';
    elements.resultNotice.appendChild(title);
    elements.resultNotice.appendChild(detail);
    elements.resultNotice.classList.remove('hidden');
}

function updateRunningView(job) {
    const progress = job.progress || {};
    const total = Number(progress.total || 0);
    const completed = Number(progress.completed || 0);
    const percent = Number(progress.percent || 0);
    const currentSeq = progress.current_seq || '';
    const currentName = progress.current_name || '';

    elements.statusText.textContent = job.message || '任务执行中...';
    elements.statJobId.textContent = job.job_id || '-';
    elements.statProgress.textContent = `${completed} / ${total}`;
    elements.statPercent.textContent = `${percent.toFixed(1)}%`;
    elements.statCurrent.textContent = currentSeq ? `NLZ100${currentSeq} ${currentName}` : '-';
    elements.progressFill.style.width = `${Math.max(0, Math.min(percent, 100))}%`;
}

function renderFiles() {
    const keyword = elements.searchInput.value.trim().toLowerCase();
    const visibleFiles = keyword
        ? appState.files.filter((file) => file.name.toLowerCase().includes(keyword))
        : appState.files;

    elements.filesTbody.innerHTML = '';
    if (!visibleFiles.length) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="2" class="empty-row">未找到匹配文件</td>';
        elements.filesTbody.appendChild(row);
        return;
    }

    visibleFiles.forEach((file) => {
        const row = document.createElement('tr');

        const nameCell = document.createElement('td');
        nameCell.title = file.name;
        nameCell.textContent = file.name;

        const actionCell = document.createElement('td');
        actionCell.className = 'col-action';
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn-link-download';
        btn.textContent = '下载 PDF';
        btn.addEventListener('click', async () => {
            try {
                await downloadBlob(file.url, file.name);
            } catch (error) {
                alert(`下载失败：${error.message}`);
            }
        });

        actionCell.appendChild(btn);
        row.appendChild(nameCell);
        row.appendChild(actionCell);
        elements.filesTbody.appendChild(row);
    });
}

async function downloadBlob(url, fileName) {
    let response;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
    try {
        response = await fetch(url, { signal: controller.signal });
    } catch (error) {
        if (error?.name === 'AbortError') {
            throw new Error('下载超时，请稍后重试');
        }
        throw new Error(`无法连接服务端（${window.location.origin}）`);
    } finally {
        clearTimeout(timeoutId);
    }
    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.error || `下载失败（${response.status}）`);
    }
    const blob = await response.blob();
    const blobUrl = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(blobUrl);
}

function showError(message) {
    appState.isRunning = false;
    window.onbeforeunload = null;
    stopPolling();
    elements.errorMessage.textContent = message;
    setSection('error');
}

async function loadJobFiles(jobId) {
    const data = await fetchJson(`/jobs/${jobId}/files`);
    appState.files = data.files || [];
    appState.zipUrl = `/jobs/${jobId}/archive`;
    appState.summary = data.summary || null;
    appState.failedItems = data.failed_items || [];
    const failedCount = Number((appState.summary || {}).failed_count || 0);
    elements.resultSummary.textContent = failedCount
        ? `成功生成 ${data.count} 份报告，失败 ${failedCount} 份`
        : `共生成 ${data.count} 份报告`;
    renderResultNotice();
    renderFiles();
    setSection('result');
}

async function pollJobStatus(jobId) {
    try {
        const job = await fetchJson(`/jobs/${jobId}`);
        appState.pollErrorCount = 0;
        updateRunningView(job);

        if (job.status === 'success' || job.status === 'partial_success') {
            stopPolling();
            appState.isRunning = false;
            window.onbeforeunload = null;
            await loadJobFiles(jobId);
            return;
        }

        if (job.status === 'failed') {
            throw new Error(job.error || '任务执行失败');
        }
    } catch (error) {
        appState.pollErrorCount += 1;
        if (appState.pollErrorCount >= MAX_POLL_ERROR_RETRIES) {
            showError(error.message);
            return;
        }
        elements.statusText.textContent = `连接异常，正在重试（${appState.pollErrorCount}/${MAX_POLL_ERROR_RETRIES}）...`;
    }
}

function startPolling(jobId) {
    stopPolling();
    appState.pollErrorCount = 0;
    pollJobStatus(jobId);
    appState.pollTimer = setInterval(() => pollJobStatus(jobId), POLL_INTERVAL_MS);
}

async function createJob(file) {
    if (!isExcelFile(file.name)) {
        showError('请上传 Excel 文件（.xlsx / .xls）');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        await fetchJson('/healthz');
    } catch (error) {
        showError(`服务不可用：${error.message}`);
        return;
    }

    setSection('running');
    elements.statusText.textContent = '文件上传中...';
    elements.progressFill.style.width = '0%';

    try {
        const data = await fetchJson('/jobs', {
            method: 'POST',
            body: formData,
        });
        appState.jobId = data.job_id;
        appState.isRunning = true;
        window.onbeforeunload = () => '任务仍在执行，离开页面后将无法继续查看该任务进度。';
        startPolling(data.job_id);
    } catch (error) {
        showError(error.message);
    }
}

function bindEvents() {
    elements.pickFileBtn.addEventListener('click', () => elements.fileInput.click());

    elements.fileInput.addEventListener('change', () => {
        const file = elements.fileInput.files[0];
        if (!file) return;
        elements.selectedFile.classList.remove('hidden');
        elements.selectedFile.textContent = `已选择：${file.name}`;
        createJob(file);
    });

    elements.dropZone.addEventListener('click', (event) => {
        if (event.target.id === 'pick-file-btn') return;
        elements.fileInput.click();
    });

    elements.dropZone.addEventListener('dragover', (event) => {
        event.preventDefault();
        elements.dropZone.classList.add('dragover');
    });

    elements.dropZone.addEventListener('dragleave', () => {
        elements.dropZone.classList.remove('dragover');
    });

    elements.dropZone.addEventListener('drop', (event) => {
        event.preventDefault();
        elements.dropZone.classList.remove('dragover');
        const file = event.dataTransfer.files[0];
        if (!file) return;
        elements.selectedFile.classList.remove('hidden');
        elements.selectedFile.textContent = `已选择：${file.name}`;
        createJob(file);
    });

    elements.searchInput.addEventListener('input', renderFiles);

    elements.zipDownloadBtn.addEventListener('click', () => {
        if (!appState.zipUrl || !appState.jobId) return;
        downloadBlob(appState.zipUrl, `${appState.jobId}-reports.zip`).catch((error) => {
            alert(`ZIP 下载失败：${error.message}`);
        });
    });

    elements.newTaskBtn.addEventListener('click', resetToUpload);
    elements.retryBtn.addEventListener('click', resetToUpload);
    elements.cancelViewBtn.addEventListener('click', resetToUpload);
}

bindEvents();
