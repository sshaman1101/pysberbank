#coding=utf8
# pysberbank 07.11.14 10:50 by mnach #
import datetime
import getpass
import json
import random
import string
import unittest
import urllib
import urllib.request
import urllib.parse
import logging
from os import path
import sys

logger = logging.getLogger(__name__)


class Credentials:
    """Класс для сохранения данных о пользователе и пароле"""
    username = password = ''

    @staticmethod
    def setUp():
        username = next((p for p in sys.argv if p.startswith('--username=')), None)
        if username:
            Credentials.username = sys.argv.pop(sys.argv.index(username))[len('--username='):]
        password = next((p for p in sys.argv if p.startswith('--password=')), None)
        if password:
            Credentials.password = sys.argv.pop(sys.argv.index(password))[len('--password='):]
        if not Credentials.username:
            sys.stdout.write('You need to specify sberbank API username for testing > ')
            Credentials.username = input()
        if not Credentials.password:
            Credentials.password = getpass.getpass('You need to specify sberbank API password for testing > ')


class RestTestCase(unittest.TestCase):

    def setUp(self):
        self.urls = dict(
            # Регистрация заказа
            register='https://3dsec.sberbank.ru/payment/rest/register.do',
            # Получение статуса заказа
            status='https://3dsec.sberbank.ru/payment/rest/getOrderStatus.do',
            # Получение статуса заказа -- расширенное
            status_ext='https://3dsec.sberbank.ru/payment/rest/getOrderStatusExtended.do',
            # Регистрация заказа с предавторизацией
            auth_register='https://3dsec.sberbank.ru/payment/rest/registerPreAuth.do',
            # Запрос завершения оплаты заказа с указанием суммы только в деньгах
            deposit='https://3dsec.sberbank.ru/payment/rest/deposit.do',
            # Запрос завершения оплаты заказа с указанием суммы в деньгах и бонусных баллах
            spasibo_deposit='https://3dsec.sberbank.ru/payment/rest/autoCompletion.do',
            # Запрос отмены оплаты заказа
            reverse='https://3dsec.sberbank.ru/payment/rest/reverse.do',
            # Запрос возврата средств оплаты заказа с указанием суммы только в деньгах
            refund='https://3dsec.sberbank.ru/payment/rest/refund.do',
            # Запрос возврата средств оплаты заказа с указанием суммы в деньгах и бонусных баллах
            spasibo_refund='https://3dsec.sberbank.ru/payment/rest/autoRefund.do'
        )

    def _request(self, url, params):
        logger.debug('Request  is {0!r}'.format(params))
        response = urllib.request.urlopen('{0}?{1}'.format(url, urllib.parse.urlencode(params)))
        logger.debug('Response is {0.status} {0._method} {0.reason} {headers}'.format(response, headers=response.getheaders()))
        self.assertEqual(response.status, 200)
        response_body = response.read()
        logger.debug('Response body is {0!r}'.format(response_body))
        self.assertIsNotNone(response_body)
        response_dict = json.loads(response_body.decode('utf8'), encoding='utf8')
        logger.debug('Unmarshaled response  is {0!r}'.format(response_dict))
        return response_dict

    def test_register(self):
        url = self.urls['register']
        request = dict(
            userName=Credentials.username,  # Логин магазина, полученный при подключении
            password=Credentials.password,  # Пароль магазина, полученный при подключении
            # Номер (идентификатор) заказа в системе магазина
            orderNumber=''.join(random.sample(string.ascii_uppercase+string.digits, 6)),
            # Сумма платежа в минимальных единицах валюты(копейки). Должна совпадать с общей суммой по всем товарным позициям в Корзине.
            amount=13531,
            currency=643,  # *Код валюты платежа ISO 4217.
            returnUrl='https://u6.ru', # Адрес, на который надо перенаправить пользователя в случае успешной оплаты
            failUrl='https://u6.ru',  # *Адрес, на который надо перенаправить пользователя в случае неуспешной оплаты
            description='Some booking on Amadeus E-Retail site',  # *Описание заказа в свободной форме
            language='RU',  # *Язык в кодировке ISO 639-1.
            pageView='DESKTOP',  # *В pageView передаётся признак - мобильное устройство: MOBILE или DESKTOP
            clientId='some_client_id',  # *Номер (идентификатор) клиента в системе магазина
            jsonParams='{}',  # *Поля дополнительной информации для последующего хранения
            sessionTimeoutSecs=600,  # *Продолжительность сессии в секундах. default=1200
            # *Время жизни заказа. Если не задано вычисляется по sessionTimeoutSecs
            expirationDate=(datetime.datetime.now() + datetime.timedelta(minutes=9)).isoformat().split('.')[0]
        )
        response = self._request(url, request)
        if 'errorCode' in response and response.get('errorCode') != '0':
            self.assertNotIn('errorCode', response)
        self.assertIn('orderId', response)
        self.assertIn('formUrl', response)
        # payment info: card 4111111111111111 Kenny McCormick CVC2 = 123

    def test_status(self):
        url = self.urls['status']
        request = dict(
            userName=Credentials.username,
            password=Credentials.password,
            # Номер заказа в платежной системе. Уникален в пределах системы.
            orderId='976495d3-2fa6-4e99-a026-058f83622767',  # you can get it after payment
            language='RU'  # Язык в кодировке ISO 639-1. Если не указан, считается, что язык – русский.
        )
        response = self._request(url, request)
        # Error Code is not 0 in this request if status != DEPOSITED
        # if 'ErrorCode' in response and response.get('ErrorCode') != '0':
        #     self.assertNotIn('ErrorCode', response)
        # check required answer keys
        for key in ('OrderNumber', 'Amount', 'Ip', 'ErrorCode'):
            self.assertIn(key, response)

    def test_status_ext(self):
        url = self.urls['status_ext']
        request = dict(
            userName=Credentials.username,
            password=Credentials.password,
            # Номер заказа в платежной системе. Уникален в пределах системы.
            orderId='976495d3-2fa6-4e99-a026-058f83622767',  # you can get it after payment
            language='RU'  # Язык в кодировке ISO 639-1. Если не указан, считается, что язык – русский.
        )
        response = self._request(url, request)
        if 'errorCode' in response and response.get('errorCode') != '0':
            self.assertNotIn('errorCode', response)
        # errorCode = 0 in this request if success not N otherwise
        # check required answer keys
        for key in ('orderNumber', 'amount', 'ip', 'date', 'errorCode'):
            self.assertIn(key, response)

    def test_reverse(self):
        url = self.urls['reverse']
        request = dict(
            userName=Credentials.username,
            password=Credentials.password,
            # Номер заказа в платежной системе. Уникален в пределах системы.
            orderId='976495d3-2fa6-4e99-a026-058f83622767',  # you can get it after payment
            language='RU'  # Язык в кодировке ISO 639-1. Если не указан, считается, что язык – русский.
        )
        response = self._request(url, request)
        self.assertEqual(response.get('errorCode'), '7',
                         msg='Reverse over DECLINE order must return ErrorCode=7 Returned: {errorCode} {errorMessage}'.format(**response))
        request['orderId'] = '30ab9530-eeb0-4a9d-beb9-1ba8c8c0b637'
        response = self._request(url, request)
        self.assertEqual(response.get('errorCode'), '7',
                         msg='Reverse over DEPOSITED order must return ErrorCode=7 Returned: {errorCode} {errorMessage}'.format(**response))

    def test_refund(self):
        url = self.urls['refund']
        request = dict(
            userName=Credentials.username,
            password=Credentials.password,
            # Номер заказа в платежной системе. Уникален в пределах системы.
            orderId='976495d3-2fa6-4e99-a026-058f83622767',  # you can get it after payment
            # Сумма возврата в валюте заказа. Может быть меньше или равна остатку в заказе.
            amount=13531,
            language='RU'  # Язык в кодировке ISO 639-1. Если не указан, считается, что язык – русский.
        )
        response = self._request(url, request)
        self.assertEqual(response.get('errorCode'), '7', msg='Refund over DECLINE order must return ErrorCode=7 Returned: {errorCode} {errorMessage}'.format(**response))

        request['orderId'] = '30ab9530-eeb0-4a9d-beb9-1ba8c8c0b637'
        response = self._request(url, request)
        self.assertEqual(response.get('errorCode'), '0', msg='Refund over DEPOSITED order must return ErrorCode=0 Returned: {errorCode} {errorMessage}'.format(**response))


class WrapperTestCase(unittest.TestCase):

    def setUp(self):
        from sber.pysberbps import SberWrapper
        self.wrapper = SberWrapper(Credentials.username, Credentials.password)

    def test_register(self):
        order = ''.join(random.sample(string.ascii_uppercase+string.digits, 6))
        amount = 35
        url = 'https://u6.ru/'
        logger.debug('Register order {} by REST POST request(default params) with {} amount and {} success url'.format(
            order, amount, url))
        order, form_url = self.wrapper.register(
            order=order,
            amount=amount,
            success_url=url)
        self.assertIsInstance(order, str)
        self.assertIsInstance(form_url, str)
        self.assertRegex(form_url, '^http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+$')
        self.assertRegex(order, '^\w{8}-\w{4}-\w{4}-\w{4}-\w{12}$')  # UID

def init_logger():
    handler = logging.FileHandler(path.join(path.dirname(path.abspath(__file__)), 'tests.log'), mode='w')
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter('%(levelname)s %(asctime)s %(message)s'))
    root_logger = logging.getLogger('')
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(handler)


if __name__ == '__main__':
    init_logger()
    Credentials.setUp()
    unittest.main()