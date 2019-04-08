import stt

stt.init()

text = ''
while 'q' not in text.lower():
    print('\n~ Type \'q\' at any time to quit')
    text = input('~ Test Active or Passive Listening? (A/P): ')
    if 'p' in text.lower():
        print('\n~ Wake Up Word: \''+stt.WAKE_UP_WORD+'\'')
        stt.listen_keyword()
        print('~ Wake Up Word Detected!')
    elif 'a' in text.lower():
        stt.active_listen()
