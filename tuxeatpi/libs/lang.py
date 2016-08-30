"""Module handling i18n and l10n for tuxeatpi"""
import gettext


LANGUAGES = {}
_GTT = None


def load_languages():
    """Prepare and load all supported languages

    TODO: make it more dynamic
    """
    # Prepare
    gettext.bindtextdomain('tuxeatpi', 'locale')
    gettext.textdomain('tuxeatpi')
    # Load languages
    _lang_en = gettext.translation('tuxeatpi', localedir='locale', languages=['en'], fallback=True)
    _lang_fr = gettext.translation('tuxeatpi', localedir='locale', languages=['fr'])
    # Put languages in dict
    LANGUAGES['eng-USA'] = _lang_en
    LANGUAGES['fra-FRA'] = _lang_fr
    LANGUAGES['fra-CAN'] = _lang_fr


def set_language(lang):
    """Change language on the fly"""
    global _GTT  # pylint: disable=W0603
    if lang not in LANGUAGES:
        raise Exception("Language not supported")
    LANGUAGES[lang].install('tuxeatpi')
    _GTT = LANGUAGES[lang].gettext


def gtt(message):
    """Gettext wrapper"""
    return _GTT(message)


# Load languages at import
load_languages()
