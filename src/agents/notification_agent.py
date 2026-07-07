import logging
from typing import List
from src.sources.base import JobPosting
from src.notifications.notifier import JobNotifier

logger = logging.getLogger(__name__)

class NotificationAgent:
    """Agent responsible for creating summaries and triggering notifications."""
    
    def __init__(self, notifier: JobNotifier):
        self.notifier = notifier
        
    def notify_summary(self, matched_jobs: List[JobPosting]) -> str:
        """Generates a summary of matched jobs using JobNotifier."""
        logger.info(f"NotificationAgent generating match summary for {len(matched_jobs)} jobs.")
        return self.notifier.summarize_matches(matched_jobs)
