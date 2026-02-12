const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');

// 拖拽事件处理
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (fileInput.files.length > 0) {
        handleFile(fileInput.files[0]);
    }
});

function handleFile(file) {
    // 检查文件类型
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
        showError('请上传Excel文件 (.xlsx 或 .xls)');
        return;
    }

    // 显示进度
    document.querySelector('.upload-area').classList.add('hidden');
    document.getElementById('progress-container').classList.remove('hidden');

    // 上传文件
    const formData = new FormData();
    formData.append('file', file);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError(data.error);
            } else {
                showResult(data);
            }
        })
        .catch(error => {
            showError('上传失败: ' + error.message);
        });
}

function showResult(data) {
    document.getElementById('progress-container').classList.add('hidden');
    const resultContainer = document.getElementById('result-container');
    resultContainer.classList.remove('hidden');

    document.getElementById('file-count').textContent = data.files.length;

    const filesList = document.getElementById('files-list');
    filesList.innerHTML = '';

    data.files.forEach(file => {
        const item = document.createElement('div');
        item.className = 'file-item';
        item.innerHTML = `
            <span>📄 ${file.name}</span>
            <a href="${file.url}" class="download-link" download>下载 PDF</a>
        `;
        filesList.appendChild(item);
    });
}

function showError(message) {
    document.querySelector('.upload-area').classList.add('hidden');
    document.getElementById('progress-container').classList.add('hidden');
    document.getElementById('result-container').classList.add('hidden');

    const errorContainer = document.getElementById('error-container');
    errorContainer.classList.remove('hidden');
    document.getElementById('error-message').textContent = message;
}

function resetUpload() {
    document.querySelector('.upload-area').classList.remove('hidden');
    document.getElementById('progress-container').classList.add('hidden');
    document.getElementById('result-container').classList.add('hidden');
    document.getElementById('error-container').classList.add('hidden');
    fileInput.value = '';
}
