"""Aptitude module for Natural language understanding"""

import logging

from tuxeatpi.aptitudes.common import ThreadedAptitude, capability, can_transmit, threaded, SubprocessedAptitude, subprocessed
from tuxeatpi.aptitudes.nlu.text import nlu_text
from tuxeatpi.aptitudes.nlu.audio import nlu_audio
from tuxeatpi.libs.lang import gtt

CONFIDENCE_THRESHOLD = 0.7

class Nlu(SubprocessedAptitude):
    """Natural language understanding aptitude"""

    def __init__(self, tuxdroid):
        SubprocessedAptitude.__init__(self, tuxdroid)

    def run(self):
        SubprocessedAptitude.run(self)

    def help_(self):
        """Return aptitude help"""
        return gtt("Understand text and voice")

    @capability(gtt("Understand what you're saying"))
    @can_transmit
    def audio(self, do_it=True, say_it=True):
        """Listen and understand sound from mic"""
        logger = logging.getLogger(name="tep").getChild("aptitudes").\
            getChild("nlu").getChild("audio")
        logger.info("NLU audio starting")
        nlu_return = nlu_audio(self.settings)
        # Parse result
        result = self._handle_nlu_return(nlu_return)
        # Handle result error
        if result.get("error", "") != "":
            if result.get("tts") != "":
                content = {"arguments": {"tts": result.get("tts")}}
                tmn = self.create_transmission("text", "aptitudes.speak.say", content)
                # wait for end of speak
                self.wait_for_answer(tmn.id_)
            return result
        elif result.get("need_confirmation", "False"):
            content = {"arguments": {"tts": result.get("tts")}}
            tmn = self.create_transmission("text", "aptitudes.speak.say", content)
            # wait for end of speak
            self.wait_for_answer(tmn.id_)
            return result
        else:
            if isinstance(result, dict):
                result = self._do_and_say_it(result, do_it, say_it)
            logger.info("NLU audio ending")
            return result

    @capability(gtt("Understand text"))
#    @threaded
#    @subprocessed
    @can_transmit
    def text(self, text, do_it=False, say_it=False):
        """Read and understand text"""
        logger = logging.getLogger(name="tep").getChild("aptitudes").\
            getChild("nlu").getChild("text")
        logger.info("NLU audio ending")
        nlu_return = nlu_text(self.settings, text)
        # Parse result
        result = self._handle_nlu_return(nlu_return)
        # Handle result error
        if result.get("error", "") != "":
            if result.get("tts") != "":
                content = {"arguments": {"tts": result.get("tts")}}
                tmn = self.create_transmission("text", "aptitudes.speak.say", content)
                # wait for end of speak
                self.wait_for_answer(tmn.id_)
            return result
        elif result.get("need_confirmation", "False"):
            content = {"arguments": {"tts": result.get("tts")}}
            tmn = self.create_transmission("text", "aptitudes.speak.say", content)
            # wait for end of speak
            self.wait_for_answer(tmn.id_)
            return result
        else:
            if isinstance(result, dict):
                result = self._do_and_say_it(result, do_it, say_it)
            logger.info("NLU audio ending")
            return result



        # TODO handle low confidence
        result = self._handle_nlu_return(nlu_return)
        if isinstance(result, dict):
            result = self._do_and_say_it(result, do_it, say_it)
        logger.info("NLU text ending")
        return result

    def _do_and_say_it(self, result, do_it, say_it):
        """Do the understood action and say the answer"""
        if do_it is True:
            # Do it
            destination = "{}.{}".format(result.get("result", {}).get("module"),
                                         result.get("result", {}).get("capacity"))
            content = {"arguments": result.get("result", {}).get('arguments', {})}
            tmn = self.create_transmission("text", destination, content)
            answer = self.wait_for_answer(tmn.id_)
            # Check if we got an answer
            if answer is None:
                self.logger.warning("No answer for tmn_id: %s", tmn.id_)
                return
            if say_it is True and answer.content.get("tts"):
                # Say it
                content = {"arguments": {"tts": answer.content.get("tts")}}
                tmn = self.create_transmission("text", "aptitudes.speak.say", content)
                # wait for end of speak
                self.wait_for_answer(tmn.id_)
            # Print answer
            return answer.content
        return result

    def _handle_nlu_return(self, nlu_return):
        """Handle nlu return by parsing result and formatting result
        to be transmission ready
        """
        result = {"module": None,
                  "capacity": None,
                  "arguments": None,
                  "confidence": None,
                  "need_confirmation": False,
                  "error": None,
                  }
        interpretations = nlu_return.get("nlu_interpretation_results", {}).\
            get("payload", {}).get("interpretations", {})
        # TODO: what about if len(interpretations) > 1 ??
        self.logger.info("Nb interpretations: %s", len(interpretations))
        for interpretation in interpretations:
            intent = interpretation.get("action", {}).get("intent", {})
            self.logger.info("Intent: %s", intent.get("value"))
            result['confidence'] = intent.get("confidence")
            self.logger.info("Confidence: %s", result["confidence"])
            # Get concepts
            arguments = {}
            for name, data in interpretation.get("concepts", {}).items():
                arguments[name] = data[0].get('value')
            self.logger.info("Arguments: %s", arguments)
            # TODO log arguments
            if intent.get("value") == "NO_MATCH":
                # I don't understand :/
                # TODO improve me
                self.logger.critical("No intent matched")
                result['error'] = "no intent matched"
                tts = gtt("Sorry, I don't get it")
                return {"result": result, "tts": tts}

            # Check intent
            if len(intent.get("value").rsplit("__", 1)) != 2:
                # TODO improve me
                self.logger.critical("BAD Intent name: {}".format(intent.get("value")))
                result['error'] = "bad intent name - trsx files must me fixed"
                tts = gtt("Sorry, I don't get it")
                return {"result": result, "tts": tts}

            module, capacity = intent.get("value").rsplit("__", 1)
            result['module'] = module.replace("__", ".")
            result['capacity'] = capacity
            result['arguments'] = arguments
            result['confidence'] = intent.get("confidence")
            if intent.get("confidence") < CONFIDENCE_THRESHOLD:
                # TODO improve me
                # I'm not sure to understand :/
                self.logger.info("Module: %s", module)
                self.logger.info("Capacity: %s", capacity)
                self.logger.info("Need confirmation - confidence: %s", result['confidence'])
                result['need_confirmation'] = True
                tts = gtt("I'm not sure to understand, could you repeat please ?")
                return {"result": result, "tts": tts}

            # Return result
            error = result.pop("error")
            if error:
                return {"error": error, "result": result}
            return {"result": result}
