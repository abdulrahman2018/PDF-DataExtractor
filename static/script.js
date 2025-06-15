document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const fileList = document.getElementById('fileList');
    const processButton = document.getElementById('processButton');
    const downloadButton = document.getElementById('downloadButton');
    const progressSection = document.querySelector('.progress-section');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const notification = document.getElementById('notification');

    let selectedFiles = new Set();
    let isProcessing = false;

    // Drag and drop handlers
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
        const files = Array.from(e.dataTransfer.files).filter(file => file.type === 'application/pdf');
        handleFiles(files);
    });

    // File input handler
    fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        handleFiles(files);
        // Reset the input to allow selecting the same file again
        e.target.value = '';
    });

    // Process button handler
    processButton.addEventListener('click', async () => {
        if (selectedFiles.size === 0 || isProcessing) return;

        isProcessing = true;
        processButton.disabled = true;
        progressSection.style.display = 'block';
        progressBar.style.width = '0%';
        progressText.textContent = 'Preparing files...';

        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append('files', file);
        });

        try {
            const response = await fetch('/process', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || 'Processing failed');
            }

            if (result.success) {
                showNotification('Files processed successfully!', 'success');
                downloadButton.style.display = 'block';
                progressBar.style.width = '100%';
                progressText.textContent = 'Complete!';
                
                // Clear the file list after successful processing
                selectedFiles.clear();
                fileList.innerHTML = '';
                updateProcessButton();
            } else {
                throw new Error(result.error || 'Processing failed');
            }
        } catch (error) {
            showNotification(error.message, 'error');
            progressSection.style.display = 'none';
        } finally {
            isProcessing = false;
            processButton.disabled = false;
        }
    });

    // Download button handler
    downloadButton.addEventListener('click', async () => {
        try {
            downloadButton.disabled = true;
            const response = await fetch('/download');
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Download failed');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'extracted_data.xlsx';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showNotification('File downloaded successfully!', 'success');
        } catch (error) {
            showNotification(error.message, 'error');
        } finally {
            downloadButton.disabled = false;
        }
    });

    function handleFiles(files) {
        const validFiles = files.filter(file => {
            if (file.type !== 'application/pdf') {
                showNotification(`Skipped ${file.name}: Not a PDF file`, 'error');
                return false;
            }
            if (file.size > 16 * 1024 * 1024) { // 16MB
                showNotification(`Skipped ${file.name}: File too large (max 16MB)`, 'error');
                return false;
            }
            return true;
        });

        validFiles.forEach(file => {
            selectedFiles.add(file);
            addFileToList(file);
        });
        updateProcessButton();
    }

    function addFileToList(file) {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <div class="file-name">
                <img src="/static/pdf-icon.svg" alt="PDF">
                <span>${file.name}</span>
                <span class="file-size">(${(file.size / 1024 / 1024).toFixed(2)} MB)</span>
            </div>
            <span class="remove-file" data-filename="${file.name}">×</span>
        `;

        fileItem.querySelector('.remove-file').addEventListener('click', () => {
            selectedFiles.delete(file);
            fileItem.remove();
            updateProcessButton();
        });

        fileList.appendChild(fileItem);
    }

    function updateProcessButton() {
        processButton.disabled = selectedFiles.size === 0 || isProcessing;
    }

    function showNotification(message, type) {
        notification.textContent = message;
        notification.className = `notification ${type}`;
        
        // Clear any existing timeout
        if (notification.timeout) {
            clearTimeout(notification.timeout);
        }
        
        // Set new timeout
        notification.timeout = setTimeout(() => {
            notification.className = 'notification';
        }, 5000);
    }
}); 