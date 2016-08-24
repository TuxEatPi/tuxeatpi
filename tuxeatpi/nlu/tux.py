"""NLU Tux actions"""


class NLUAction(object):  # pylint: disable=R0903
    """Base class for all NLU Actions"""

    def __init__(self, tuxdroid):
        self.tuxdroid = tuxdroid


class NLUTux(NLUAction):
    """Class for NLU actions TuxDroid related"""

    prefix = "tux"

    def __init__(self, tuxdroid):
        NLUAction.__init__(self, tuxdroid)

    def get_name(self, print_it=False, text_it=False, say_it=False):
        """Return the tux name"""
        name = self.tuxdroid.get_name()
        text = "My name is {}".format(name)
        if print_it is True:
            print(text)
        if say_it is True:
            self.tuxdroid.say(text)
        if text_it is True:
            return text

    def get_birthday(self, print_it=False, text_it=False, say_it=False):
        """Return the tux birthday"""
        birthday_str = self.tuxdroid.get_birthday().strftime("%B %-d, %Y at %I:%M %p")
        text = "I'm born on {}".format(birthday_str)
        if print_it is True:
            print(text)
        if say_it is True:
            self.tuxdroid.say(text)
        if text_it is True:
            return text

    def get_uptime(self, print_it=False, text_it=False, say_it=False):
        """Return the tux uptime"""
        uptime = self.tuxdroid.get_uptime()
        minutes = uptime.seconds // 60
        seconds = uptime.seconds % 60
        text = "I'm awake for"
        if uptime.days == 1:
            text += " {} day".format(uptime.days)
        elif uptime.days > 1:
            text += " {} days".format(uptime.days)
        if minutes <= 1:
            text += " {} minute".format(minutes)
        elif minutes > 1:
            text += " {} minute".format(minutes)
        if seconds <= 1:
            text += " {} second".format(seconds)
        elif minutes > 1:
            text += " {} seconds".format(seconds)

        if print_it is True:
            print(text)
        if say_it is True:
            self.tuxdroid.say(text)
        if text_it is True:
            return text
