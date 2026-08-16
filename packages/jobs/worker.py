import asyncio
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from packages.tenant.database import async_session_maker
from packages.jobs.models import OutboxMessage

logger = logging.getLogger(__name__)

class OutboxWorker:
    """
    A simple async worker that polls the outbox_messages table and processes pending messages.
    """
    
    def __init__(self, poll_interval: int = 5, session_maker=None):
        self.poll_interval = poll_interval
        self._running = False
        self.session_maker = session_maker or async_session_maker
        
    async def start(self):
        self._running = True
        logger.info("Starting OutboxWorker...")
        while self._running:
            try:
                await self.process_pending_messages()
            except Exception as e:
                logger.error(f"Error in OutboxWorker: {e}")
            await asyncio.sleep(self.poll_interval)
            
    async def stop(self):
        self._running = False
        logger.info("Stopping OutboxWorker...")
        
    async def process_pending_messages(self):
        async with self.session_maker() as db:
            # Simple polling mechanism (for production, use SELECT FOR UPDATE SKIP LOCKED)
            stmt = select(OutboxMessage).where(
                OutboxMessage.status == 'PENDING'
            ).order_by(OutboxMessage.created_at.asc()).limit(10)
            
            result = await db.execute(stmt)
            messages = result.scalars().all()
            
            for msg in messages:
                try:
                    await self.handle_message(msg)
                    msg.status = 'PROCESSED'
                    msg.processed_at = func.now()
                except Exception as e:
                    # Exponential backoff retry logic
                    msg.retry_count += 1
                    if msg.retry_count > 5:
                        msg.status = 'FAILED'
                    else:
                        msg.status = 'PENDING'
                        msg.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=2 ** msg.retry_count)
                    msg.error_message = str(e)
                    
            if messages:
                await db.commit()
                
    async def handle_message(self, message: OutboxMessage):
        """
        Routes the message to the appropriate handler based on its type.
        """
        # Logic to route message to specific handlers
        # e.g., if message.type == 'WebhookReceived': handle_webhook(message.payload)
        pass

# Example usage to run the worker
# if __name__ == "__main__":
#     worker = OutboxWorker()
#     asyncio.run(worker.start())
