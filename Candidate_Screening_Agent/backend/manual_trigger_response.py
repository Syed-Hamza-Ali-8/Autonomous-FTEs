"""
Manually trigger scheduling agent to process the reply.
This bypasses ReplyWatcher and directly calls the scheduling agent.
"""
import asyncio
from db.database import AsyncSessionLocal
from services.scheduling_agent import scheduling_agent

async def process_reply():
    print("=" * 60)
    print("MANUALLY TRIGGERING SCHEDULING RESPONSE")
    print("=" * 60)
    print()
    
    candidate_id = 153
    reply_text = "my timezone is PKT"
    reply_message_id = "19f7bd7287671d87"
    
    print(f"Processing reply for candidate {candidate_id}")
    print(f"Reply text: '{reply_text}'")
    print()
    
    async with AsyncSessionLocal() as db:
        try:
            await scheduling_agent.handle_scheduling_reply(
                db=db,
                candidate_id=candidate_id,
                reply_text=reply_text,
                reply_message_id=reply_message_id
            )
            print("✅ Successfully processed reply!")
            print("   Agent should have sent response email with timezone-aware slots")
        except Exception as e:
            print(f"❌ Error processing reply: {e}")
            import traceback
            traceback.print_exc()

asyncio.run(process_reply())
