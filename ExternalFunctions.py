from bs4 import BeautifulSoup
import requests
import logging
import subprocess


class ExternalFunctions(object):
    def __init__(self, chat_text):
        self.userAgent = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:50.0) '
                                        'Gecko/20100101 Firefox/50.0'}
        self.chatText = chat_text

    def commands(self):
        if "/help" in self.chatText:
            return self.help_list()
        if "/rp5_ru" in self.chatText:
            return self.weather_rp5()
        if "/excur_ru" in self.chatText:
            return self.excur_currency()
        if "/cbr_ru" in self.chatText:
            return self.cbr_currency()
        if "/drom_" in self.chatText:
            try:
                brand_model = str(self.chatText).split('_')
                brand, model = brand_model[1], brand_model[2]
                return self.drom_check(brand, model)
            except Exception as error:
                logging.error(f'Error in Commands {error}')
                return "Please Input Brand And Model With Space, Example /drom_honda_stream"
        if "/bash_" in self.chatText:
            try:
                bash = str(self.chatText).split('_')
                return self.bash_command(bash[1], bash[2])
            except Exception as error:
                logging.error(f'Error in Commands {error}')
                return "Please Input Command And Option With Space, Example /bash_ls_-l"

    def help_list(self):
        message = "List Commands: \n/help\n/rp5_ru\n/excur_ru\n/cbr_ru\n/drom_honda_stream\n/bash_ls_-l"
        return message

    def weather_rp5(self):
        url = 'https://rp5.ru/Погода_в_Новосибирске'
        try:
            response = requests.get(url, headers=self.userAgent, timeout=5)
            soup = BeautifulSoup(response.text, 'lxml')
            meta_tags = soup.find_all('meta', attrs={'name': 'description'})
            message = ""
            for meta in meta_tags:
                message += meta.attrs['content']
        except Exception as error:
            message = '\nNo data for Weather_rp5'
            logging.critical(f"Error in weather_rp5 {error}")
        return message

    def excur_currency(self):
        url = "https://excur.ru/Novosibirsk"
        try:
            response = requests.get(url, headers=self.userAgent, timeout=5)
            soup = BeautifulSoup(response.text, 'lxml')
            selling_usd = soup.find_all('td', class_='best-buy px-0 pr-1 text-center align-middle pointer',
                                        title='Выгодная продажа Доллара США')
            buying_usd = soup.find_all('td', class_='best-sell pl-0 pr-1 text-center align-middle pointer',
                                       title='Выгодная покупка Доллара США')
            selling_eur = soup.find_all('td', class_='best-buy px-0 pr-1 text-center align-middle pointer',
                                        title='Выгодная продажа Евро')
            buying_eur = soup.find_all('td', class_='best-sell pl-0 pr-1 text-center align-middle pointer',
                                       title='Выгодная покупка Евро')
            message = ""
            for currency in [selling_usd, buying_usd, selling_eur, buying_eur]:
                for child in currency:
                    message += f"{child.attrs['title']} {child.text}\n"
        except Exception as error:
            message = '\nNo data for excur_ru'
            logging.critical(f"Error in excur_currency {error}")
        return message

    def cbr_currency(self):
        url = "https://www.cbr.ru/scripts/XML_daily.asp?"
        message = ""
        try:
            response = requests.get(url, headers=self.userAgent, timeout=5)
            soup = BeautifulSoup(response.text, 'lxml')
            for currency in soup.find_all("name"):
                message += f"{currency.parent.charcode.text} {currency.text} " \
                           f"{currency.parent.nominal.text} {currency.parent.value.text} \n"
        except Exception as error:
            message = '\nNo data for cbr_ru'
            logging.critical(f"Error in cbr_currency {error}")
        return message

    def drom_check(self, brand, model):
        url = f"https://novosibirsk.drom.ru/{brand}/{model}/?isOwnerSells=1"
        message = ""
        try:
            response = requests.get(url, headers=self.userAgent, timeout=5)
            if response.status_code != 200:
                raise Exception
            soup = BeautifulSoup(response.text, 'lxml')
            car_list = soup.find_all(class_="b-advItem")
            for car in car_list:
                single_car = car.text.replace("  ", "").splitlines()
                for single in single_car:
                    if single:
                        message += single + "\n"
                message += car.get('href') + "\n"
        except Exception as error:
            message = f'\nNo data for drom_ru {brand} {model}'
            logging.critical(f"Error in drom_check {error}")
        return message

    def bash_command(self, bash, option):
        try:
            message = subprocess.check_output([bash, option], universal_newlines=True)
        except Exception as error:
            message = f'\nNo data for bash_command {bash} {option}'
            logging.critical(f"Error in bash_command {error}")
        return message
