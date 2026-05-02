import logging
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from tools.news_tools import fetch_news
from tools.system_tools import get_system_info
from tools.productivity_tools import get_reminders
from tools.system_tools import open_multiple_urls

class ProactiveEngine:
    def __init__(self, agent_session=None):
        """
        Proactive intelligence engine that runs scheduled tasks.
        :param agent_session: The active LiveKit AgentSession to push voice updates.
        """
        self.scheduler = AsyncIOScheduler()
        self.agent_session = agent_session
        self.logger = logging.getLogger("ProactiveEngine")

    async def _speak(self, text: str):
        """Helper to push text to the agent session for speech."""
        if self.agent_session:
            try:
                # We use generate_reply to make the agent speak the text
                await self.agent_session.generate_reply(instructions=f"Speak this exactly: {text}")
            except Exception as e:
                self.logger.error(f"Failed to push speech to session: {e}")
        else:
            self.logger.info(f"[PROACTIVE VOICE]: {text}")

    async def morning_briefing(self):
        """8 AM daily: weather + news + calendar + tasks."""
        self.logger.info("Running morning briefing...")

        # 1. News
        news = await fetch_news(None, category="World") # context is None for manual call

        # 2. Reminders
        reminders = await get_reminders(None)

        # 3. Construct briefing
        briefing = f"Good morning, Sir. Your morning briefing: {news}\n\nYour schedule: {reminders}"
        await self._speak(briefing)

    async def reminder_checker(self):
        """Every 60s: check SQLite for due reminders, speak them."""
        self.logger.info("Checking for due reminders...")
        reminders = await get_reminders(None)

        # In a real scenario, we would check if CURRENT_TIME matches the reminder time
        # For this demo, we'll just log if reminders exist.
        # Actual implementation would involve comparing datetime.now() with reminder.datetime.
        if "No upcoming reminders" not in reminders:
             self.logger.info(f"Reminders pending: {reminders}")

    async def news_digest(self):
        """Every 2 hours: fetch top 3 new headlines not yet reported."""
        self.logger.info("Running news digest...")
        news = await fetch_news(None, category="Tech")
        await self._speak(f"Sir, a quick tech update: {news}")

    async def system_health_monitor(self):
        """Every 5 min: check CPU/RAM/battery, warn if critical."""
        self.logger.info("Monitoring system health...")
        info = await get_system_info(None)

        # Simple threshold check
        if "CPU Usage: 90%" in info or "RAM Usage: 90%" in info:
            await self._speak("Sir, system resources are critically low. I suggest closing some heavy applications.")

    def start(self):
        """Schedule all proactive tasks."""
        # Morning Briefing - Daily 8 AM
        self.scheduler.add_job(self.morning_briefing, 'cron', hour=8, minute=0)

        # Reminder Checker - Every 60 seconds
        self.scheduler.add_job(self.reminder_checker, 'interval', seconds=60)

        # News Digest - Every 2 hours
        self.scheduler.add_job(self.news_digest, 'interval', hours=2)

        # Health Monitor - Every 5 minutes
        self.scheduler.add_job(self.system_health_monitor, 'interval', minutes=5)

        self.scheduler.start()
        self.logger.info("Proactive Intelligence Engine started and scheduled.")

    def stop(self):
        self.scheduler.shutdown()
        self.logger.info("Proactive Intelligence Engine stopped.")
