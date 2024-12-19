
import json
import time
from collections import namedtuple

import matplotlib.pyplot as plt
import requests

# Реализация хранение чисел с плавающей точкой
FloatNumber = namedtuple('FloatNumber', ['integer', 'fractional'])


class CurrenciesLst:

    def __init__(self, currencies: list):
        self.currencies = currencies

    def __len__(self):
        return len(self.currencies)

    def __iter__(self):
        return iter(self.currencies)

    def plot_currencies(self, filename="currencies.jpg"):
        names = []
        values = []
        for item in self.currencies:
            for code, (name, value) in item.items():
                names.append(name)
                values.append(float(value.integer + '.' + value.fractional))

        plt.figure(figsize=(10, 6))
        plt.bar(names, values)
        plt.xlabel("Валюта")
        plt.ylabel("Курс (RUB)")
        plt.title("Курсы валют ЦБ РФ")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(filename)
        plt.show()

    def to_json(self):
        return json.dumps(self.currencies, indent=4)

    def to_csv(self):
        import csv
        from io import StringIO

        csv_data = StringIO()
        writer = csv.writer(csv_data)

        # Write header
        writer.writerow(["Currency Code", "Currency Name", "Currency Value"])

        for item in self.currencies:
            for code, (name, value) in item.items():
                writer.writerow([code, name, str(float(value.integer + '.' + value.fractional))])

        return csv_data.getvalue()


class Component:

    def get_currencies(self, currency_codes=None):
        pass


class Decorator(Component):
    def __init__(self, decorated):
        self.decorated = decorated

    def get_currencies(self, currency_codes=None):
        return self.decorated.get_currencies(currency_codes)


class ConcreteDecoratorJSON(Decorator):
    def get_currencies(self, currency_codes=None):
        currencies = super().get_currencies(currency_codes)
        return currencies.to_json()


class ConcreteDecoratorCSV(Decorator):
    def get_currencies(self, currency_codes=None):
        currencies = super().get_currencies(currency_codes)
        return currencies.to_csv()


class CentralBankRates(Component, metaclass=type):
    __instance = None

    def __new__(cls, request_interval=1):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance._last_request_time = 0
            cls.__instance.request_interval = request_interval
        return cls.__instance

    def __init__(self, request_interval=1):
        self.request_interval = request_interval

    def __del__(self):
        print("Объект CentralBankRates удален")

    def set_request_interval(self, interval):
        self.request_interval = interval

    def get_request_interval(self):
        return self.request_interval

    def _wait_for_next_request(self):
        elapsed_time = time.time() - self._last_request_time
        if elapsed_time < self.request_interval:
            time.sleep(self.request_interval - elapsed_time)
        self._last_request_time = time.time()

    def get_currencies(self, currency_codes=None) -> CurrenciesLst:
        self._wait_for_next_request()

        cur_res_str = requests.get('http://www.cbr.ru/scripts/XML_daily.asp')
        result = []

        from xml.etree import ElementTree as ET

        root = ET.fromstring(cur_res_str.content)
        valutes = root.findall(
            "Valute"
        )
        for _v in valutes:
            valute_id = _v.get('ID')
            valute = {}
            if str(valute_id) in currency_codes:
                valute_cur_name = _v.find('Name').text
                valute_cur_val = FloatNumber(*_v.find('Value').text.split(','))
                valute_nominal = int(_v.find('Nominal').text)
                valute_charcode = _v.find('CharCode').text
                if valute_nominal != 1:
                    valute[valute_charcode] = (valute_cur_name, valute_cur_val)
                else:
                    valute[valute_charcode] = (valute_cur_name, valute_cur_val)
                result.append(valute)

        return CurrenciesLst(result)
    


print(CentralBankRates().get_currencies(['R01035']).to_csv())

