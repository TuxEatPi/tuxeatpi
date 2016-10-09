"""Module handling i18n and l10n for tuxeatpi"""
import gettext
import locale


LANGUAGES = {'eng-USA': {'gettext': None,
                         'locale': 'en_US.UTF-8'},
             'fra-FRA': {'gettext': None,
                         'locale': 'fr_FR.UTF-8'},
             }

_GTT = None


def load_languages():
    """Prepare and load all supported languages

    TODO: make it more dynamic
    """
    # Prepare
    gettext.bindtextdomain('tuxeatpi', 'tuxeatpi/locale')
    gettext.textdomain('tuxeatpi')
    # Load languages
    _lang_en = gettext.translation('tuxeatpi',
                                   localedir='tuxeatpi/locale',
                                   languages=['en'],
                                   fallback=True)
    LANGUAGES['eng-USA']['gettext'] = _lang_en
    try:
        _lang_fr = gettext.translation('tuxeatpi',
                                       localedir='tuxeatpi/locale',
                                       languages=['fr'])
        LANGUAGES['fra-FRA']['gettext'] = _lang_fr
    except OSError:
        pass


def set_language(lang):
    """Change language on the fly"""
    global _GTT  # pylint: disable=W0603
    if lang not in LANGUAGES:
        raise Exception("Language not supported")
    LANGUAGES[lang]['gettext'].install('tuxeatpi')
    _GTT = LANGUAGES[lang]['gettext'].gettext
    # TODO
    locale.setlocale(locale.LC_TIME, LANGUAGES[lang]['locale'])


def gtt(message):
    """Gettext wrapper"""
    global _GTT
    if _GTT is not None:
        return _GTT(message)
    else:
        return message


def doc(text):
    def wrapper(func):
        func.__doc__ = text
        return func
    return wrapper

# Load languages at import
load_languages()
