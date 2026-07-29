// 8-bit Sound Effects Manager for Audio Fetch

/**
 * Sound effects manager for playing 8-bit audio on UI interactions
 * 
 * Required sound files (to be placed in static/sounds/):
 * - click.mp3 (or .wav) - UI button clicks
 * - fetch.mp3 - When starting video info fetch
 * - download.mp3 - When starting download
 * - success.mp3 - Successful completion
 * - error.mp3 - Error occurred
 * 
 * Recommended sources for free 8-bit sounds:
 * - Freesound.org (search "8-bit", "retro", "NES")
 * - OpenGameArt.org
 * - Bfxr.net (generate custom sounds)
 */

class SoundEffects {
    constructor() {
        this.sounds = {};
        this.enabled = true; // Enabled by default
        this.volume = 0.5; // Default volume (0.0 - 1.0)
        
        // Initialize sounds
        this.loadSounds();
        
        // Load settings from localStorage
        this.loadSettings();
    }
    
    /**
     * Load all sound files
     */
    loadSounds() {
        // Generate 8-bit sounds using Web Audio API (no files needed)
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        // Sound generators for each type - optimized for minimal latency
        this.soundGenerators = {
            click: () => this.generateBeep(800, 0.03),
            fetch: () => this.generateRiseBeep(400, 800, 0.1),
            download: () => this.generateFallBeep(1000, 400, 0.12),
            success: () => this.generateChord([523, 659, 784], 0.15),
            error: () => this.generateBuzz(200, 0.15)
        };
    }
    
    /**
     * Generate a simple beep sound - optimized version
     */
    generateBeep(frequency, duration) {
        const now = this.audioContext.currentTime;
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        oscillator.type = 'square'; // 8-bit style
        oscillator.frequency.value = frequency;
        
        // Fast attack, fast release
        gainNode.gain.setValueAtTime(this.volume * 0.3, now);
        gainNode.gain.exponentialRampToValueAtTime(0.01, now + duration);
        
        oscillator.start(now);
        oscillator.stop(now + duration);
    }
    
    /**
     * Generate a rising pitch beep - optimized version
     */
    generateRiseBeep(startFreq, endFreq, duration) {
        const now = this.audioContext.currentTime;
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        oscillator.type = 'square';
        oscillator.frequency.setValueAtTime(startFreq, now);
        oscillator.frequency.linearRampToValueAtTime(endFreq, now + duration);
        
        gainNode.gain.setValueAtTime(this.volume * 0.3, now);
        gainNode.gain.exponentialRampToValueAtTime(0.01, now + duration);
        
        oscillator.start(now);
        oscillator.stop(now + duration);
    }
    
    /**
     * Generate a falling pitch beep - optimized version
     */
    generateFallBeep(startFreq, endFreq, duration) {
        const now = this.audioContext.currentTime;
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        oscillator.type = 'square';
        oscillator.frequency.setValueAtTime(startFreq, now);
        oscillator.frequency.linearRampToValueAtTime(endFreq, now + duration);
        
        gainNode.gain.setValueAtTime(this.volume * 0.3, now);
        gainNode.gain.exponentialRampToValueAtTime(0.01, now + duration);
        
        oscillator.start(now);
        oscillator.stop(now + duration);
    }
    
    /**
     * Generate a chord (multiple frequencies) - optimized using AudioContext scheduling
     */
    generateChord(frequencies, duration) {
        const now = this.audioContext.currentTime;
        const staggerDelay = 0.03; // 30ms stagger instead of 50ms
        
        frequencies.forEach((freq, i) => {
            const startTime = now + (i * staggerDelay);
            const oscillator = this.audioContext.createOscillator();
            const gainNode = this.audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(this.audioContext.destination);
            
            oscillator.type = 'square';
            oscillator.frequency.value = freq;
            
            // Schedule gain envelope
            gainNode.gain.setValueAtTime(this.volume * 0.2, startTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + duration);
            
            // Schedule start and stop using AudioContext time
            oscillator.start(startTime);
            oscillator.stop(startTime + duration);
        });
    }
    
    /**
     * Generate a buzz sound for errors - optimized version
     */
    generateBuzz(frequency, duration) {
        const now = this.audioContext.currentTime;
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        oscillator.type = 'sawtooth';
        oscillator.frequency.value = frequency;
        
        gainNode.gain.setValueAtTime(this.volume * 0.3, now);
        gainNode.gain.exponentialRampToValueAtTime(0.01, now + duration);
        
        oscillator.start(now);
        oscillator.stop(now + duration);
    }
    
    /**
     * Play a sound effect
     * @param {string} name - Sound name (click, fetch, download, success, error)
     */
    play(name) {
        if (!this.enabled) {
            return;
        }
        
        const generator = this.soundGenerators[name];
        if (!generator) {
            console.warn(`Sound generator not found: ${name}`);
            return;
        }
        
        try {
            generator();
        } catch (err) {
            console.debug(`Could not play sound ${name}:`, err.message);
        }
    }
    
    /**
     * Set volume for all sounds
     * @param {number} vol - Volume level (0.0 - 1.0)
     */
    setVolume(vol) {
        this.volume = Math.max(0, Math.min(1, vol));
        
        // Update all loaded sounds
        for (const sound of Object.values(this.sounds)) {
            sound.volume = this.volume;
        }
        
        this.saveSettings();
    }
    
    /**
     * Enable sound effects
     */
    enable() {
        this.enabled = true;
        this.saveSettings();
    }
    
    /**
     * Disable sound effects
     */
    disable() {
        this.enabled = false;
        this.saveSettings();
    }
    
    /**
     * Toggle sound effects on/off
     * @returns {boolean} New enabled state
     */
    toggle() {
        this.enabled = !this.enabled;
        this.saveSettings();
        return this.enabled;
    }
    
    /**
     * Check if sounds are enabled
     * @returns {boolean}
     */
    isEnabled() {
        return this.enabled;
    }
    
    /**
     * Save settings to localStorage
     */
    saveSettings() {
        try {
            localStorage.setItem('audioFetch_soundEnabled', this.enabled.toString());
            localStorage.setItem('audioFetch_soundVolume', this.volume.toString());
        } catch (e) {
            // Ignore localStorage errors
        }
    }
    
    /**
     * Load settings from localStorage
     */
    loadSettings() {
        try {
            const enabled = localStorage.getItem('audioFetch_soundEnabled');
            if (enabled !== null) {
                this.enabled = enabled === 'true';
            }
            
            const volume = localStorage.getItem('audioFetch_soundVolume');
            if (volume !== null) {
                this.setVolume(parseFloat(volume));
            }
        } catch (e) {
            // Ignore localStorage errors
        }
    }
}

// Create global sound effects instance
const soundEffects = new SoundEffects();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = soundEffects;
}
