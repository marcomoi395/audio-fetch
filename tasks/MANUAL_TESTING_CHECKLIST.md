# Manual Testing Checklist

## Pre-Testing Setup

- [x] FFmpeg installed and available in PATH
- [x] Virtual environment activated
- [x] Dependencies installed (requirements.txt)
- [x] All automated tests passing (22 tests)

## Server Startup

```bash
# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- [ ] Server starts without errors
- [ ] Access http://localhost:8000
- [ ] Page loads with NES.css 8-bit theme
- [ ] No console errors in browser DevTools

## Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "ffmpeg_available": true,
  "queue_active": false
}
```

- [ ] Health endpoint returns 200 OK
- [ ] FFmpeg availability is true

## Video Info Flow

### Test Case 1: Valid YouTube URL
1. [ ] Enter valid YouTube URL (e.g., https://youtube.com/watch?v=dQw4w9WgXcQ)
2. [ ] Click "Lấy thông tin" button
3. [ ] Hear "click" sound effect
4. [ ] See loading spinner
5. [ ] Hear "fetch" sound effect
6. [ ] Video info displays: title, uploader, duration, thumbnail
7. [ ] Hear "success" sound effect
8. [ ] Format dropdown populated (mp3, m4a, opus, wav, best)
9. [ ] Quality dropdown populated (Best, Medium, Low)

### Test Case 2: Invalid URL
1. [ ] Enter invalid URL (e.g., "not-a-url")
2. [ ] Click "Lấy thông tin"
3. [ ] Hear "click" then "error" sound effect
4. [ ] Error message displays in Vietnamese
5. [ ] "Thử lại" button appears
6. [ ] Click "Thử lại" returns to input form

### Test Case 3: Private/Unavailable Video
1. [ ] Enter URL of private/deleted video
2. [ ] Click "Lấy thông tin"
3. [ ] Error message: "Video không khả dụng..."
4. [ ] Hear "error" sound effect

## Download Flow

### Test Case 4: Download MP3 (Best Quality)
1. [ ] Fetch valid video info first
2. [ ] Select format: mp3
3. [ ] Select quality: Best (0)
4. [ ] Click "Download" button
5. [ ] Hear "click" then "download" sound effect
6. [ ] Button text changes to "⬇️ Đang tải..."
7. [ ] Button disabled during download
8. [ ] File downloads to browser's download folder
9. [ ] Hear "success" sound effect
10. [ ] Button shows "✅ Thành công!" briefly
11. [ ] Button resets after 2 seconds

### Test Case 5: Download Different Formats
Test each format:
- [ ] MP3 (audio/mpeg)
- [ ] M4A (audio/mp4)
- [ ] Opus (audio/opus)
- [ ] WAV (audio/wav)
- [ ] Best (default format)

### Test Case 6: Concurrent Download Blocking
1. [ ] Start download 1 (long video)
2. [ ] Immediately try download 2 in new tab
3. [ ] Expected: Second download returns 503 error
4. [ ] Error message: "Another download is in progress..."
5. [ ] Wait for download 1 to complete
6. [ ] Retry download 2
7. [ ] Expected: Download 2 succeeds

## UI/UX Testing

### Responsive Design
- [ ] Test on desktop (1920x1080)
- [ ] Test on tablet (768x1024)
- [ ] Test on mobile (375x667)
- [ ] Layout adapts correctly at all sizes
- [ ] Text remains readable
- [ ] Buttons are touch-friendly on mobile

### Keyboard Navigation
- [ ] Tab through all interactive elements
- [ ] Press Enter in URL input to fetch info
- [ ] Focus states visible on all buttons

### Sound Effects
- [ ] Click sound on all button clicks
- [ ] Fetch sound when starting info extraction
- [ ] Download sound when starting download
- [ ] Success sound on successful operations
- [ ] Error sound on failures
- [ ] Volume control works (browser console: `soundEffects.setVolume(0.3)`)
- [ ] Toggle sounds (browser console: `soundEffects.toggle()`)

## Error Handling

### Test Case 7: Network Errors
1. [ ] Disconnect internet
2. [ ] Try to fetch video info
3. [ ] Error message displays network-related error
4. [ ] Reconnect internet
5. [ ] Retry successfully

### Test Case 8: FFmpeg Not Available
1. [ ] Check /health endpoint shows ffmpeg_available: false (if FFmpeg removed)
2. [ ] Download attempt fails with FFmpeg error message

### Test Case 9: Rate Limiting
1. [ ] Rapidly fetch info for multiple videos
2. [ ] If rate limited (HTTP 429), error message suggests waiting

## Browser Compatibility

Test in multiple browsers:
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari (macOS)
- [ ] Edge

## Performance

- [ ] Page loads in < 2 seconds
- [ ] Video info fetch completes in < 5 seconds (depends on video)
- [ ] Download starts immediately after button click
- [ ] No memory leaks during extended use
- [ ] Temp files cleaned up after downloads

## Cleanup Verification

After downloads:
- [ ] Check system temp directory
- [ ] Verify old download temp folders are removed
- [ ] No orphaned files left behind

## Final Checks

- [ ] All 22 automated tests passing
- [ ] No console errors in browser
- [ ] No Python exceptions in server logs
- [ ] UI renders correctly in all tested scenarios
- [ ] Sound effects play correctly
- [ ] Downloads complete successfully
- [ ] Error messages are user-friendly (Vietnamese)
- [ ] Queue prevents concurrent downloads
- [ ] README.md accurate and complete

## Notes

Record any issues found during testing:
- Issue 1: [Description]
- Issue 2: [Description]

## Sign-off

- [ ] All critical tests passed
- [ ] All blockers resolved
- [ ] Application ready for deployment

Tested by: _____________  
Date: _____________  
Version: 1.0.0
