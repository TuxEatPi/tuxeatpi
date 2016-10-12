"""Clock skill module"""

from datetime import datetime

from tuxeatpi.skills.common import ThreadedSkill, capability, can_transmit, threaded
from tuxeatpi.libs.lang import gtt


class Clock(ThreadedSkill):
    """Skill about clock, timer, ..."""

    def __init__(self, settings):
        ThreadedSkill.__init__(self, settings)

    def help_(self):
        """Return skill help"""
        return gtt("talk about time")

    @capability(gtt("Give time"))
    @threaded
    @can_transmit
    def get_time(self):  # pylint: disable=R0201
        """Return current time"""
        now = datetime.now()
        time_text = now.strftime(gtt("%I:%M %p"))
        tts = gtt("It's {}").format(time_text)
        return {"tts": tts, "result": {"time": time_text}}
