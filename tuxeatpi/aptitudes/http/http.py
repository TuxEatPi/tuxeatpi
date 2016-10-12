"""Web Rest API TuxDroid aptitude module"""

import hug

from gunicorn.app.base import BaseApplication
from gunicorn.six import iteritems

from tuxeatpi.aptitudes.common import SubprocessedAptitude


class _HttpServer(BaseApplication):
    """Wsgi server class for gunicorn"""

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super(_HttpServer, self).__init__()

    def init(self, parser, opts, args):
        """Init method"""
        pass

    def load_config(self):
        """Load config method"""
        config = dict(
            [(key, value) for key, value in iteritems(self.options)
                if key in self.cfg.settings and value is not None]
        )
        for key, value in iteritems(config):
            self.cfg.set(key.lower(), value)

    def load(self):
        """Load application method"""
        return self.application


class Http(SubprocessedAptitude):
    """TuxDroid Http aptitude"""

    def __init__(self, tuxdroid):
        SubprocessedAptitude.__init__(self, tuxdroid)

    def help_(self):
        """Return aptitude help"""
        # TODO do it
        pass

    def run(self):
        """Main function
        - Read arguments
        - Start web server
        """

        @hug.get('/')
        def root():  # pylint: disable=W0612
            """Root path function"""
            return "root"

        # curl
        # -H "Content-Type: application/json"
        # -XPOST -d '{"command": "brain.understand_audio" , "arguments": {}}'
        # http://127.0.0.1:8000/order
        @hug.post('/order')
        def order(command, arguments=None, block=True):  # pylint: disable=W0612
            """order route"""
            if arguments is None:
                arguments = {}
            return self.order(command, arguments, block)

        @hug.post('/understand_text')
        def nlu_text(text, say_it=False):  # pylint: disable=W0612
            """nlu text route"""
            return self.understand_text(text, say_it)

        @hug.post('/understand_audio')
        def nlu_audio(say_it=True):  # pylint: disable=W0612
            """nlu audio route"""
            return self.understand_audio(say_it)

        # Serve in a thread
        try:
            app = hug.API(__name__).http.server()
            self._http_server = _HttpServer(app, {"bind": "0.0.0.0:8000", "workers": 4})
            self._http_server.run()
        except KeyboardInterrupt:
            pass

    def order(self, command, arguments=None, block=True):
        """Http order method"""
        self.logger.info("order: %s with %s", command, arguments)
        if arguments is None:
            arguments = {}
        # If nlu_text use understand_text func
        if command == "brain.understand_text":
            return self.understand_text(**arguments)
        if command == "brain.understand_audio":
            return self.understand_audio(**arguments)
        # For all other order
        # Create transmission
        content = {"arguments": arguments}
        tmn = self.create_transmission("order", command, content)
        # Wait for transmission answer
        if block:
            answer = self.wait_for_answer(tmn.id_)
            # Check if we got an answer
            if answer is None:
                self.logger.warning("No answer for tmn_id: %s", tmn.id_)
                return
            # Print answer
            return answer.content

    def understand_audio(self, say_it=True):
        """Http NLU audio method"""
        self.logger.info("understand_audio")
        # Create transmission for NLU audio
        content = {"arugments": {"say_it": say_it}}
        tmn = self.create_transmission("understand_audio", "brain.understand_audio", content)
        # Wait for transmission answer
        answer = self.wait_for_answer(tmn.id_)
        return answer.content

    def understand_text(self, text, say_it=False):
        """Http NLU text method"""
        self.logger.info("understand_text: %s", text)
        # Create transmission for NLU text
        content = {"arguments": {"text": text}}
        tmn = self.create_transmission("understand_text", "brain.understand_text", content)
        # Wait for transmission answer
        answer = self.wait_for_answer(tmn.id_)

        # Check if we got an answer
        if answer is None:
            self.logger.warning("No answer for tmn_id: %s", tmn.id_)
            return
        confidence = answer.content.get('attributes', {}).get('confidence')
        # Check confidence
        if confidence is None:
            self.logger.warning("No answer for tmn_id: %s", tmn.id_)
            return
        elif confidence < 0.8:
            self.logger.info("Text NOT understood fo tmn_id: %s", tmn.id_)
            return
        elif confidence < 0.6:
            self.logger.info("Text NOT understood fo tmn_id: %s", tmn.id_)
            return
        # Run the capacity of the NLU answer
        destination = "{module}.{capacity}".format(**answer.content.get('attributes'))
        new_content = {"attributes": answer.content.get('attributes', {}).get("arguments", {})}
        # Create transmission
        tmn = self.create_transmission("understand_text", destination, new_content)
        # Wait for transmission answer
        answer = self.wait_for_answer(tmn.id_)
        # Check if we got an answer
        if answer is None:
            self.logger.warning("No answer for tmn_id: %s", tmn.id_)
            return
        # Say it
        # TODO replace text by tts
        if say_it and "text" in answer.content.get("attributes", {}):
            new_content = {"attributes": {"text": answer.content.get("attributes").get("text")}}
            tmn = self.create_transmission("understand_text", "aptitudes.speak.say", new_content)
            # Wait for transmission answer
            self.wait_for_answer(tmn.id_)
        # return answer
        return answer.content
