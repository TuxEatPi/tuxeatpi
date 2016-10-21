"""Being TuxDroid aptitude module"""

import copy
import time
from datetime import timedelta, datetime

import agecalc

from tuxeatpi.aptitudes.common import ThreadedAptitude, capability, can_transmit, threaded
from tuxeatpi.libs.lang import gtt


class Being(ThreadedAptitude):
    """Being aptitude contains capabilities about TuxDroid himself"""

    def __init__(self, tuxdroid):
        ThreadedAptitude.__init__(self, tuxdroid)
        self.start_time = time.time()

    def help_(self):
        """Return aptitude help"""
        return gtt("talk about myself")

    # TuxDroid name
    def _get_name(self):
        """Return TuxDroid name"""
        return self.settings['global']['name']

    @threaded
    @capability(gtt("Give my name"))
    @can_transmit
    def get_name(self):
        """Return TuxDroid name text"""
        self.logger.debug("name")
        name = self._get_name()
        text = gtt("My name is {}").format(name)
        return {"tts": text, "result": {"name": name}}

    # TuxDroid birthday
    def _get_birthday(self):
        """Return TuxDroid birthday"""
        return datetime.fromtimestamp(self.settings['data']['birthday'])

    @threaded
    @capability(gtt("Give my birthday"))
    @can_transmit
    def get_birthday(self):
        """Return TuxDroid birthday text"""
        birthday_str = self._get_birthday().strftime("%B %-d, %Y at %I:%M %p")
        text = gtt("I'm born on {}").format(birthday_str)
        return {"tts": text, "result": {"birthday": self._get_birthday()}}

    # Get Uptime
    def _get_uptime(self):
        """Return current uptime"""
        return timedelta(seconds=time.time() - self.start_time)

    @threaded
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
        return {"tts": text, "result": {"uptime": uptime}}

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

    @threaded
    @capability(gtt("Give my age"))
    @can_transmit
    def get_age(self):
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

        if years is None:
            years = 0
        if months is None:
            months = 0
        if days is None:
            days = 0
        return {"tts": text, "result": {"age": {"years": years, "months": months, "days": days}}}

    # Set language
    @capability(gtt("Speak an other language"))
    @threaded
    @can_transmit
    def set_lang(self, language):
        """Change Tux lang"""
        self.logger.info("Change the language to %s", language)
        new_settings = copy.deepcopy(dict(self._tuxdroid.settings))
        new_settings['speech']['language'] = language
        self._tuxdroid.update_setting(new_settings)
        # Reload hear aptitude
        self._tuxdroid.aptitudes.hear.reload_decoder()

        text = gtt("I speak english now")
        return {"tts": text, "result": {"language": language}}
