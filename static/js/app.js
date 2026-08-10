// Main application logic for Audio Fetch

// Global state
let currentVideoUrl = '';
let currentVideoInfo = null;

// DOM Elements
const inputSection = document.getElementById('input-section');
const loadingSection = document.getElementById('loading-section');
const errorSection = document.getElementById('error-section');
const infoSection = document.getElementById('info-section');

const urlInput = document.getElementById('youtube-url');
const fetchBtn = document.getElementById('fetch-btn');
const retryBtn = document.getElementById('retry-btn');
const newUrlBtn = document.getElementById('new-url-btn');
const downloadBtn = document.getElementById('download-btn');

const errorMessage = document.getElementById('error-message');
const videoThumbnail = document.getElementById('video-thumbnail');
const videoTitle = document.getElementById('video-title');
const videoUploader = document.getElementById('video-uploader');
const videoDuration = document.getElementById('video-duration');

const formatSelect = document.getElementById('format-select');
const qualitySelect = document.getElementById('quality-select');



// UI State Management
function showSection(section) {
    inputSection.style.display = 'none';
    loadingSection.style.display = 'none';
    errorSection.style.display = 'none';
    infoSection.style.display = 'none';
    
    section.style.display = 'block';
}

function showError(error) {
    // Handle both string and object errors
    let message = 'An error occurred';
    
    if (typeof error === 'string') {
        message = error;
    } else if (error && error.message) {
        message = error.message;
    } else if (error && error.detail) {
        message = error.detail;
    }
    
    errorMessage.textContent = message;
    showSection(errorSection);
}

function showLoading() {
    showSection(loadingSection);
}

function showInput() {
    showSection(inputSection);
    urlInput.value = '';
    urlInput.focus();
}

function showVideoInfo() {
    showSection(infoSection);
}


function updateButtonStates() {
    // Buttons are always enabled
    fetchBtn.disabled = false;
    downloadBtn.disabled = false;
}


// API Functions
async function fetchVideoInfo(url) {
    try {
        const response = await fetch('/api/video-info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to fetch video info');
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching video info:', error);
        throw error;
    }
}

async function downloadAudio(url, format, quality) {
    try {
        const body = {
            url: url,
            format: format,
            quality: quality
        };

        const response = await fetch('/api/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Download failed');
        }
        
        // Get filename from Content-Disposition header
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'audio.mp3';
        
        if (contentDisposition) {
            // Try to get UTF-8 encoded filename first (RFC 5987)
            const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/);
            if (utf8Match) {
                filename = decodeURIComponent(utf8Match[1]);
            } else {
                // Fallback to regular filename parameter
                const asciiMatch = contentDisposition.match(/filename="([^"]+)"/);
                if (asciiMatch) {
                    filename = asciiMatch[1];
                }
            }
        }
        
        // Download file
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(downloadUrl);
        document.body.removeChild(a);
        
        return true;
    } catch (error) {
        throw error;
    }
}

// Event Handlers
async function handleFetchInfo() {
    soundEffects.play('click');
    const url = urlInput.value.trim();
    
    if (!url) {
        showError('Please enter a YouTube URL');
        return;
    }
    
    currentVideoUrl = url;
    soundEffects.play('fetch');
    showLoading();
    
    try {
        const info = await fetchVideoInfo(url);
        currentVideoInfo = info;
        
        // Display video info
        videoThumbnail.src = info.thumbnail_url;
        videoThumbnail.alt = info.title;
        videoTitle.textContent = info.title;
        videoUploader.textContent = info.uploader;
        videoDuration.textContent = formatDuration(info.duration);
        
        soundEffects.play('success');
        showVideoInfo();
    } catch (error) {
        soundEffects.play('error');
        // Show error message
        const errorMsg = error.message;
        showError(errorMsg);
    }
}

async function handleDownload() {
    soundEffects.play('click');
    const format = formatSelect.value;
    const quality = qualitySelect.value;
    
    if (!currentVideoUrl || !currentVideoInfo) {
        soundEffects.play('error');
        showError('Video info not found');
        return;
    }
    
    // Disable download button during download
    downloadBtn.disabled = true;
    downloadBtn.textContent = '⬇️ Downloading...';
    soundEffects.play('download');
    
    try {
        await downloadAudio(currentVideoUrl, format, quality);
        
        // Show success state briefly
        soundEffects.play('success');
        downloadBtn.textContent = '✅ Success!';
        setTimeout(() => {
            downloadBtn.textContent = 'Download';
            downloadBtn.disabled = false;
        }, 2000);
    } catch (error) {
        downloadBtn.textContent = 'Download';
        downloadBtn.disabled = false;
        
        // Show error message
        const errorMsg = error.message;
        showError(errorMsg);
    }
}

function handleNewUrl() {
    soundEffects.play('click');
    currentVideoUrl = '';
    currentVideoInfo = null;
    urlInput.value = '';
    showInput();
}

function handleRetry() {
    soundEffects.play('click');
    showInput();
}

// Helper Functions
function formatDuration(seconds) {
    if (!seconds || seconds === 0) {
        return 'Unknown';
    }
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
        return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
}


// Event Listeners
fetchBtn.addEventListener('click', handleFetchInfo);
retryBtn.addEventListener('click', handleRetry);
newUrlBtn.addEventListener('click', handleNewUrl);
downloadBtn.addEventListener('click', handleDownload);



// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    showInput();
});


// Window Control Functions
async function minimizeWindow() {
    try {
        await fetch('/api/window/minimize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
    } catch (error) {
        console.error('Failed to minimize window:', error);
    }
}
async function closeWindow() {
    try {
        // Add a small delay to ensure the UI registers the click
        await new Promise(resolve => setTimeout(resolve, 50));
        
        const response = await fetch('/api/window/close', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            // Ensure request completes
            keepalive: true,
        });
        
        if (!response.ok) {
            console.error('Failed to close window:', response.statusText);
        }
    } catch (error) {
        console.error('Failed to close window:', error);
        // Fallback: try to close via Qt if available
        if (window.qt && window.qt.webChannelTransport) {
            window.close();
        }
    }
}
// Window Drag Functionality
function setupWindowDrag() {
    const dragArea = document.getElementById('drag-area');
    if (!dragArea) return;

    let isDragging = false;

    dragArea.addEventListener('mousedown', (e) => {
        isDragging = true;
        e.preventDefault();
    });

    document.addEventListener('mouseup', () => {
        isDragging = false;
    });
}

// Initialize window controls
document.addEventListener('DOMContentLoaded', () => {
    // Setup window control buttons
    const minimizeBtn = document.getElementById('minimize-btn');
    const closeBtn = document.getElementById('close-btn');

    if (minimizeBtn) {
        minimizeBtn.addEventListener('click', minimizeWindow);
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', closeWindow);
    }

    // Setup window drag
    setupWindowDrag();
});
