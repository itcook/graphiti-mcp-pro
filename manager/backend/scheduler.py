"""
Log cleanup scheduler using APScheduler
"""

import asyncio
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from datetime import datetime

from .database import cleanup_old_logs, get_setting


class LogCleanupScheduler:
    """Log cleanup scheduler manager"""
    
    def __init__(self):
        """Initialize the scheduler"""
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.job_id = "log_cleanup_job"
        self._initialized = False
    
    def _create_scheduler(self) -> AsyncIOScheduler:
        """Create and configure the scheduler"""
        scheduler = AsyncIOScheduler()

        # Optional: Add event listeners for logging
        scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
        scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)

        return scheduler
    
    def _job_executed(self, event):
        """Handle job execution success"""
        print(f"Log cleanup job executed successfully at {datetime.now()}")
    
    def _job_error(self, event):
        """Handle job execution error"""
        print(f"Log cleanup job failed at {datetime.now()}: {event.exception}")
    
    async def _cleanup_logs_async(self):
        """Async wrapper for cleanup_old_logs function"""
        try:
            # Run the synchronous cleanup function in a thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, cleanup_old_logs)
        except Exception as e:
            print(f"Error during async log cleanup: {e}")
            raise
    
    def initialize(self):
        """Initialize the scheduler and add the cleanup job"""
        if self._initialized:
            return
        
        try:
            # Create scheduler
            self.scheduler = self._create_scheduler()
            
            # Get current settings
            setting = get_setting()
            clean_hour = setting.clean_logs_at_hour
            
            # Add the cleanup job with cron trigger
            # Run daily at the specified hour
            trigger = CronTrigger(hour=clean_hour, minute=0, second=0)
            
            self.scheduler.add_job(
                func=self._cleanup_logs_async,
                trigger=trigger,
                id=self.job_id,
                name="Daily Log Cleanup",
                replace_existing=True,
                # Task-level configuration (overrides defaults)
                coalesce=True,  # Merge duplicate tasks
                max_instances=1,  # Maximum 1 instance running concurrently
                misfire_grace_time=3600  # Grace time for missed tasks (1 hour)
            )
            
            print(f"Log cleanup job scheduled to run daily at {clean_hour:02d}:00")
            self._initialized = True
            
        except Exception as e:
            print(f"Error initializing log cleanup scheduler: {e}")
            raise
    
    def start(self):
        """Start the scheduler"""
        if not self._initialized:
            self.initialize()
        
        if self.scheduler and not self.scheduler.running:
            self.scheduler.start()
            print("Log cleanup scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            print("Log cleanup scheduler stopped")
    
    def reschedule_cleanup_job(self, new_hour: int):
        """Reschedule the cleanup job to run at a different hour
        
        Args:
            new_hour: Hour of the day (0-23) when the job should run
        """
        if not self.scheduler:
            print("Scheduler not initialized, cannot reschedule job")
            return
        
        try:
            # Validate hour
            if not (0 <= new_hour <= 23):
                raise ValueError(f"Hour must be between 0 and 23, got {new_hour}")
            
            # Create new trigger
            new_trigger = CronTrigger(hour=new_hour, minute=0, second=0)
            
            # Reschedule the job
            self.scheduler.reschedule_job(
                job_id=self.job_id,
                trigger=new_trigger
            )
            
            print(f"Log cleanup job rescheduled to run daily at {new_hour:02d}:00")
            
        except Exception as e:
            print(f"Error rescheduling log cleanup job: {e}")
            raise
    
    def get_next_run_time(self) -> Optional[datetime]:
        """Get the next scheduled run time for the cleanup job"""
        if not self.scheduler:
            return None
        
        try:
            job = self.scheduler.get_job(self.job_id)
            if job:
                return job.next_run_time
        except Exception as e:
            print(f"Error getting next run time: {e}")
        
        return None
    
    def trigger_cleanup_now(self):
        """Trigger log cleanup immediately (for testing purposes)"""
        if not self.scheduler:
            print("Scheduler not initialized, cannot trigger cleanup")
            return
        
        try:
            # Add a one-time job to run immediately
            self.scheduler.add_job(
                func=self._cleanup_logs_async,
                trigger='date',
                run_date=datetime.now(),
                id=f"{self.job_id}_manual",
                name="Manual Log Cleanup",
                replace_existing=True
            )
            print("Manual log cleanup triggered")
            
        except Exception as e:
            print(f"Error triggering manual cleanup: {e}")
            raise


# Global scheduler instance
log_cleanup_scheduler = LogCleanupScheduler()
