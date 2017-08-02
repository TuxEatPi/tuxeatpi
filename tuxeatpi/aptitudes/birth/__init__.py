import time

def check_birth(tuxdroid):
    """Check if TuxDroid is already birth"""
    if not tuxdroid.settings.get('data', {}).get('birthday'):
        tuxdroid.settings['data']['birthday'] = time.time()
#        tuxdroid.settings.save()
        return True
    else:
        return False
