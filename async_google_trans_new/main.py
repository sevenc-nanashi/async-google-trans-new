import asyncio
import json
import logging
import random
import re
from typing import Union
from urllib.parse import quote

import aiohttp
import aiohttp.web_exceptions
import urllib3
from debtcollector import moves

from .constant import DEFAULT_SERVICE_URLS, LANGUAGES

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URLS_SUFFIX = [re.search('translate.google.(.*)', url.strip()).group(1) for url in DEFAULT_SERVICE_URLS]
URL_SUFFIX_DEFAULT = 'com'


class TransError(Exception):
    """Exception that uses context to present a meaningful error message"""

    def __init__(self, msg=None, **kwargs):
        self.tts = kwargs.pop('tts', None)
        self.rsp = kwargs.pop('response', None)
        if msg:
            self.msg = msg
        elif self.tts is not None:
            self.msg = self.infer_msg(self.tts, self.rsp)
        else:
            self.msg = None
        super(TransError, self).__init__(self.msg)

    def infer_msg(self, tts, rsp=None):
        cause = "Unknown"

        if rsp is None:
            premise = "Failed to connect"

            return "{}. Probable cause: {}".format(premise, "timeout")
            # if tts.tld != 'com':
            #     host = _translate_url(tld=tts.tld)
            #     cause = "Host '{}' is not reachable".format(host)

        else:
            status = rsp.status_code
            reason = rsp.reason

            premise = "{:d} ({}) from TTS API".format(status, reason)

            if status == 403:
                cause = "Bad token or upstream API changes"
            elif status == 200 and not tts.lang_check:
                cause = "No audio stream in response. Unsupported language '%s'" % self.tts.lang
            elif status >= 500:
                cause = "Uptream API error. Try again later."

        return "{}. Probable cause: {}".format(premise, cause)


class InvalidLanguageCode(Exception):
    pass


class AsyncTranslator:
    '''
    You can use 108 language in target and source, details view LANGUAGES.
    Target language: like 'en', 'zh', 'th'...

    :param url_suffix: The source text(s) to be translated. Batch translation is supported via sequence input.
                       The value should be one of the url_suffix listed in : `DEFAULT_SERVICE_URLS`
    :type url_suffix: UTF-8 :class:`str`; :class:`unicode`; string sequence (list, tuple, iterator, generator)

    :param timeout: Timeout Will be used for every request.
    :type timeout: int

    :param proxies: proxies Will be used for every request.
    :type proxies: :class:`dict`; like: {'http': 'http:171.112.169.47:19934/', 'https': 'https:171.112.169.47:19934/'}

    :param code_sensitive: Raise exception when invalid language code passed or not.
    :type code_sensitive: :class:`bool`;

    :param return_list: Return List when multiple results returned or not.
    :type return_list: :class:`bool`;
    '''

    def __init__(self, url_suffix="cn", timeout=5, proxies=None, code_sensitive=False, return_list=True):
        self.proxies = proxies
        if url_suffix not in URLS_SUFFIX:
            self.url_suffix = URL_SUFFIX_DEFAULT
        else:
            self.url_suffix = url_suffix
        url_base = "https://translate.google.{}".format(self.url_suffix)
        self.url = url_base + "/_/TranslateWebserverUi/data/batchexecute"
        self.timeout = timeout
        self.__session = aiohttp.ClientSession()
        self._requests = []
        self.code_sensitive = code_sensitive
        self.return_list = return_list

    def _package_rpc(self, text, lang_src='auto', lang_tgt='auto'):
        GOOGLE_TTS_RPC = ["MkEWBc"]
        parameter = [[text.strip(), lang_src, lang_tgt, True], [1]]
        escaped_parameter = json.dumps(parameter, separators=(',', ':'))
        rpc = [[[random.choice(GOOGLE_TTS_RPC), escaped_parameter, None, "generic"]]]
        espaced_rpc = json.dumps(rpc, separators=(',', ':'))
        # text_urldecode = quote(text.strip())
        freq_initial = "f.req={}&".format(quote(espaced_rpc))
        freq = freq_initial
        return freq

    @property
    def _session(self):
        if self.__session.closed:
            self.__session = aiohttp.ClientSession()
        return self.__session

    async def translate(self, text: str, lang_tgt: str = 'auto', lang_src: str = 'auto', pronounce: bool = False) -> Union[str, list]:
        """
        Translates text.

        :param text: The source text(s) to be translated. Can only detect less than 5000 characters.
        :type text: UTF-8 :class:`str`; :class:`unicode`;

        :param lang_tgt: The language to translate the source text into.
                        The value should be one of the language codes listed in : `LANGUAGES`
        :type lang_tgt: :class:`str`; :class:`unicode`;

        :param lang_src: The language of the source text.
                        The value should be one of the language codes listed in :const:`googletrans.LANGUAGES`
                        If a language is not specified,
                        the system will attempt to identify the source language automatically.
        :type lang_src: :class:`str`; :class:`unicode`;

        :param pronounce: Return pronounce or not.
        :type pronounce: :class:`bool`;

        :return: Translated text or list.
        :rtype: Union[str, list]
        """
        try:
            try:
                LANGUAGES[lang_src]
            except KeyError:
                if self.code_sensitive:
                    raise InvalidLanguageCode(f"Invalid language code passed ({lang_src})")
                lang_src = 'auto'
            try:
                LANGUAGES[lang_tgt]
            except KeyError:
                if self.code_sensitive:
                    raise InvalidLanguageCode(f"Invalid language code passed ({lang_tgt})")
                lang_tgt = 'auto'
            text = str(text)
            if len(text) >= 5000:
                return "Warning: Can only translate less than 5000 characters"
            if len(text) == 0:
                return ""
            headers = {
                "Referer": "http://translate.google.{}/".format(self.url_suffix),
                "User-Agent":
                    "Mozilla/5.0 (Windows NT 10.0; WOW64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/47.0.2526.106 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
            }
            freq = self._package_rpc(text, lang_src, lang_tgt)

            try:
                if self.proxies is None or not isinstance(self.proxies, dict):
                    self.proxies = {}
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                s = self._session.post(url=self.url,
                                       data=freq,
                                       headers=headers,
                                       verify_ssl=False,
                                       timeout=timeout
                                       )
                s.proxy = self.proxies.get("https")

                async with s as r:
                    resp = await r.text()

                for line in (resp).splitlines():
                    if "MkEWBc" in line:
                        try:
                            response = line
                            response = json.loads(response)
                            response = list(response)
                            response = json.loads(response[0][2])
                            response_ = list(response)
                            response = response_[1][0]
                            if len(response) == 1 or not self.return_list:
                                if len(response[0]) > 5:
                                    sentences = response[0][5]
                                else:  # only url
                                    sentences = response[0][0]
                                    if pronounce is False:
                                        return sentences
                                    elif pronounce is True:
                                        return [sentences, None, None]
                                translate_text = ""
                                for sentence in sentences:
                                    sentence = sentence[0]
                                    translate_text += sentence.strip() + ' '
                                translate_text = translate_text
                                if pronounce is False:
                                    return translate_text
                                elif pronounce is True:
                                    pronounce_src = (response_[0][0])
                                    pronounce_tgt = (response_[1][0][0][1])
                                    return [translate_text, pronounce_src, pronounce_tgt]
                            elif len(response) == 2:
                                sentences = []
                                for i in response:
                                    sentences.append(i[0])
                                if pronounce is False:
                                    return sentences
                                elif pronounce is True:
                                    pronounce_src = (response_[0][0])
                                    pronounce_tgt = (response_[1][0][0][1])
                                    return [sentences, pronounce_src, pronounce_tgt]
                        except Exception as e:
                            raise e
                r.raise_for_status()
                await s.close()
            except TimeoutError as e:
                raise e
            except aiohttp.web_exceptions.HTTPError:
                # Request successful, bad response
                raise TransError(tts=self, response=r)
            except aiohttp.ClientConnectorError:
                # Request failed
                raise TransError(tts=self)
        except Exception as e:
            await s.close()
            raise e

    async def detect(self, text):
        """
        Detects language of text.

        :param text: The source text(s) to be detectd. Can only detect less than 5000 characters.
        :type text: UTF-8 :class:`str`; :class:`unicode`;

        :return: Language code of text.
        :rtype: str
        """
        try:
            text = str(text)
            if len(text) >= 5000:
                return log.debug("Warning: Can only detect less than 5000 characters")
            if len(text) == 0:
                return ""
            headers = {
                "Referer": "http://translate.google.{}/".format(self.url_suffix),
                "User-Agent":
                    "Mozilla/5.0 (Windows NT 10.0; WOW64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/47.0.2526.106 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
            }
            freq = self._package_rpc(text)
            if self.proxies is None or not isinstance(self.proxies, dict):
                self.proxies = {}
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            try:
                s = self._session.post(url=self.url,
                                       data=freq,
                                       headers=headers,
                                       verify_ssl=False,
                                       timeout=timeout
                                       )
                s.proxy = self.proxies.get("https")

                async with s as r:
                    resp = await r.text()
                for line in (resp).splitlines():
                    if "MkEWBc" in line:
                        # regex_str = r"\[\[\"wrb.fr\",\"MkEWBc\",\"\[\[(.*).*?,\[\[\["
                        try:
                            # data_got = re.search(regex_str,line).group(1)
                            response = line
                            response = json.loads(response)
                            response = list(response)
                            response = json.loads(response[0][2])
                            response = list(response)
                            detect_lang = response[0][2]
                        except Exception:
                            raise Exception
                        # data_got = data_got.split('\\\"]')[0]
                        return [detect_lang, LANGUAGES[detect_lang.lower()]]
                r.raise_for_status()
                await s.close()
            except TimeoutError as e:
                raise e
            except aiohttp.web_exceptions.HTTPError:
                # Request successful, bad response
                raise TransError(tts=self, response=r)
            except aiohttp.ClientConnectorError:
                # Request failed
                raise TransError(tts=self)
        except Exception as e:
            await s.close()
            raise e

    async def close(self):
        await self.__session.close()

    def __del__(self):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.create_task(self.__session.close())


google_translator = moves.moved_class(AsyncTranslator, 'google_translator', __name__)
google_new_transError = moves.moved_class(TransError, 'google_new_transError', __name__)
