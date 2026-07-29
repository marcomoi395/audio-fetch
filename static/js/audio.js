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
        this.enabled = true;
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
        const soundFiles = {
            click: '/static/sounds/click.mp3',
            fetch: '/static/sounds/fetch.mp3',
            download: '/static/sounds/download.mp3',
            success: '/static/sounds/success.mp3',
            error: '/static/sounds/error.mp3'
        };
        
        for (const [name, path] of Object.entries(soundFiles)) {
            const audio = new Audio(path);
            audio.volume = this.volume;
            
            // Preload audio
            audio.preload = 'auto';
            
            // Handle loading errors gracefully
            audio.addEventListener('error', () => {
                console.warn(`Failed to load sound: ${name} from ${path}`);
            });
            
            this.sounds[name] = audio;
        }
    }
    
    /**
     * Play a sound effect
     * @param {string} name - Sound name (click, fetch, download, success, error)
     */
    play(name) {
        if (!this.enabled) {
            return;
        }
        
        const sound = this.sounds[name];
        if (!sound) {
            console.warn(`Sound not found: ${name}`);
            return;
        }
        
        // Clone the audio to allow overlapping plays
        const clone = sound.cloneNode();
        clone.volume = this.volume;
        
        // Play and clean up
        clone.play().catch(err => {
            // Ignore errors (e.g., autoplay policy)
            console.debug(`Could not play sound ${name}:`, err.message);
        });
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
