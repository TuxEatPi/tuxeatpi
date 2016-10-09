
from tuxeatpi.transmission import create_transmission
from tuxeatpi.skills.common import SkillThread


class Clock(SkillThread):
    def __init__(self):
        SkillThread.__init__(self)

    def get_time(self, print_it=False, text_it=False, say_it=False):
        """Return current time"""
        now = datetime.now()
        text = now.strftime("%I:%M %p")
        if print_it is True:
            print(text)
        if say_it is True:
            create_transmission("clock", "get_time",
                                "aptitude", "tts", {"text": text})
            self.tuxdroid.say()
        if text_it is True:
            return text



