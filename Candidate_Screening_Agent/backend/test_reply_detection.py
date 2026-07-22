"""Quick test for ReplyWatcher message detection."""
import asyncio
import os
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy import select
from db.database import AsyncSessionLocal
from db.models import Candidate, SchedulingConversation
import redis.asyncio as redis

load_dotenv()

async def test_detection():
    print('=' * 60)
    print('REPLY WATCHER MESSAGE DETECTION TEST')
    print('=' * 60)
    
    # Test 1: Gmail API
    print('\n[1/5] Testing Gmail API connection...')
    try:
        credentials = Credentials(
            token=None,
            refresh_token=os.getenv('GMAIL_REFRESH_TOKEN'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=os.getenv('GMAIL_CLIENT_ID'),
            client_secret=os.getenv('GMAIL_CLIENT_SECRET'),
        )
        service = build('gmail', 'v1', credentials=credentials)
        profile = service.users().getProfile(userId='me').execute()
        print(f'      ✅ Connected: {profile.get("emailAddress")}')
    except Exception as e:
        print(f'      ❌ Failed: {e}')
        return
    
    # Test 2: Redis
    print('\n[2/5] Testing Redis connection...')
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        r = await redis.from_url(redis_url)
        await r.ping()
        processed_count = await r.scard('processed_emails')
        print(f'      ✅ Connected: {processed_count} processed messages in cache')
    except Exception as e:
        print(f'      ❌ Failed: {e}')
        r = None
    
    # Test 3: Find candidates
    print('\n[3/5] Finding candidates awaiting replies...')
    try:
        async with AsyncSessionLocal() as db:
            # Screening candidates
            query = select(Candidate).where(Candidate.status == 'awaiting_reply')
            result = await db.execute(query)
            screening = result.scalars().all()
            
            # Scheduling conversations
            sched_query = select(SchedulingConversation).where(
                SchedulingConversation.conversation_state.in_([
                    'proposing_times', 'awaiting_confirmation', 
                    'awaiting_questions_reply', 'awaiting_timezone', 
                    'rescheduling', 'confirmed'
                ])
            )
            result = await db.execute(sched_query)
            scheduling_convs = result.scalars().all()
            
            # Get candidate emails for scheduling
            scheduling_candidates = []
            for conv in scheduling_convs:
                cand = await db.get(Candidate, conv.candidate_id)
                if cand:
                    scheduling_candidates.append(cand)
            
            print(f'      Screening: {len(screening)} candidates')
            print(f'      Scheduling: {len(scheduling_candidates)} candidates')
            
            all_candidates = list(screening) + scheduling_candidates
            
            if not all_candidates:
                print('      ⚠️  No candidates awaiting replies - cannot test detection')
                print('         Add a candidate in "awaiting_reply" status or with active scheduling')
                return
            
            print(f'\n      Candidates to monitor:')
            for cand in all_candidates[:5]:
                print(f'        - {cand.email} (ID: {cand.id})')
    
    except Exception as e:
        print(f'      ❌ Database query failed: {e}')
        return
    
    # Test 4: Search for messages
    print('\n[4/5] Searching Gmail for messages from candidates...')
    try:
        found_replies = []
        
        for cand in all_candidates:
            query_str = f'from:{cand.email} -in:sent newer_than:24h'
            results = service.users().messages().list(
                userId='me', q=query_str, maxResults=5
            ).execute()
            
            messages = results.get('messages', [])
            if messages:
                print(f'\n      ✅ Found {len(messages)} message(s) from {cand.email}')
                
                for msg in messages:
                    full_msg = service.users().messages().get(
                        userId='me', id=msg['id'], format='full'
                    ).execute()
                    
                    headers = full_msg['payload'].get('headers', [])
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No subject')
                    in_reply_to = next((h['value'] for h in headers if h['name'] == 'In-Reply-To'), '')
                    
                    # Check if already processed
                    is_processed = False
                    if r:
                        is_processed = await r.sismember('processed_emails', msg['id'])
                    
                    print(f'         Message ID: {msg["id"]}')
                    print(f'         Subject: {subject[:50]}')
                    print(f'         Has In-Reply-To: {"Yes" if in_reply_to else "No"}')
                    print(f'         Already processed: {"Yes" if is_processed else "No"}')
                    
                    if in_reply_to and not is_processed:
                        found_replies.append({
                            'msg_id': msg['id'],
                            'candidate_id': cand.id,
                            'email': cand.email
                        })
        
        if not found_replies:
            print('\n      ⚠️  No new replies detected in last 24 hours')
        else:
            print(f'\n      ✅ Detected {len(found_replies)} new reply(ies) that would be processed!')
    
    except Exception as e:
        print(f'      ❌ Search failed: {e}')
        import traceback
        traceback.print_exc()
    
    # Test 5: Summary
    print('\n[5/5] Summary')
    print('=' * 60)
    print(f'Gmail API: ✅')
    print(f'Redis: {"✅" if r else "❌"}')
    print(f'Candidates monitored: {len(all_candidates)}')
    print(f'New replies detected: {len(found_replies) if "found_replies" in locals() else 0}')
    
    if 'found_replies' in locals() and found_replies:
        print('\n✅ ReplyWatcher SHOULD detect these messages!')
        print('   Make sure the orchestrator is running to process them.')
    elif all_candidates:
        print('\n⚠️  No new messages to detect from monitored candidates.')
        print('   Send a test reply to one of the emails above to test detection.')
    else:
        print('\n⚠️  No candidates to monitor.')
    
    print('=' * 60)
    
    # Cleanup
    if r:
        await r.close()

if __name__ == '__main__':
    asyncio.run(test_detection())
