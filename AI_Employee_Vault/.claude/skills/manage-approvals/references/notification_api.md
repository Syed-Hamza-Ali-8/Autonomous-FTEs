# Desktop Notification API

## Overview

The approval workflow uses desktop notifications to alert users of pending approval requests. This document covers the notification API for all supported platforms.

## Python Library: plyer

We use the `plyer` library for cross-platform desktop notifications.

### Installation

```bash
pip install plyer
```

### Basic Usage

```python
from plyer import notification

notification.notify(
    title='Approval Required',
    message='New email approval request pending',
    app_name='AI Employee Vault',
    timeout=10  # seconds
)
```

## Platform-Specific Implementation

### Linux (libnotify)

**Requirements**:
- `libnotify-bin` package installed
- D-Bus session running

**Installation**:
```bash
sudo apt-get install libnotify-bin
```

**Features**:
- Custom icons
- Action buttons (limited support)
- Urgency levels (low, normal, critical)
- Sound support

**Example**:
```python
from plyer import notification

notification.notify(
    title='Approval Required',
    message='Send email to client@example.com?',
    app_name='AI Employee Vault',
    app_icon='/path/to/icon.png',
    timeout=10,
    ticker='New approval request',
    toast=False
)
```

### Windows

**Requirements**:
- Windows 10+ (native notification support)
- No additional packages needed

**Features**:
- Native Windows notifications
- Action buttons
- Custom icons
- Sound support

**Example**:
```python
from plyer import notification

notification.notify(
    title='Approval Required',
    message='Send email to client@example.com?',
    app_name='AI Employee Vault',
    timeout=10
)
```

### macOS

**Requirements**:
- macOS 10.10+ (native notification support)
- No additional packages needed

**Features**:
- Native macOS notifications
- Action buttons
- Custom icons
- Sound support

**Example**:
```python
from plyer import notification

notification.notify(
    title='Approval Required',
    message='Send email to client@example.com?',
    app_name='AI Employee Vault',
    timeout=10
)
```

## ApprovalNotifier Class

### Implementation

```python
from plyer import notification
import logging

class ApprovalNotifier:
    def __init__(self, app_name: str = "AI Employee Vault"):
        self.app_name = app_name
        self.logger = logging.getLogger(__name__)

    def send_notification(
        self,
        title: str,
        message: str,
        urgency: str = "normal",
        timeout: int = 10
    ) -> bool:
        """
        Send desktop notification.

        Args:
            title: Notification title
            message: Notification message
            urgency: low, normal, critical
            timeout: Seconds to display (0 = until dismissed)

        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            notification.notify(
                title=title,
                message=message,
                app_name=self.app_name,
                timeout=timeout
            )
            self.logger.info(f"Notification sent: {title}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
            return False
```

### Usage

```python
from silver.src.approval.approval_notifier import ApprovalNotifier

notifier = ApprovalNotifier()

# Send normal notification
notifier.send_notification(
    title="Approval Required",
    message="New email approval request pending",
    urgency="normal",
    timeout=10
)

# Send critical notification
notifier.send_notification(
    title="URGENT: File Deletion Approval",
    message="Request to delete important file",
    urgency="critical",
    timeout=0  # Don't auto-dismiss
)
```

## Error Handling

### Common Errors

1. **Notification service not available**
   ```python
   try:
       notification.notify(...)
   except NotImplementedError:
       logger.warning("Notifications not supported on this platform")
       # Fallback: user must check folder manually
   ```

2. **Permission denied**
   ```python
   try:
       notification.notify(...)
   except PermissionError:
       logger.error("Permission denied for notifications")
       # Fallback: user must check folder manually
   ```

3. **D-Bus error (Linux)**
   ```python
   try:
       notification.notify(...)
   except Exception as e:
       if "D-Bus" in str(e):
           logger.error("D-Bus session not available")
           # Fallback: user must check folder manually
   ```

### Graceful Degradation

If notifications fail, the system should continue to work:

```python
def create_approval_request(self, ...):
    # Create approval request file
    request_id = self._create_request_file(...)

    # Try to send notification (non-blocking)
    try:
        self.notifier.send_notification(
            title="Approval Required",
            message=f"New {action_type} request pending"
        )
    except Exception as e:
        self.logger.warning(f"Notification failed: {e}")
        # Continue anyway - user can check folder manually

    return request_id
```

## Testing

### Test Notification Delivery

```python
def test_notification():
    from plyer import notification

    notification.notify(
        title="Test Notification",
        message="If you see this, notifications are working!",
        app_name="AI Employee Vault",
        timeout=5
    )

    print("Notification sent. Did you see it? (y/n)")
    response = input().lower()

    if response == 'y':
        print("✅ Notifications working correctly")
    else:
        print("❌ Notifications not working - check system settings")
```

### Platform Detection

```python
import platform

def get_notification_support():
    system = platform.system()

    if system == "Linux":
        # Check if libnotify is installed
        import subprocess
        try:
            subprocess.run(["notify-send", "--version"],
                         capture_output=True, check=True)
            return True
        except:
            return False

    elif system == "Windows":
        # Windows 10+ has native support
        return platform.release() >= "10"

    elif system == "Darwin":  # macOS
        # macOS 10.10+ has native support
        return True

    return False
```

## Best Practices

1. **Non-blocking**: Never block on notification delivery
2. **Fallback**: Always have a fallback if notifications fail
3. **Rate limiting**: Don't spam notifications (max 1 per minute)
4. **Clear messages**: Keep notification text concise and actionable
5. **Urgency levels**: Use appropriate urgency for each action type
6. **Testing**: Test on all target platforms before deployment

## References

- [plyer Documentation](https://plyer.readthedocs.io/)
- [libnotify Specification](https://specifications.freedesktop.org/notification-spec/)
- [Windows Notifications](https://docs.microsoft.com/en-us/windows/apps/design/shell/tiles-and-notifications/)
- [macOS Notifications](https://developer.apple.com/documentation/usernotifications)
