# Sound Effects for Audio Fetch

This directory contains 8-bit sound effects for UI interactions.

## Required Sound Files

Place the following sound files in this directory:

1. **click.mp3** - Button click sound (short, subtle)
2. **fetch.mp3** - Video info fetch start sound
3. **download.mp3** - Download start sound
4. **success.mp3** - Success completion sound
5. **error.mp3** - Error occurred sound

## Recommended Sources

### Free 8-bit Sound Resources:
- **Freesound.org** - Search for "8-bit", "retro", "NES", "chiptune"
  - Filter by Creative Commons licenses
  - Download as MP3 or WAV
  
- **OpenGameArt.org** - Retro game sound effects
  - Section: Sound Effects > UI
  - Look for NES/retro collections

- **Bfxr.net** - Generate custom 8-bit sounds
  - Browser-based sound generator
  - Export as WAV, convert to MP3 if needed
  - Presets: Pickup/Coin, Powerup, Hit/Hurt, Jump, Blip/Select

## File Format
- **Preferred**: MP3 (better browser support)
- **Alternative**: WAV (larger files)
- **Duration**: 0.1 - 0.5 seconds (keep them short!)
- **Volume**: Normalize to consistent level

## Usage

Sounds are automatically loaded by `static/js/audio.js` and played on:
- **click**: All button clicks
- **fetch**: Starting video info fetch
- **download**: Starting audio download
- **success**: Successful completion (fetch or download)
- **error**: Error occurred

Users can toggle sound effects on/off via browser (settings persist in localStorage).
