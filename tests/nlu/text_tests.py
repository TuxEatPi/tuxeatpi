from io import StringIO
from multiprocessing import Queue
import logging
import sys
import time
import unittest

from tuxeatpi.actionner.actionner import Actionner
from tuxeatpi.tux import Tux
from tuxeatpi.libs.settings import Settings
from tuxeatpi.nlu.text import NLUText


from unittest.mock import MagicMock, Mock, patch


def toto():
    print("QQQQEEEEEEEEEEEEEEEE")
sys.modules['get_event_loop'] = toto
#from tuxeatpi.nlu.common import WebsocketConnection, NLUBase, get_event_loop

import threading
import aiohttp
import asyncio
class MyLoop1(asyncio.AbstractEventLoop):
    def run_until_complete(self, *args, **kwargs):
        return {'nlu_interpretation_results': {'payload': {'interpretations': [{'literal': 'What is your name', 'action': {'intent': {'value': 'tux__get_name', 'confidence': 1.0}}}]}}}


class MyLoop2(asyncio.AbstractEventLoop):
    def run_until_complete(self, *args, **kwargs):
        return {'nlu_interpretation_results': {'payload': {'interpretations': [{'literal': 'What is your name', 'action': {'intent': {'value': 'tux__get_name', 'confidence': 0.7}}}]}}}


class MyLoop3(asyncio.AbstractEventLoop):
    def run_until_complete(self, *args, **kwargs):
        return {'nlu_interpretation_results': {'payload': {'interpretations': [{'literal': 'What is your name', 'action': {'intent': {'value': 'NO_MATCH', 'confidence': 1.0}}}]}}}


class MyLoop4(asyncio.AbstractEventLoop):
    def run_until_complete(self, *args, **kwargs):
        return {'nlu_interpretation_results': {'payload': {'interpretations': [{'literal': 'What is your name', 'action': {'intent': {'value': 'badintent', 'confidence': 1.0}}}]}}}


class NLUTextTests(unittest.TestCase):
    myloop1 = MyLoop1()
    myloop2 = MyLoop2()
    myloop3 = MyLoop3()
    myloop4 = MyLoop4()

    @patch('asyncio.get_event_loop', MagicMock(return_value=myloop1))
    def test_nlutext_1_0(self):
        """NLU text with 1.0 confidence Tests"""
        logger = logging.getLogger(name="TestLogger")
        conf_file = "tests/tux/conf/tux_tests_conf_1.yaml"
        settings = Settings(conf_file, logger)
        # Get actionner object
        action_queue = Queue()
        nlu_queue = Queue()
        tts_queue = Queue()
        nlu_text = NLUText(settings,  action_queue, nlu_queue, tts_queue, logger)
        t = threading.Timer(4, nlu_text.stop, [])
        t.start()
        t = threading.Timer(2, nlu_queue.put, [(False, "What is your name ?")])
        t.start()
        nlu_text.run()

    @patch('asyncio.get_event_loop', MagicMock(return_value=myloop2))
    def test_nlutext_0_7(self):
        """NLU text with 0.7 confidence Tests"""
        logger = logging.getLogger(name="TestLogger")
        conf_file = "tests/tux/conf/tux_tests_conf_1.yaml"
        settings = Settings(conf_file, logger)
        # Get actionner object
        action_queue = Queue()
        nlu_queue = Queue()
        tts_queue = Queue()
        nlu_text = NLUText(settings,  action_queue, nlu_queue, tts_queue, logger)
        t = threading.Timer(4, nlu_text.stop, [])
        t.start()
        t = threading.Timer(2, nlu_queue.put, [(False, "What is your name ?")])
        t.start()
        nlu_text.run()


    @patch('asyncio.get_event_loop', MagicMock(return_value=myloop3))
    def test_nlutext_nomatch(self):
        """NLU text with nomatch confidence Tests"""
        logger = logging.getLogger(name="TestLogger")
        conf_file = "tests/tux/conf/tux_tests_conf_1.yaml"
        settings = Settings(conf_file, logger)
        # Get actionner object
        action_queue = Queue()
        nlu_queue = Queue()
        tts_queue = Queue()
        nlu_text = NLUText(settings,  action_queue, nlu_queue, tts_queue, logger)
        t = threading.Timer(4, nlu_text.stop, [])
        t.start()
        t = threading.Timer(2, nlu_queue.put, [(False, "What is your name ?")])
        t.start()
        nlu_text.run()


    @patch('asyncio.get_event_loop', MagicMock(return_value=myloop4))
    def test_nlutext_badintent (self):
        """NLU text with badintent Tests"""
        logger = logging.getLogger(name="TestLogger")
        conf_file = "tests/tux/conf/tux_tests_conf_1.yaml"
        settings = Settings(conf_file, logger)
        # Get actionner object
        action_queue = Queue()
        nlu_queue = Queue()
        tts_queue = Queue()
        nlu_text = NLUText(settings,  action_queue, nlu_queue, tts_queue, logger)
        t = threading.Timer(4, nlu_text.stop, [])
        t.start()
        t = threading.Timer(2, nlu_queue.put, [(False, "What is your name ?")])
        t.start()
        nlu_text.run()


#        return {'message': 'query_response', 'transaction_id': 123, 'NMAS_PRFX_TRANSACTION_ID': '123', 'final_response': 1, 'result_type': 'NDSP_APP_CMD', 'result_format': 'nlu_interpretation_results', 'nlu_interpretation_results': {'status': 'success', 'final_response': 1, 'payload_version': '1.0', 'payload_format': 'nlu-base', 'payload': {'interpretations': [{'literal': 'Quel est ton nom', 'action': {'intent': {'value': 'tux__get_name', 'confidence': 1.0}}}], 'type': 'nlu-1.0', 'diagnostic_info': {'nlps_profile_package': 'QUICKNLU', 'adk_dialog_manager_status': 'undefined', 'nlps_profile': 'QUICKNLUDYN', 'third_party_delay': '0', 'ext_map_time': '0', 'nlps_profile_package_version': 'nlps(z):6.2.200.13.1-B258', 'nlu_annotator': 'com.nuance.QUICKNLU.quicknlu.Client', 'fieldId': 'dm_main', 'int_map_time': '0', 'context_tag': 'master', 'nlps_version': 'nlps(z):6.2.200.13.1-B258;Version: nlps-base-Zeppelin-6.2.200-B87-GMT20160708224223;', 'nlu_version': '[Version: nlps-fra-FRA-QUICKNLU;Label;3527_NLPS_5;Model;2994b62f-6984-11e6-9cbe-49366b49eae8;Build;5cc9c3e6-730b-11e6-9cbe-cbdea37b47dd;QnluTrain;1.14.5;CreatedAt;2016-09-05T01:52:03.000Z]', 'nmaid': 'NMDPTRIAL_thibault_cohen_nuance_com20150916110537', 'nlu_component_flow': '[Input:TextProcJSON] [NLUlib|C-ising-r$Rev$.f20160617.1703] [Flow|GramURI:/opt/nuance/ncs/nlps-uima-as/datapacks/nlps-nlu/nlps-QUICKNLU/8650//8650/NMDPTRIAL_thibault_cohen_nuance_com20150916110537_master_fra-FRA/5cc9c3e6-730b-11e6-9cbe-cbdea37b47dd/UIMA//trainedInnerGrammar.filter.gram] [Input:TextProcJSON] [NLUlib|C-ising-r$Rev$.f20160617.1703] [Flow|GramURI:/opt/nuance/ncs/nlps-uima-as/datapacks/nlps-nlu/nlps-QUICKNLU/8650//8650/NMDPTRIAL_thibault_cohen_nuance_com20150916110537_master_fra-FRA/5cc9c3e6-730b-11e6-9cbe-cbdea37b47dd/UIMA//trainedInnerGrammar.filter.gram]', 'application': 'NMDPTRIAL_thibault_cohen_nuance_com20150916110537', 'nlu_language': 'fra-FRA', 'qws_project_id': 'b4d065c537ea596e0a8b62c2fcd1bf45b92b1b27c9a5446b', 'nlps_host': 'nlps-dy-qnlu-pool-1-12e1cdd74ad91b2674535fdc6579efc8-3227i:8636', 'nlps_ip': '172.17.7.7', 'nlu_use_literal_annotator': '0', 'nlps_nlu_type': 'quicknludynamic'}}}, 'NMAS_PRFX_SESSION_ID': '6cf6f736-64a8-4f5f-adaf-a148e04a0057'}
