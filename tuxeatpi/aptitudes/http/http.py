"""Web Rest API TuxDroid aptitude module"""

import hug

from gunicorn.app.base import BaseApplication
from gunicorn.six import iteritems

from tuxeatpi.aptitudes.common import SubprocessedAptitude
from tuxeatpi.aptitudes.http import static


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
        # -XPOST -d '{"command": "aptitudes.being.get_name" , "arguments": {}}'
        # http://127.0.0.1:8000/order
        @hug.post('/order')
        def order(command, arguments=None, block=True):  # pylint: disable=W0612
            """order route"""
            if arguments is None:
                arguments = {}
            return self.order(command, arguments, block)

        @hug.extend_api('/ui')
        def ui_routes():
            """Import all static routes"""
            return [static]

        # Settings
        @hug.get('/settings', requires=cors_support)
        def settings_get():  # pylint: disable=W0612
            """get settings route"""
            self._tuxdroid.settings.reload()
            return {"result": dict(self._tuxdroid.settings)}

        @hug.options('/settings', requires=cors_support)
        def settings_options():
            return

        @hug.post('/settings', requires=cors_support)
        def settings_set(settings):  # pylint: disable=W0612
            """get settings route"""
            # new settings
            self.logger.debug("New settings received %s", settings)
            # save settings
            ret = self._tuxdroid.update_setting(settings)
            # TODO handle error
            return {"state": ret, "result": dict(self._tuxdroid.settings)}

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


def cors_support(response, *args, **kwargs):
    """Add cors support"""
    # TODO clean useless
    response.set_header('Access-Control-Allow-Origin', '*')
    response.set_header('Access-Control-Allow-Methods', 'GET, POST, PATCH, PUT, DELETE, OPTIONS')
    response.set_header('Access-Control-Allow-Credentials', 'true')
    headers = ["Accept-Encoding",
            "Accept-Language",
            "Access-Control-Request-Headers",
            "Access-Control-Request-Method",
            "Authorization",
            "Cache-Control",
            "Client-Offset",
            "Connection",
            "Content-Type",
            "Host",
            "Lang",
            "Origin"
            "Pragma",
            "Referer",
            "Token",
            "User-Agent",
            "X-Requested-With",
           ]
    response.set_header('Access-Control-Allow-Headers', ', '.join(headers))
