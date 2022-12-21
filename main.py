#!/usr/bin/env python3

__author__ = "Yves Mongo"
__version__ = "0.1.0"
__license__ = "MIT"

import argparse
from datetime import datetime, timedelta
import json
from bs4 import BeautifulSoup
from logzero import logger
import requests
import pywhatkit
from constants import *
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import locale

BASE_URL = 'https://www.sivu-bordeauxmerignac.fr/'
MENU_QUERY_PATTERN = '?menu-repas=bordeaux-maternelle-{date}'
GROUP_ID = 'KKJ70JWgBOk661QxWYOxsL'
WA_FILE_PATH = "session.wa"
SET_SESSION_FILE_PATH = 'set_wa_session.js'
session = requests.Session()
locale.setlocale(category=locale.LC_ALL, locale="fr_FR.utf8")

categories = {
    "potage_entree": {
        "name": "potage_entree",
        "index": 1
    },
    "entree_classique": {
        "name": "entree_classique",
        "index": 2
    },
    "entree_sans_porc": {
        "name": "entree_sans_porc",
        "index": 3
    },
    "entree_vg": {
        "name": "entree_vg",
        "index": 4
    },
    "plat_classique": {
        "name": "plat_classique",
        "index": 5
    },
    "plat_sans_porc": {
        "name": "plat_sans_porc",
        "index": 6
    },
    "plat_vg": {
        "name": "plat_vg",
        "index": 7
    },
    "garniture_classique": {
        "name": "garniture_classique",
        "index": 8
    },
    "garniture_sans_porc": {
        "name": "garniture_sans_porc",
        "index": 9
    },
    "garniture_vg": {
        "name": "garniture_vg",
        "index": 10
    },
    "produit_laitier": {
        "name": "produit_laitier",
        "index": 11
    },
    "dessert": {
        "name": "dessert",
        "index": 12
    },
    "gouter_1": {
        "name": "gouter_1",
        "index": 13
    },
    "gouter_2": {
        "name": "gouter_2",
        "index": 14
    },

}


template = '''
*Menu du {date}* 

Potage / Entrée: _{potage_entree}_
Entrée classique: _{entree_classique}_
Entrée sans porc: _{entree_sans_porc}_
Entrée végétarien: _{entree_vg}_

Plat classique: _{plat_classique}_
Plat sans porc: _{plat_sans_porc}_
Plat végétarien: _{plat_vg}_
Garniture classique: _{garniture_classique}_
Garniture sans porc: _{garniture_sans_porc}_
Garniture végétarien: _{garniture_vg}_

Produit laitier: _{produit_laitier}_

Dessert: _{dessert}_

Goûter 1: _{gouter_1}_
Goûter 2: _{gouter_2}_

Bonne journée !
'''

class Jour():
    def __init__(self, date):
        self.date = datetime.strftime(date, "%A %d/%m/%y")
        self.potage_entree = ''
        self.entree_classique = ''
        self.entree_sans_porc = ''
        self.entree_vg = ''
        self.plat_classique = ''
        self.plat_sans_porc = ''
        self.plat_vg = ''
        self.garniture_classique = ''
        self.garniture_sans_porc = ''
        self.garniture_vg = ''
        self.produit_laitier = ''
        self.dessert = ''
        self.gouter_1 = ''
        self.gouter_2 = ''

    def __repr__(self):
        return repr(vars(self))


class Semaine():
    def __init__(self, lundi: Jour, mardi: Jour, mercredi: Jour, jeudi: Jour, vendredi: Jour,):
        self.jours = [lundi, mardi, mercredi, jeudi, vendredi]

    def __repr__(self):
        return str(vars(self))


def init_semaine(raw_date):
    date = datetime.strptime(raw_date, '%y%m%d').date()
    return Semaine(Jour(date),
                   Jour(date + timedelta(days=1)),
                   Jour(date + timedelta(days=2)),
                   Jour(date + timedelta(days=3)),
                   Jour(date + timedelta(days=4)))


def get_menu_rows(menu):
    table = menu[0].find_all('table')[0]
    return table.find_all('tr')

def get_cell_text(cols, index):
    text = ''
    if len(cols[index]):
        text = cols[index].get_text(
            strip=True, separator='\n').splitlines()[0]
    return text

def set_categorie(semaine, rows, categorie):
    cols = rows[categorie.get('index')].find_all('td')
    for i in range(1, 6):
        try:
            text = ''
            if categorie.get('name') == 'potage_entree':
                text = get_cell_text(cols, i+1)
            elif categorie.get('name') == 'gouter_1':
                text = get_cell_text(cols, i+1)
            else:
                text = get_cell_text(cols, i)
            if text:
                setattr(semaine.jours[i-1], categorie.get('name'), text)
        except Exception as e:
            logger.error(str(e), f"failed at {i}")


def set_daily_menus(semaine, rows):
    for day in semaine.jours:
        generator = (x for x in vars(day).keys() if x != 'date')
        for categorie_name in generator:
            categorie = categories[categorie_name]
            set_categorie(semaine, rows, categorie)


def _wait_for_presence_of_an_element(browser, selector):
	element = None

	try:
		element = WebDriverWait(browser, INTEGERS.DEFAULT_WAIT).until(
			EC.presence_of_element_located(selector)
		)
	except:
		pass
	finally:
		return element

def sessionOpener(): 
    with open(WA_FILE_PATH, "r", encoding='UTF-8') as session_file:
        session = session_file.read()
    browser = webdriver.Chrome()
    browser.get("https://web.whatsapp.com/")
    _wait_for_presence_of_an_element(browser, SELECTORS.QR_CODE)
    with open(SET_SESSION_FILE_PATH, "r", encoding='UTF-8') as set_session_file:
        script = set_session_file.read()
    print(script)
    browser.execute_script(script, session)
    browser.refresh

    input('test')

def main(args):
    logger.info("Cantine Maternelle Bordeaux Scrapping Script")
    logger.info(args)
    html = get_raw_content(args.date)
    soup = BeautifulSoup(html.content, "html.parser")
    menu = soup.find_all("div", class_="menu")
    rows = get_menu_rows(menu)
    semaine = init_semaine(args.date)
    set_daily_menus(semaine, rows)
    json_menu = json.dumps(str(semaine), ensure_ascii=False, indent=2)
    # print(json_menu)
    with open('json_menu.json', 'w') as outfile:
        json.dump(str(semaine), outfile)
    # sessionOpener()
    day_number = datetime.now().weekday()
    day_menu = semaine.jours[day_number]
    menu = template.format(**vars(day_menu)).replace("__", "")
    print(menu)
    # fomatted_message = template.format()
    pywhatkit.sendwhatmsg_to_group_instantly(GROUP_ID, menu)


def get_args():

    parser = argparse.ArgumentParser()

    # Required positional argument
    parser.add_argument(
        "date", help="Required date of start of the week, YYMMDD")

    # Specify output of "--version"
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s (version {version})".format(version=__version__))

    return parser.parse_args()


def get_raw_content(date):
    headers = {
        'Accept': 'text/html',
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"
    }
    url = BASE_URL+MENU_QUERY_PATTERN.format(date=date)
    response = session.get(url, headers=headers)
    if response.status_code == 200:
        logger.debug(f"Succesfully retrieved content from date {date}")
    else:
        logger.debug(
            f"Something wnet wrong while retrieving content from date {date}, status code {response.status_code}")
    return response


if __name__ == "__main__":
    args = get_args()
    main(args)
