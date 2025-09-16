class YouTubeDownloader {
    constructor() {
        this.currentDownloadId = null;
        this.progressInterval = null;
        this.initializeElements();
        this.attachEventListeners();
    }

    initializeElements() {
        // Input elements
        this.urlInput = document.getElementById('urlInput');
        this.qualitySelect = document.getElementById('qualitySelect');
        this.downloadTypeRadios = document.querySelectorAll('input[name="downloadType"]');
        
        // Button elements
        this.getInfoBtn = document.getElementById('getInfoBtn');
        this.downloadBtn = document.getElementById('downloadBtn');
        this.downloadFileBtn = document.getElementById('downloadFileBtn');
        this.retryBtn = document.getElementById('retryBtn');
        
        // Section elements
        this.loadingSection = document.getElementById('loadingSection');
        this.videoInfoSection = document.getElementById('videoInfoSection');
        this.progressSection = document.getElementById('progressSection');
        this.errorSection = document.getElementById('errorSection');
        
        // Video info elements
        this.videoThumbnail = document.getElementById('videoThumbnail');
        this.videoTitle = document.getElementById('videoTitle');
        this.videoDuration = document.getElementById('videoDuration');
        this.videoChannel = document.getElementById('videoChannel');
        this.videoViews = document.getElementById('videoViews');
        
        // Progress elements
        this.progressFill = document.getElementById('progressFill');
        this.progressText = document.getElementById('progressText');
        this.downloadSpeed = document.getElementById('downloadSpeed');
        this.downloadSize = document.getElementById('downloadSize');
        this.downloadComplete = document.getElementById('downloadComplete');
        
        // Error elements
        this.errorMessage = document.getElementById('errorMessage');
    }

    attachEventListeners() {
        this.getInfoBtn.addEventListener('click', () => this.getVideoInfo());
        this.downloadBtn.addEventListener('click', () => this.startDownload());
        this.downloadFileBtn.addEventListener('click', () => this.downloadFile());
        this.retryBtn.addEventListener('click', () => this.resetForm());
        
        // Enter key support for URL input
        this.urlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.getVideoInfo();
            }
        });
        
        // Disable quality selector when audio-only is selected
        this.downloadTypeRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                const isAudioOnly = document.querySelector('input[name="downloadType"]:checked').value === 'audio';
                this.qualitySelect.disabled = isAudioOnly;
            });
        });
    }

    hideAllSections() {
        [this.loadingSection, this.videoInfoSection, this.progressSection, this.errorSection]
            .forEach(section => section.classList.add('hidden'));
    }

    showError(message) {
        this.hideAllSections();
        this.errorMessage.textContent = message;
        this.errorSection.classList.remove('hidden');
    }

    formatDuration(seconds) {
        if (!seconds) return 'N/A';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    }

    formatNumber(num) {
        if (!num) return '0';
        
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        } else {
            return num.toString();
        }
    }

    formatBytes(bytes) {
        if (!bytes) return '0 B';
        
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return (bytes / Math.pow(1024, i)).toFixed(2) + ' ' + sizes[i];
    }

    formatSpeed(speed) {
        if (!speed) return '0 B/s';
        return this.formatBytes(speed) + '/s';
    }

    async getVideoInfo() {
        const url = this.urlInput.value.trim();
        
        if (!url) {
            this.showError('Por favor ingresa una URL válida de YouTube');
            return;
        }
        
        // Show loading
        this.hideAllSections();
        this.loadingSection.classList.remove('hidden');
        this.getInfoBtn.disabled = true;
        
        try {
            const response = await fetch('/api/video-info', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Error al obtener información del video');
            }
            
            this.displayVideoInfo(data);
            
        } catch (error) {
            this.showError(error.message);
        } finally {
            this.getInfoBtn.disabled = false;
        }
    }

    displayVideoInfo(videoData) {
        this.hideAllSections();
        
        // Populate video information
        this.videoThumbnail.src = videoData.thumbnail || '';
        this.videoThumbnail.alt = videoData.title || 'Video Thumbnail';
        this.videoTitle.textContent = videoData.title || 'Sin título';
        this.videoDuration.textContent = this.formatDuration(videoData.duration);
        this.videoChannel.textContent = videoData.uploader || 'Desconocido';
        this.videoViews.textContent = this.formatNumber(videoData.view_count);
        
        // Show video info section
        this.videoInfoSection.classList.remove('hidden');
    }

    async startDownload() {
        const url = this.urlInput.value.trim();
        const quality = this.qualitySelect.value;
        const downloadType = document.querySelector('input[name="downloadType"]:checked').value;
        const audioOnly = downloadType === 'audio';
        
        if (!url) {
            this.showError('Por favor ingresa una URL válida');
            return;
        }
        
        // Show progress section
        this.hideAllSections();
        this.progressSection.classList.remove('hidden');
        this.downloadComplete.classList.add('hidden');
        
        // Reset progress
        this.progressFill.style.width = '0%';
        this.progressText.textContent = '0%';
        this.downloadSpeed.textContent = '';
        this.downloadSize.textContent = '';
        
        try {
            const response = await fetch('/api/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url,
                    quality,
                    audio_only: audioOnly
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Error al iniciar descarga');
            }
            
            this.currentDownloadId = data.download_id;
            this.startProgressPolling();
            
        } catch (error) {
            this.showError(error.message);
        }
    }

    startProgressPolling() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }
        
        this.progressInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/progress/${this.currentDownloadId}`);
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Error al obtener progreso');
                }
                
                this.updateProgress(data);
                
                if (data.status === 'completed' || data.status === 'error') {
                    clearInterval(this.progressInterval);
                    this.progressInterval = null;
                }
                
            } catch (error) {
                clearInterval(this.progressInterval);
                this.progressInterval = null;
                this.showError(error.message);
            }
        }, 1000); // Poll every second
    }

    updateProgress(progressData) {
        const { status, progress, speed, downloaded, total, error } = progressData;
        
        if (status === 'error') {
            this.showError(error || 'Error durante la descarga');
            return;
        }
        
        if (status === 'completed') {
            this.progressFill.style.width = '100%';
            this.progressText.textContent = '100%';
            this.downloadComplete.classList.remove('hidden');
            return;
        }
        
        if (status === 'downloading' && progress !== undefined) {
            this.progressFill.style.width = `${progress}%`;
            this.progressText.textContent = `${progress}%`;
            
            if (speed) {
                this.downloadSpeed.textContent = this.formatSpeed(speed);
            }
            
            if (downloaded && total) {
                this.downloadSize.textContent = `${this.formatBytes(downloaded)} / ${this.formatBytes(total)}`;
            }
        }
    }

    downloadFile() {
        if (this.currentDownloadId) {
            // Create a temporary link to download the file
            const link = document.createElement('a');
            link.href = `/api/download-file/${this.currentDownloadId}`;
            link.style.display = 'none';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }

    resetForm() {
        this.hideAllSections();
        this.urlInput.value = '';
        this.currentDownloadId = null;
        
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
        
        // Reset form elements
        this.qualitySelect.value = 'best';
        document.querySelector('input[name="downloadType"][value="video"]').checked = true;
        this.qualitySelect.disabled = false;
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new YouTubeDownloader();
});