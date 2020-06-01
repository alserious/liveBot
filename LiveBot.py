from bs4 import BeautifulSoup
from requests import Session
from lxml import html
import logging
import requests
import time
import ExternalFunctions

logging.basicConfig(filename="debug.log", format='%(asctime)s %(levelname)s:%(message)s', level=logging.DEBUG)


class Proxy(Session):
    def __init__(self):
        super().__init__()
        self.telegramApi = "https://api.telegram.org/"
        self.ipList = []
        self.proxyDict = {}

    def proxy_site_first(self):
        site = "https://www.ip-adress.com/proxy-list"
        try:
            response = self.get(site, timeout=3)
        except Exception as error:
            return logging.critical(f"Proxy Site: {site} TIMEOUT {error}")
        body = html.fromstring(response.text)
        ip = body.xpath("//tr/td[1]/a[1]/text()")
        port = body.xpath("//tr/td[1]/text()")
        for counter in range(0, len(ip)):
            self.ipList.append(ip[counter] + port[counter])
        return self.ipList

    def proxy_site_second(self):
        site = "https://free-proxy-list.net/"
        try:
            response = self.get(site, timeout=3)
        except Exception as error:
            return logging.critical(f"Proxy Site: {site} TIMEOUT {error}")
        soup = BeautifulSoup(response.text, "html.parser")
        proxy = soup.find(id="proxylisttable")
        iter_ip = [i for i in range(0, len(proxy.findAll("td")), 8)]
        iter_port = [i for i in range(1, len(proxy.findAll("td")), 8)]
        ip = ""
        for counter, ip_port in enumerate(proxy.findAll("td")):
            if counter in iter_ip:
                ip = ip_port.text
            if counter in iter_port:
                ip += f":{ip_port.text}"
                self.ipList.append(ip)
        return self.ipList

    def get_proxy(self, proxy_dict):
        ip = proxy_dict.get("https")
        ip = str(ip)[8:]
        if not ip:
            logging.info("Proxy Start First If NO IP")
            self.proxy_site_first()
            self.proxy_site_second()
        elif ip:
            logging.info("Start Second If HAVE IP")
            index = self.ipList.index(ip)
            self.ipList = self.ipList[index + 1:]
        for ip in self.ipList:
            self.proxyDict = {
                "http": "http://" + ip,
                "https": "https://" + ip,
                "ftp": "ftp://" + ip
            }
            try:
                self.get(self.telegramApi, proxies=self.proxyDict, timeout=1)
                logging.info("OK Proxy: " + str(self.proxyDict))
                return self.proxyDict
            except Exception as error:
                logging.error(f"Fail Proxy: {self.proxyDict} {error}")
                continue
        logging.critical("Not Found Proxy Wait 40 Sec And Try Again")
        time.sleep(40)
        return self.get_proxy(proxy_dict={})


class Telegram(Proxy):
    def recursive_listening(self, url_bot):
        self.urlBot = url_bot
        self.offset = None
        while True:
            self.get_update()
            self.parse_response()
            self.execute_commands()
            self.offset = self.updateId + 1
            logging.info(f"{self.updateId} - {self.userName} : {self.chatText}")

    def get_update(self):
        while True:
            try:
                params = {'timeout': 30, 'offset': self.offset}
                response = self.get(self.urlBot + 'getUpdates', data=params, proxies=self.proxyDict, timeout=40).json()
                self.listResponses = response['result']
                if self.listResponses:
                    logging.info(f"Get Result: {self.listResponses}")
                    return self.listResponses
                else:
                    # logging.info(f"DO NOT Get Result: {self.listResponses}")
                    time.sleep(30)
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout,
                    requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
                self.proxyDict = self.get_proxy(self.proxyDict)
                # return self.proxyDict

    def parse_response(self):
        for self.response in self.listResponses:
            self.updateId = self.response['update_id']
            try:
                self.userName = self.response['message']['chat']['username']
                self.chatId = self.response['message']['chat']['id']
            except Exception as error:
                self.userName = ""
                self.chatId = ""
                logging.critical(f"userName or chatId Error {error}")
            try:
                self.chatText = self.response['message']['text']
            except Exception as error:
                self.chatText = ""
                logging.critical(f"chatText Error {error}")
            return self.updateId, self.userName, self.chatId, self.chatText

    def execute_commands(self):
        if self.chatId == 'YOUR CHAT ID':
            try:
                output = ExternalFunctions.ExternalFunctions(self.chatText).commands()
                if len(output) < 4000:
                    params = {'chat_id': self.chatId, 'text': output}
                    self.post(self.urlBot + 'sendMessage', data=params, proxies=self.proxyDict, timeout=20)
                else:
                    strings = 0
                    count_messge = int(len(output) / 4000)
                    for count in range(0, count_messge):
                        params = {'chat_id': self.chatId, 'text': output[strings:strings + 4000]}
                        self.post(self.urlBot + 'sendMessage', data=params, proxies=self.proxyDict, timeout=20)
                        strings = strings + 4000
            except Exception as error:
                logging.critical(f"Can't Sent ExeCommand \n {error}")


def main():
    url_bot = "YOUR BOT TOKEN"
    Telegram().recursive_listening(url_bot)


main()
