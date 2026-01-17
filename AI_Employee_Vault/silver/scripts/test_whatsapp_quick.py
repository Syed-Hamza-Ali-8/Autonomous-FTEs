#!/usr/bin/env python3
"""Quick WhatsApp test for Mr Honey"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set to visible browser mode
os.environ['WHATSAPP_HEADLESS'] = 'false'

from src.actions.whatsapp_sender import WhatsAppSender

print("Testing WhatsApp...")
print("(Browser will open - you'll see it)")
print()

sender = WhatsAppSender('/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault')

result = sender.send_message(
    to='Mr Honey 😎',  # Your WhatsApp name (with emoji)
    message='🧪 Test from AI Employee - WhatsApp integration working!'
)

print()
if result['success']:
    print('✅ WhatsApp message sent successfully!')
    print(f"   Message ID: {result.get('message_id', 'N/A')}")
    print(f"   Recipient: {result.get('recipient', 'N/A')}")
    print()
    print('Check your WhatsApp to see the message!')
else:
    print(f"❌ WhatsApp failed: {result.get('error', 'Unknown error')}")
