# LinkedIn Playwright Selectors Reference

This document contains CSS selectors for LinkedIn Web automation using Playwright.

## Important Notes

⚠️ **LinkedIn UI changes frequently**. These selectors may need updates.

**Last verified**: 2026-01-16
**LinkedIn version**: Web (desktop)

## Posting Workflow Selectors

### 1. Start a Post Button

**Primary selector** (most reliable):
```python
page.click('button:has-text("Start a post")')
```

**Alternative selectors** (fallbacks):
```python
# By aria-label
page.click('[aria-label*="Start a post"]')

# By class (less reliable, changes often)
page.click('.share-box-feed-entry__trigger')

# By data attribute
page.click('[data-test-share-box-trigger]')
```

**Verification**:
```python
# Check if button exists
if page.locator('button:has-text("Start a post")').count() > 0:
    print("Start post button found")
```

### 2. Text Editor

**Primary selector**:
```python
page.wait_for_selector('[role="textbox"]')
editor = page.locator('[role="textbox"]').first
```

**Alternative selectors**:
```python
# By contenteditable attribute
page.locator('[contenteditable="true"]').first

# By class
page.locator('.ql-editor')

# By aria-label
page.locator('[aria-label*="share your thoughts"]')
```

**Fill content**:
```python
editor.click()
editor.fill(content)
```

### 3. Post Button

**Primary selector**:
```python
page.click('button:has-text("Post")')
```

**Alternative selectors**:
```python
# By aria-label
page.click('[aria-label="Post"]')

# By data attribute
page.click('[data-test-modal-close-btn]')

# By class
page.click('.share-actions__primary-action')
```

**Verification**:
```python
# Wait for post to complete
page.wait_for_timeout(3000)

# Check if modal closed
if page.locator('[role="dialog"]').count() == 0:
    print("Post completed")
```

## Authentication Selectors

### Login Page

**Email input**:
```python
page.fill('#username', email)
```

**Password input**:
```python
page.fill('#password', password)
```

**Sign in button**:
```python
page.click('button[type="submit"]')
```

### Session Verification

**Check if logged in**:
```python
# If URL contains "login" or "authwall", not logged in
if "login" in page.url.lower() or "authwall" in page.url.lower():
    print("Not logged in")
else:
    print("Logged in")
```

**Check for feed**:
```python
# Feed should be visible when logged in
if page.locator('[role="main"]').count() > 0:
    print("Feed loaded")
```

## Image Upload Selectors

### Add Media Button

**Primary selector**:
```python
page.click('button:has-text("Add media")')
```

**Alternative selectors**:
```python
# By aria-label
page.click('[aria-label*="Add media"]')

# By icon class
page.click('.share-box-footer__media-button')
```

### File Input

**Upload image**:
```python
page.set_input_files('input[type="file"]', image_path)
```

**Wait for upload**:
```python
# Wait for image preview
page.wait_for_selector('.share-media-preview')
page.wait_for_timeout(2000)  # Additional wait for processing
```

## Navigation Selectors

### Feed URL

```python
FEED_URL = "https://www.linkedin.com/feed/"
page.goto(FEED_URL, wait_until="networkidle")
```

### Profile URL

```python
PROFILE_URL = "https://www.linkedin.com/in/me/"
page.goto(PROFILE_URL)
```

## Error Detection Selectors

### Error Messages

**Generic error**:
```python
error = page.locator('[role="alert"]').text_content()
```

**Post error**:
```python
error = page.locator('.artdeco-inline-feedback--error').text_content()
```

### Rate Limiting

**Detect rate limit**:
```python
if "too many requests" in page.content().lower():
    print("Rate limited")
```

## Selector Update Process

When LinkedIn UI changes:

1. **Detect failure**:
   ```python
   try:
       page.click('button:has-text("Start a post")', timeout=5000)
   except PlaywrightTimeout:
       logger.error("Selector outdated")
   ```

2. **Inspect element**:
   - Open LinkedIn in browser
   - Right-click "Start a post" button
   - Select "Inspect"
   - Copy selector

3. **Update code**:
   ```python
   # Old selector (broken)
   # page.click('button:has-text("Start a post")')

   # New selector (updated)
   page.click('[data-test-share-box-trigger="true"]')
   ```

4. **Test**:
   ```bash
   python silver/scripts/test_linkedin.py --dry-run
   ```

## Selector Strategies

### 1. Text-Based (Most Reliable)

**Pros**: Survives UI changes
**Cons**: Language-dependent

```python
page.click('button:has-text("Start a post")')
```

### 2. Aria-Label (Reliable)

**Pros**: Accessibility-focused, stable
**Cons**: May change with UI updates

```python
page.click('[aria-label="Start a post"]')
```

### 3. Data Attributes (Moderate)

**Pros**: Designed for testing
**Cons**: LinkedIn may not use them consistently

```python
page.click('[data-test-share-box-trigger]')
```

### 4. Class Names (Least Reliable)

**Pros**: Direct targeting
**Cons**: Changes frequently with UI updates

```python
page.click('.share-box-feed-entry__trigger')
```

## Recommended Approach

**Use cascading fallbacks**:

```python
def click_start_post(page):
    """Click 'Start a post' button with fallbacks."""
    selectors = [
        'button:has-text("Start a post")',
        '[aria-label*="Start a post"]',
        '.share-box-feed-entry__trigger',
        '[data-test-share-box-trigger]'
    ]

    for selector in selectors:
        try:
            page.click(selector, timeout=5000)
            return True
        except PlaywrightTimeout:
            continue

    raise Exception("Could not find 'Start a post' button")
```

## Debugging Selectors

### Take Screenshot

```python
page.screenshot(path="debug_linkedin.png")
```

### Print Page Content

```python
print(page.content())
```

### List All Buttons

```python
buttons = page.locator('button').all()
for i, button in enumerate(buttons):
    print(f"{i}: {button.text_content()}")
```

### Check Element Visibility

```python
if page.locator('button:has-text("Start a post")').is_visible():
    print("Button is visible")
else:
    print("Button is hidden or doesn't exist")
```

## Common Issues

### Issue 1: Button Not Found

**Symptoms**: `PlaywrightTimeout` error

**Causes**:
- LinkedIn UI changed
- Page not fully loaded
- Session expired (redirected to login)

**Solutions**:
1. Increase timeout: `page.click(selector, timeout=10000)`
2. Wait for network idle: `page.goto(url, wait_until="networkidle")`
3. Check if logged in: `if "login" not in page.url`
4. Update selector (see update process above)

### Issue 2: Element Not Clickable

**Symptoms**: Element found but click fails

**Causes**:
- Element covered by modal/overlay
- Element not yet interactive
- JavaScript not finished loading

**Solutions**:
1. Wait for element: `page.wait_for_selector(selector, state="visible")`
2. Scroll into view: `element.scroll_into_view_if_needed()`
3. Force click: `element.click(force=True)`
4. Wait for load: `page.wait_for_load_state("networkidle")`

### Issue 3: Text Not Filled

**Symptoms**: Editor found but content not appearing

**Causes**:
- Editor not focused
- JavaScript event listeners not ready
- Content cleared by LinkedIn

**Solutions**:
1. Click before fill: `editor.click()` then `editor.fill(content)`
2. Type instead of fill: `editor.type(content, delay=50)`
3. Use keyboard: `page.keyboard.type(content)`
4. Wait after fill: `page.wait_for_timeout(1000)`

## Testing Selectors

### Manual Test

```bash
# Open browser and inspect
python -c "
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto('https://www.linkedin.com/feed/')
    input('Press Enter to close...')
    browser.close()
"
```

### Automated Test

```python
def test_selectors():
    """Test all critical selectors."""
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(session_path)
        page = browser.new_page()
        page.goto("https://www.linkedin.com/feed/")

        # Test each selector
        tests = {
            "Start post button": 'button:has-text("Start a post")',
            "Text editor": '[role="textbox"]',
            "Post button": 'button:has-text("Post")'
        }

        for name, selector in tests.items():
            if page.locator(selector).count() > 0:
                print(f"✅ {name}: Found")
            else:
                print(f"❌ {name}: Not found")

        browser.close()
```

## Maintenance Schedule

**Weekly**: Check for UI changes
**Monthly**: Update selectors if needed
**Quarterly**: Full selector audit

## Summary

**Key selectors**:
- Start post: `button:has-text("Start a post")`
- Text editor: `[role="textbox"]`
- Post button: `button:has-text("Post")`

**Best practices**:
1. Use text-based selectors when possible
2. Implement fallback selectors
3. Add proper error handling
4. Test after LinkedIn updates
5. Keep this document updated

**When selectors break**:
1. Check logs for error
2. Inspect LinkedIn UI
3. Update selector
4. Test with dry run
5. Deploy update
