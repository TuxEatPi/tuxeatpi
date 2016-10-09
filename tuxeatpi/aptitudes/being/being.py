from queue import Empty
import time
from datetime import timedelta, datetime
import threading

import agecalc
import hug

from tuxeatpi.aptitudes.common import Aptitude, capability, can_transmit
from tuxeatpi.libs.lang import gtt, doc
from tuxeatpi.transmission import create_transmission


class Being(Aptitude, threading.Thread):

    def __init__(self, settings):
        threading.Thread.__init__(self)
        Aptitude.__init__(self, settings)
        self.start_time = time.time()

    # TuxDroid name
    def _get_name(self):
        """Return TuxDroid name"""
        return self.settings['global']['name']

    @capability(gtt("Give my name"))
    @can_transmit
    def get_name(self):
        """Return TuxDroid name text"""
        self.logger.debug("name")
        name = self._get_name()
        text = gtt("My name is {}").format(name)
        return text

    # TuxDroid birthday
    def _get_birthday(self):
        """Return TuxDroid birthday"""
        return datetime.fromtimestamp(self.settings['data']['birthday'])

    @capability(gtt("Give my birthday"))
    @can_transmit
    def get_birthday(self):
        """Return TuxDroid birthday text"""
        birthday_str = self._get_birthday().strftime("%B %-d, %Y at %I:%M %p")
        text = gtt("I'm born on {}").format(birthday_str)
        # Create a transmission
#        if id_ is not None and s_mod is not None and s_func is not None:
#            content = {"attributes": {"text": text}}
#            create_transmission(s_mod, s_func, s_mod, s_func, content, id_)
        return text

    # Get Uptime
    def _get_uptime(self):
        """Return current uptime"""
        return timedelta(seconds=time.time() - self.start_time)

#    def get_uptime(self, id_=None, s_mod=None, s_func=None):
    @capability(gtt("Give my uptime"))
    @can_transmit
    def get_uptime(self):
        """Return current uptime"""
        uptime = self._get_uptime()
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
            text += " {} minutes".format(minutes)
        if seconds <= 1:
            text += " {} second".format(seconds)
        elif minutes > 1:
            text += " {} seconds".format(seconds)
        # Create a transmission
#        if id_ is not None and s_mod is not None and s_func is not None:
#            content = {"attributes": {"text": text}}
#            create_transmission(s_mod, s_func, s_mod, s_func, content, id_)
        return text

    # Get age
    def _get_age(self):
        """Return TuxDroid age"""
        birth_day = datetime.fromtimestamp(self.settings['data']['birthday'])
        now = datetime.now()
        tux_age = agecalc.AgeCalc(birth_day.day, birth_day.month, birth_day.year)

        years = None
        months = None
        days = None
        if birth_day - now < timedelta(days=30):
            delta = now - birth_day
            days = delta.days
        else:
            years = tux_age.age_years_months['years']
            months = tux_age.age_years_months['months']
        self.logger.debug("age: %s, %s, %s", years, months, days)
        return (years, months, days)

    @capability(gtt("Give my age"))
    def get_age(self, id_=None, s_mod=None, s_func=None):
        """Return TuxDroid age"""
        years, months, days = self._get_age()

        if years is None and months is None:
            if days <= 1:
                text = gtt("I'm {} day old").format(days)
            else:
                text = gtt("I'm {} days old").format(days)
        elif years == 0:
            if months == 1:
                text = gtt("I'm {} month old").format(months)
            else:
                text = gtt("I'm {} months old").format(months)
        elif years == 1:
            if months == 0:
                text = gtt("I'm {} year").format(years, months)
            elif months == 1:
                text = gtt("I'm {} year and {} month").format(years, months)
            else:
                text = gtt("I'm {} year and {} months").format(years, months)
        else:
            if months == 0:
                text = gtt("I'm {} years").format(years, months)
            elif months == 1:
                text = gtt("I'm {} years and {} month").format(years, months)
            else:
                text = gtt("I'm {} years and {} months").format(years, months)
        # Create a transmission
        if id_ is not None and s_mod is not None and s_func is not None:
            content = {"attributes": {"text": text}}
            create_transmission(s_mod, s_func, s_mod, s_func, content, id_)
        return text

    # Get time
    # TODO put it in clock skill
    def get_time(self, id_=None, s_mod=None, s_func=None):
        """Return current time"""
        now = datetime.now()
        text = now.strftime("%I:%M %p")
        # Create a transmission
        if id_ is not None and s_mod is not None and s_func is not None:
            content = {"attributes": {"text": text}}
            create_transmission(s_mod, s_func, s_mod, s_func, content, id_)
        return text

    # Set language
    @capability(gtt("Speak an other language"))
    def set_lang(self, language, id_=None, s_mod=None, s_func=None):
        """Change Tux lang"""
        self.logger.info("Change the language to %s", language)
        new_settings = dict(self.tuxdroid.settings)
        new_settings['speech']['language'] = language
        self.tuxdroid.update_setting(new_settings)
        # Create a transmission
        content = {"attributes": {"text": text}}
        create_transmission(s_mod, s_func, s_mod, s_func, content, id_)
        # Create a transmission
        if id_ is not None and s_mod is not None and s_func is not None:
            content = {"attributes": {"text": text}}
            create_transmission(s_mod, s_func, s_mod, s_func, content, id_)
        text = gtt("I speak english now")
        return text
