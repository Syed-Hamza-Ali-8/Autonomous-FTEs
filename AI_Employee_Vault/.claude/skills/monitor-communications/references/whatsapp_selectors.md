# WhatsApp Web Selectors

**Last Updated**: 2026-01-13
**WhatsApp Web Version**: 2.2412.x

## Important Notes

⚠️ **WhatsApp Web selectors change frequently**. If selectors stop working:
1. Open WhatsApp Web in browser
2. Inspect elements with DevTools
3. Update selectors below
4. Test thoroughly before deploying

## Main Selectors

### Chat List

```python
# Chat list container
CHAT_LIST = 'div[aria-label="Chat list"]'

# Individual chat items
CHAT_ITEM = 'div[role="listitem"]'

# Unread chat indicator
UNREAD_INDICATOR = 'span[data-icon="unread-count"]'

# Chat name
CHAT_NAME = 'span[title]'

# Last message preview
LAST_MESSAGE = 'span.selectable-text'
```

### Chat Window

```python
# Message container
MESSAGE_CONTAINER = 'div[data-testid="conversation-panel-messages"]'

# Individual messages
MESSAGE = 'div[data-testid="msg-container"]'

# Message text
MESSAGE_TEXT = 'span.selectable-text.copyable-text'

# Message timestamp
MESSAGE_TIME = 'span[data-testid="msg-time"]'

# Sender name (in groups)
SENDER_NAME = 'span[data-testid="message-author"]'
```

### Input Area

```python
# Message input box
INPUT_BOX = 'div[contenteditable="true"][data-tab="10"]'

# Send button
SEND_BUTTON = 'button[data-testid="compose-btn-send"]'

# Attachment button
ATTACH_BUTTON = 'div[title="Attach"]'
```

### Authentication

```python
# QR code container
QR_CODE = 'canvas[aria-label="Scan this QR code to link a device!"]'

# QR code reload button
QR_RELOAD = 'button[data-testid="qrcode-reload"]'

# Login success indicator
LOGIN_SUCCESS = 'div[data-testid="default-user"]'
```

## Playwright Selectors

### Wait for Elements

```python
from playwright.sync_api import sync_playwright

# Wait for chat list to load
page.wait_for_selector(CHAT_LIST, timeout=30000)

# Wait for specific chat
page.wait_for_selector(f'span[title="{chat_name}"]', timeout=10000)
```

### Extract Messages

```python
# Get all unread chats
unread_chats = page.query_selector_all(f'{CHAT_ITEM}:has({UNREAD_INDICATOR})')

for chat in unread_chats:
    # Get chat name
    name_element = chat.query_selector(CHAT_NAME)
    chat_name = name_element.get_attribute('title')

    # Click to open chat
    chat.click()

    # Wait for messages to load
    page.wait_for_selector(MESSAGE_CONTAINER)

    # Get all messages
    messages = page.query_selector_all(MESSAGE)

    for msg in messages:
        text = msg.query_selector(MESSAGE_TEXT).inner_text()
        time = msg.query_selector(MESSAGE_TIME).inner_text()
```

## Session Management

### Save Session

```python
# Save browser context (includes cookies, localStorage)
context = browser.new_context(storage_state='whatsapp_session.json')
page = context.new_page()

# After login, save state
context.storage_state(path='whatsapp_session.json')
```

### Restore Session

```python
# Restore session on next run
context = browser.new_context(storage_state='whatsapp_session.json')
page = context.new_page()
page.goto('https://web.whatsapp.com')

# Check if logged in
if page.query_selector(LOGIN_SUCCESS):
    print("Session restored successfully")
```

## Error Handling

### Common Issues

1. **QR Code Expired**
   - Selector: `button[data-testid="qrcode-reload"]`
   - Action: Click reload button

2. **Phone Disconnected**
   - Selector: `div[data-testid="alert-phone-disconnected"]`
   - Action: Notify user to reconnect phone

3. **Rate Limited**
   - Indicator: Messages not loading
   - Action: Wait 60 seconds, retry

4. **Element Not Found**
   - Cause: Selector changed
   - Action: Update selectors, test thoroughly

## Testing Selectors

```python
# Test script to verify selectors
def test_selectors(page):
    selectors = {
        'chat_list': CHAT_LIST,
        'message_container': MESSAGE_CONTAINER,
        'input_box': INPUT_BOX,
    }

    for name, selector in selectors.items():
        try:
            element = page.wait_for_selector(selector, timeout=5000)
            print(f"✅ {name}: Found")
        except:
            print(f"❌ {name}: Not found - UPDATE NEEDED")
```

## Alternative Selectors

If primary selectors fail, try these alternatives:

```python
# Chat list (alternative)
CHAT_LIST_ALT = '#pane-side'

# Message text (alternative)
MESSAGE_TEXT_ALT = 'div.copyable-text > span'

# Input box (alternative)
INPUT_BOX_ALT = 'div[role="textbox"]'
```

## References

- [Playwright Selectors](https://playwright.dev/python/docs/selectors)
- [WhatsApp Web Reverse Engineering](https://github.com/sigalor/whatsapp-web-reveng)
