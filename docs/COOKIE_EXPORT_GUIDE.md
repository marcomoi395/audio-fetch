# YouTube Cookie Export Guide

This guide provides step-by-step instructions for exporting YouTube cookies to use with Audio Fetch.

## Why Cookies?

YouTube uses bot detection that may block automated downloads. Providing your browser cookies allows the application to authenticate as your logged-in session, bypassing these restrictions.

## Security & Privacy

**Important:** Cookies contain authentication tokens that grant access to your YouTube account.

- **Only use trusted cookie export extensions** from official browser stores
- **Never share your cookies** with others or paste them in untrusted applications
- **Cookies are processed server-side** in temporary files and deleted immediately after use
- **No cookies are stored persistently** on the server
- **Review the source code** at the repository to verify cookie handling

## Chrome: Using "Get cookies.txt LOCALLY"

### 1. Install Extension

1. Open Chrome Web Store
2. Search for "Get cookies.txt LOCALLY"
3. Verify publisher and ratings before installing
4. Click "Add to Chrome"

### 2. Export Cookies

1. Navigate to `youtube.com` in Chrome
2. Make sure you're logged in to your YouTube account
3. Click the extension icon in your toolbar
4. Click "Export" or "Copy to Clipboard"
5. Cookies are now copied in Netscape format

### 3. Use in Audio Fetch

1. Open Audio Fetch web interface
2. Click "🍪 Optional: Add cookies (click to expand)"
3. Paste the copied cookies into the textarea
4. Enter your YouTube URL and fetch video info

## Firefox: Using "cookies.txt"

### 1. Install Extension

1. Open Firefox Add-ons
2. Search for "cookies.txt"
3. Look for extensions that export in Netscape format
4. Click "Add to Firefox"

### 2. Export Cookies

1. Navigate to `youtube.com` in Firefox
2. Make sure you're logged in to your YouTube account
3. Click the extension icon in your toolbar
4. Select "Export for current site" or similar
5. Copy the exported cookie text

### 3. Use in Audio Fetch

1. Open Audio Fetch web interface
2. Click "🍪 Optional: Add cookies (click to expand)"
3. Paste the copied cookies into the textarea
4. Enter your YouTube URL and fetch video info

## Netscape Cookie Format

Cookies must be in Netscape format, which looks like this:

```
# Netscape HTTP Cookie File
.youtube.com	TRUE	/	TRUE	0	CONSENT	YES+cb.20210328-17-p0.en+FX+865
.youtube.com	TRUE	/	FALSE	1234567890	VISITOR_INFO1_LIVE	xxx_xxxxxxxx
.youtube.com	TRUE	/	TRUE	1234567890	PREF	tz=America.Los_Angeles
```

Each line (except comments starting with `#`) contains:
- Domain
- Domain flag (TRUE/FALSE)
- Path
- Secure flag (TRUE/FALSE)
- Expiration timestamp
- Cookie name
- Cookie value

## Troubleshooting

### "Invalid cookie format" error

- Ensure cookies are in Netscape format (not JSON or other formats)
- Check that you copied the entire cookie block
- Verify no extra characters were added during copy/paste

### Download still fails with cookies

- **Cookies may have expired**: Export fresh cookies
- **IP mismatch**: YouTube cookies are often tied to your IP address/region
- **Account restrictions**: Some YouTube accounts have download restrictions
- **Try incognito mode**: Export cookies from a fresh incognito session

### Extension not working

- Try a different extension
- Check browser console for errors
- Verify extension permissions
- Update browser to latest version

## When to Use Cookies

You typically need cookies when:

- You encounter "Sign in to confirm you're not a bot" errors
- Downloads fail with authentication errors  
- YouTube shows captcha or verification screens
- Accessing age-restricted or region-locked content

For most public videos, cookies may not be required.

## Cookie Lifespan

YouTube cookies typically expire after:

- **Session cookies**: When you close the browser
- **Persistent cookies**: 1-2 years from creation

If downloads suddenly stop working, try exporting fresh cookies.

---

**Security Reminder:** Only use cookie export extensions from trusted sources. Review the Audio Fetch source code to verify cookie handling before use.
