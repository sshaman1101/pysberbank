#coding=utf8
# pysberbank 10.11.14 8:32 by mnach #
import datetime
from enum import Enum
import json
import logging
import urllib.request
import urllib.parse
import urllib.error
logger = logging.getLogger(__name__)

__author__ = 'Mikhail Nacharov'
__version__ = '0.0.1.dev1'
__author_email__ = 'mnach@ya.ru'

class SberError(Exception): pass

class SberNetworkError(SberError): pass

class SberRequestError(SberError):
    def __init__(self, request, code, desc):
        self.request = request
        self.code = code
        self.desc = desc
        super(SberRequestError, self).__init__('{0.request} error {0.code}: {0.desc}'.format(self))


class SberWrapper(object):
    """
    Sberbank acquiring API wrapper
    """
    class PageType(Enum):
        DESKTOP = 1
        MOBILE = 2

    rest_urls = dict(
        # register order in sberbank
        register='https://3dsec.sberbank.ru/payment/rest/register.do',
	# register order in sberbank (for 2 steps payments with hold mode)
        registerPreAuth='https://3dsec.sberbank.ru/payment/rest/registerPreAuth.do',
        # get order status
        status='https://3dsec.sberbank.ru/payment/rest/getOrderStatus.do',
        # get order extended status
        status_ext='https://3dsec.sberbank.ru/payment/rest/getOrderStatusExtended.do',
        # refund order
        refund='https://3dsec.sberbank.ru/payment/rest/refund.do'
    )
    soap_urls = dict(

    )

    def __init__(self, username: str, password: str, soap: bool=False, post: bool=True, urls: dict=None):
        """
        :param username: Store username
        :param password: Store password
        :param use_soap: use soap api instead of REST
        :param post: use POST request not GET
        :param urls: dict of urls where requests will be sent
        """
        self._username = username
        self._password = password

        self.soap = soap
        self.post = post
        if self.soap and not self.post:
            raise ValueError("Soap request must be send by POST request")
        self.urls = urls or (self.soap_urls if self.soap else self.rest_urls)

    def _request(self, url, params):
        if self.soap:
            # todo: Soap implementation
            raise NotImplementedError("SOAP haven't implemented yet")
        logger.debug('Request  is {0!r}'.format(params))

        try:
            if self.post:
                request = urllib.request.Request(url)
                # adding charset parameter to the Content-Type header.
                request.add_header("Content-Type","application/x-www-form-urlencoded;charset=utf-8")
                data = urllib.parse.urlencode(params)
                data = data.encode('utf-8')
                response = urllib.request.urlopen(request, data)
            else:
                response = urllib.request.urlopen('{0}?{1}'.format(url, urllib.parse.urlencode(params)))
        except urllib.error.HTTPError as e:
            exception_body = ''
            try:
                exception_body = e.fp.read()
            except: pass
            logger.error('Sberbank REST-server return wrong status {0.code}: {0.msg}'.format(e), exc_info=True,
                         extra={'response': exception_body})
            raise SberNetworkError

        except urllib.error.URLError as e:
            logger.warning('Error {0!r} happened during processing request'.format(e), exc_info=True)
            raise SberNetworkError

        logger.debug('Response is {0.status} {0._method} {0.reason} {headers}'.format(response, headers=response.getheaders()))
        response_body = response.read()
        logger.debug('Response body is {0!r}'.format(response_body))
        if response_body is None:
            logger.error('Sberbank REST-server return empty reply with HTTPCode={0}'.format(response.status))
            raise SberNetworkError

        response_dict = json.loads(response_body.decode('utf8'), encoding='utf8')
        logger.debug('Unmarshaled response  is {0!r}'.format(response_dict))
        return response_dict

    def register(self, order: str, amount: int, success_url: str, currency: int=643, fail_url: str=None,
                 is_pre_auth: bool=False, description: str='', language: str='RU', page_type: PageType=PageType.DESKTOP,
		 clinet_id: str=None, session_timeout: int=1200, expiration: datetime.date=None, extra: dict=None):
        """
        Register request in acquiring system
        :param order: order id in the store
        :param amount: Order amount in minimal unit of currency(penny / kopeck)
        :param success_url: Send user to this URL after success of payment
        :param currency: Currency code in ISO 4217
        :param fail_url: Send user to this URL after failure of payment
        :param is_pre_auth: If True, activates hold mode (2-step payments processing), default False
	:param description: order description in free text format
        :param language: Acquiring page language
        :param page_type: Is it mobile or desctop user ?
        :param clinet_id: Client id in the store
        :param session_timeout: The duration of the session, in seconds
        :param expiration: Order lifetime. It will be (<now>+session_timeout) if None
        :param extra: some extra params to store in the system
        :return: (order_id, form_url)
        """
        # 1. preparing data to request
        url = self.urls['register']
	if is_pre_auth:
            url = self.urls['registerPreAuth']
        request = dict(
            # Логин магазина, полученный при подключении
            userName=self._username,
            # Пароль магазина, полученный при подключении
            password=self._password,
            # Номер (идентификатор) заказа в системе магазина
            orderNumber=order,
            # Сумма платежа в минимальных единицах валюты(копейки).
            amount=amount,
            # *Код валюты платежа ISO 4217.
            currency=currency,
            # Адрес, на который надо перенаправить пользователя в случае успешной оплаты
            returnUrl=success_url,
            # *Язык в кодировке ISO 639-1.
            language=language,
             # В pageView передаётся признак - мобильное устройство: MOBILE или DESKTOP
            pageView=page_type.name,
            # *Продолжительность сессии в секундах. default=1200
            sessionTimeoutSecs=session_timeout,
        )
        if fail_url:
            # *Адрес, на который надо перенаправить пользователя в случае неуспешной оплаты
            request['failUrl'] = fail_url
        if description:
             # *Описание заказа в свободной форме
            request['description'] = description
        if clinet_id:
            # *Номер (идентификатор) клиента в системе магазина
            request['clientId'] = clinet_id
        if extra:
            # *Поля дополнительной информации для последующего хранения
            request['jsonParams'] = extra
        if expiration:
            # *Время жизни заказа. Если не задано вычисляется по sessionTimeoutSecs
            request['expirationDate'] = expiration.isoformat().split('.')[0]

        # 2. send request to the server
        try:
            response = self._request(url, request)
        except SberError:
            raise
        except Exception as e:
            raise SberError(e)

        # 3. processing reply
        if 'errorCode' in response and response.get('errorCode') != '0':
            raise SberRequestError('register', response['errorCode'],
                                   response.get('errorMessage', 'Description not presented'))
        if 'orderId' not in response or 'formUrl' not in response:
            raise SberNetworkError('Service temporary unavailable')
        return response['orderId'], response['formUrl']

    def status(self, order_id: str, language: str='RU'):
        """
        Get order status
        :param order_id: order UID
        :param language: Acquiring page language
        :return: <dict> order data
        """
        # 1. preparing data to request
        url = self.urls['status']
        request = dict(
            userName=self._username,
            password=self._password,
            # Номер заказа в платежной системе. Уникален в пределах системы.
            orderId=order_id,
            # Язык в кодировке ISO 639-1. Если не указан, считается, что язык – русский.
            language=language
        )

        # 2. send request to the server
        try:
            response = self._request(url, request)
        except SberError:
            raise
        except Exception as e:
            raise SberError(e)

        # 3. processing reply
        if 'ErrorCode' in response and response.get('ErrorCode') != '0':
            raise SberRequestError('status', response['ErrorCode'],
                                   response.get('ErrorMessage', 'Description not presented'))
        return response

    def status_ext(self, order_id: str, language: str='RU'):
        """
        Get order status
        :param order_id: order UID
        :param language: Acquiring page language
        :return: <dict> order data
        """
        # 1. preparing data to request
        url = self.urls['status_ext']
        request = dict(
            userName=self._username,
            password=self._password,
            # Номер заказа в платежной системе. Уникален в пределах системы.
            orderId=order_id,
            # Язык в кодировке ISO 639-1. Если не указан, считается, что язык – русский.
            language=language
        )

        # 2. send request to the server
        try:
            response = self._request(url, request)
        except SberError:
            raise
        except Exception as e:
            raise SberError(e)

        # 3. processing reply
        if 'errorCode' in response and response.get('errorCode') != '0':
            raise SberRequestError('status_ext', response['errorCode'],
                                   response.get('errorMessage', 'Description not presented'))
        return response

    def refund(self, order_id: str, amount: int, language: str='RU'):
        """
        Refund order and send <amount> back to user credit card
        :param order_id: Sberbank order UID
        :param amount: Order amount in minimal unit of currency(penny / kopeck)
        :param language: Acquiring page language
        :return: Sberbank status text
        """
        # 1. preparing data to request
        url = self.urls['refund']
        request = dict(
            userName=self._username,
            password=self._password,
            # Номер заказа в платежной системе. Уникален в пределах системы.
            orderId=order_id,
            # Сумма платежа в копейках (или центах)
            amount=amount,
            # Язык в кодировке ISO 639-1. Если не указан, считается, что язык – русский.
            language=language
        )

        # 2. send request to the server
        try:
            response = self._request(url, request)
        except SberError:
            raise
        except Exception as e:
            raise SberError(e)

        # 3. processing reply
        if 'errorCode' in response and response.get('errorCode') != '0':
            raise SberRequestError('refund', response['errorCode'],
                                   response.get('errorMessage', 'Description not presented'))
        return response.get('errorMessage', 'OK')
