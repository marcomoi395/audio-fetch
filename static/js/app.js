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

// Cookie UI elements
const addCookiesBtn = document.getElementById('add-cookies-btn');
const cookiesContainer = document.getElementById('cookies-container');
const cookiesTextarea = document.getElementById('youtube-cookies');
const persistCheckbox = document.getElementById('persist-cookies-checkbox');
const saveCookiesBtn = document.getElementById('save-cookies-btn');
const clearCookiesBtn = document.getElementById('clear-cookies-btn');
const cancelCookiesBtn = document.getElementById('cancel-cookies-btn');
const cookieStatusMsg = document.getElementById('cookie-status-message');
const cookieStatusIndicator = document.getElementById('cookie-status-indicator');
const cookieSecurityDialog = document.getElementById('cookie-security-dialog');


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

// Cookie UI Functions
function showCookieInput() {
    cookiesContainer.style.display = 'block';
    addCookiesBtn.textContent = '🍪 Hide cookie input';
}

function hideCookieInput() {
    cookiesContainer.style.display = 'none';
    addCookiesBtn.textContent = '🍪 Add Cookies (Required)';
}

function toggleCookieInput() {
    if (cookiesContainer.style.display === 'none' || !cookiesContainer.style.display) {
        showCookieInput();
    } else {
        hideCookieInput();
    }
}

function updateCookieStatus(message, isError = false) {
    cookieStatusMsg.style.display = 'block';
    cookieStatusMsg.textContent = message;
    cookieStatusMsg.className = isError ? 'nes-text is-error' : 'nes-text is-success';
    cookieStatusMsg.style.fontSize = '0.7rem';
    cookieStatusMsg.style.marginTop = '0.5rem';
}

function showCookieIndicator() {
    cookieStatusIndicator.style.display = 'block';
}

function hideCookieIndicator() {
    cookieStatusIndicator.style.display = 'none';
}

function initializeCookieUI() {
    if (CookieManager.hasStored()) {
        showCookieIndicator();
        updateCookieStatus('✓ Cookies loaded from storage');
    } else {
        hideCookieIndicator();
    }
    updateButtonStates();
}

function updateButtonStates() {
    const hasCookies = CookieManager.hasStored();
    fetchBtn.disabled = !hasCookies;
    downloadBtn.disabled = !hasCookies;
}


// API Functions
async function fetchVideoInfo(url, cookies = null) {
    try {
        const body = { url: url };
        if (cookies) {
            body.cookies = cookies;
        }
        
        const response = await fetch('/api/video-info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to fetch video info');
        }
        
        return await response.json();
    } catch (error) {
        throw error;
    }
}

async function downloadAudio(url, format, quality, cookies = null) {
    try {
        const body = {
            url: url,
            format: format,
            quality: quality
        };
        if (cookies) {
            body.cookies = cookies;
        }
        
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
        let filename = 'audio';
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="([^"]+)"/);
            if (filenameMatch) {
                filename = filenameMatch[1];
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
    
    // Get cookies from storage if available
    const cookies = CookieManager.get();

    // Validate cookies are present
    if (!cookies) {
        soundEffects.play('error');
        showError('YouTube cookies required. Please add cookies before fetching.');
        return;
    }
    
    soundEffects.play('fetch');
    showLoading();
    
    try {
        const info = await fetchVideoInfo(url, cookies);
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
        showError(error.message);
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
        // Get cookies from storage if available
        const cookies = CookieManager.get();

        // Validate cookies are present
        if (!cookies) {
            downloadBtn.disabled = false;
            downloadBtn.textContent = 'Download';
            soundEffects.play('error');
            showError('YouTube cookies required. Please add cookies before downloading.');
            return;
        }
        
        await downloadAudio(currentVideoUrl, format, quality, cookies);
        
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
        
        soundEffects.play('error');
        // Show error in modal or toast
        showError(error.message);
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

// Cookie UI event listeners
addCookiesBtn.addEventListener('click', toggleCookieInput);

saveCookiesBtn.addEventListener('click', () => {
    const cookies = cookiesTextarea.value.trim();
    const persist = persistCheckbox.checked;
    
    if (!cookies) {
        updateCookieStatus('Please enter cookies', true);
        return;
    }
    
    if (CookieManager.save(cookies, persist)) {
        updateCookieStatus(`✓ Cookies saved ${persist ? '(persistent)' : '(session only)'}`);
        showCookieIndicator();
        updateButtonStates();
    } else {
        updateCookieStatus('Failed to save cookies', true);
    }
});

clearCookiesBtn.addEventListener('click', () => {
    if (CookieManager.clear()) {
        cookiesTextarea.value = '';
        persistCheckbox.checked = false;
        updateCookieStatus('Cookies cleared');
        hideCookieIndicator();
        updateButtonStates();
    } else {
        updateCookieStatus('Failed to clear cookies', true);
    }
});

cancelCookiesBtn.addEventListener('click', () => {
    hideCookieInput();
});

// Allow Enter key to trigger fetch
urlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleFetchInfo();
    }
});

// Listen for storage changes (e.g., cookies cleared in another tab or by test)
window.addEventListener('storage', (e) => {
    if (e.key === 'youtube_cookies' || e.key === null) {
        updateButtonStates();
        if (CookieManager.hasStored()) {
            showCookieIndicator();
        } else {
            hideCookieIndicator();
        }
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    showInput();
    initializeCookieUI();
});
