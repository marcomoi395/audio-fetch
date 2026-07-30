/**
 * Cookie Manager Utility
 * Handles browser storage, retrieval, validation, and clearing of YouTube cookies.
 */

class CookieManager {
    static STORAGE_KEY = 'youtube_cookies';

    /**
     * Save cookies to browser storage
     * @param {string} cookies - Netscape format cookie text
     * @param {boolean} persist - If true, use localStorage; if false, use sessionStorage
     * @returns {boolean} Success status
     */
    static save(cookies, persist = false) {
        if (!cookies || typeof cookies !== 'string') {
            console.error('CookieManager.save: Invalid cookies value');
            return false;
        }

        try {
            const storage = persist ? localStorage : sessionStorage;
            storage.setItem(this.STORAGE_KEY, cookies);
            
            // Clear from the other storage to avoid conflicts
            const otherStorage = persist ? sessionStorage : localStorage;
            otherStorage.removeItem(this.STORAGE_KEY);
            
            console.log(`Cookies saved to ${persist ? 'localStorage' : 'sessionStorage'}`);
            return true;
        } catch (error) {
            console.error('CookieManager.save: Storage error', error);
            return false;
        }
    }

    /**
     * Retrieve cookies from browser storage
     * Checks sessionStorage first, then localStorage
     * @returns {string|null} Cookie text or null if not found
     */
    static get() {
        try {
            // Check sessionStorage first (temporary)
            const sessionCookies = sessionStorage.getItem(this.STORAGE_KEY);
            if (sessionCookies) {
                return sessionCookies;
            }

            // Fall back to localStorage (persistent)
            const localCookies = localStorage.getItem(this.STORAGE_KEY);
            if (localCookies) {
                return localCookies;
            }

            return null;
        } catch (error) {
            console.error('CookieManager.get: Storage error', error);
            return null;
        }
    }

    /**
     * Clear cookies from all browser storage
     * @returns {boolean} Success status
     */
    static clear() {
        try {
            sessionStorage.removeItem(this.STORAGE_KEY);
            localStorage.removeItem(this.STORAGE_KEY);
            console.log('Cookies cleared from storage');
            return true;
        } catch (error) {
            console.error('CookieManager.clear: Storage error', error);
            return false;
        }
    }

    /**
     * Check if cookies are currently stored
     * @returns {boolean} True if cookies exist in storage
     */
    static hasStored() {
        try {
            return !!(sessionStorage.getItem(this.STORAGE_KEY) || localStorage.getItem(this.STORAGE_KEY));
        } catch (error) {
            console.error('CookieManager.hasStored: Storage error', error);
            return false;
        }
    }

    /**
     * Basic validation for Netscape cookie format
     * Checks for header and basic structure
     * @param {string} cookieText - Cookie text to validate
     * @returns {boolean} True if appears to be valid Netscape format
     */
    static isValidNetscapeFormat(cookieText) {
        if (!cookieText || typeof cookieText !== 'string') {
            return false;
        }

        const trimmed = cookieText.trim();
        
        // Empty string is not valid
        if (trimmed.length === 0) {
            return false;
        }

        // Check for Netscape header (optional but common)
        const hasHeader = trimmed.startsWith('# Netscape HTTP Cookie File') || 
                         trimmed.startsWith('# HTTP Cookie File');

        // Check for tab-separated cookie lines (domain, flag, path, secure, expiration, name, value)
        const lines = trimmed.split('\n');
        let hasCookieLine = false;

        for (const line of lines) {
            // Skip comments and empty lines
            if (line.startsWith('#') || line.trim() === '') {
                continue;
            }

            // Check if line has tab separators (Netscape format uses tabs)
            const parts = line.split('\t');
            if (parts.length >= 6) {
                hasCookieLine = true;
                break;
            }
        }

        // Valid if it has header OR has at least one cookie line
        return hasHeader || hasCookieLine;
    }
}
