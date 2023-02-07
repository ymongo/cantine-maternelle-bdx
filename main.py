#!/usr/bin/env python3

__author__ = "Yves Mongo"
__version__ = "0.1.0"
__license__ = "MIT"

import argparse
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from logzero import logger, logfile
import requests
import pywhatkit
import locale
from pathlib import Path

LOG_FILE = './tmp/script.log'
BASE_URL = 'https://www.sivu-bordeauxmerignac.fr/'
MENU_QUERY_PATTERN = '?menu-repas=bordeaux-maternelle-{date}'
GROUP_ID = 'KKJ70JWgBOk661QxWYOxsL'

session = requests.Session()
locale.setlocale(category=locale.LC_ALL, locale="fr_FR.utf8")
Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
logfile(LOG_FILE)

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
    "entree_sans_viande": {
        "name": "entree_sans_viande",
        "index": 4
    },
    "entree_vg": {
        "name": "entree_vg",
        "index": 5
    },
    "plat_classique": {
        "name": "plat_classique",
        "index": 6
    },
    "plat_sans_porc": {
        "name": "plat_sans_porc",
        "index": 7
    },
    "plat_sans_viande": {
        "name": "plat_sans_viande",
        "index": 8
    },
    "plat_vg": {
        "name": "plat_vg",
        "index": 9
    },
    "garniture_classique": {
        "name": "garniture_classique",
        "index": 10
    },
    "garniture_sans_porc": {
        "name": "garniture_sans_porc",
        "index": 11
    },
    "garniture_sans_viande": {
        "name": "garniture_sans_viande",
        "index": 12
    },
    "garniture_vg": {
        "name": "garniture_vg",
        "index": 13
    },
    "produit_laitier": {
        "name": "produit_laitier",
        "index": 14
    },
    "dessert": {
        "name": "dessert",
        "index": 15
    },
    "gouter_1": {
        "name": "gouter_1",
        "index": 16
    },
    "gouter_2": {
        "name": "gouter_2",
        "index": 17
    },

}


template = '''
*Menu du {date}* 

Potage / Entrée: _{potage_entree}_
Entrée classique: _{entree_classique}_
Entrée sans porc: _{entree_sans_porc}_
Entrée sans viande: _{entree_sans_viande}_
Entrée végétarien: _{entree_vg}_

Plat classique: _{plat_classique}_
Plat sans porc: _{plat_sans_porc}_
Plat sans viande: _{plat_sans_viande}_
Plat végétarien: _{plat_vg}_
Garniture classique: _{garniture_classique}_
Garniture sans porc: _{garniture_sans_porc}_
Garniture sans viande: _{garniture_sans_viande}_
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
        self.entree_sans_viande = ''
        self.entree_vg = ''
        self.plat_classique = ''
        self.plat_sans_porc = ''
        self.plat_sans_viande = ''
        self.plat_vg = ''
        self.garniture_classique = ''
        self.garniture_sans_porc = ''
        self.garniture_sans_viande = ''
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
    logger.info("Daily menus retrieved!")


def get_monday_date():
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    return start_of_week.strftime('%y%m%d')


def get_soup(html):

    soup = BeautifulSoup(html.content, "html5lib")
    return soup.find_all("div", class_="menu")


def send_message(semaine: Semaine):
    day_number = datetime.now().weekday()
    day_menu = semaine.jours[day_number]
    menu = template.format(**vars(day_menu)).replace("__", "")
    pywhatkit.sendwhatmsg_to_group_instantly(GROUP_ID, menu)
    logger.info("Check Whatsapp for sent message!")


def main(args):
    try:
        logger.info("Cantine Maternelle Bordeaux Scrapping Script")
        start_of_week_date = get_monday_date()
        html = get_raw_content(start_of_week_date)

        menu = get_soup(html)
        rows = get_menu_rows(menu)
        semaine = init_semaine(start_of_week_date)
        set_daily_menus(semaine, rows)

        send_message(semaine)
    except Exception as e:
        logger.error(str(e), exc_info=True)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s (version {version})".format(version=__version__))

    return parser.parse_args()


def get_raw_content(date):
    headers = {
        'Accept': 'text/html',
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:92.0) Gecko/20100101 Firefox/92.0",
    }
    url = BASE_URL+MENU_QUERY_PATTERN.format(date=date)
    response = session.get(url, headers=headers)
    if response.status_code == 200:
        logger.info(f"Succesfully retrieved content from date {date}")
    else:
        logger.error(
            f"Something wnet wrong while retrieving content from date {date}, status code {response.status_code}")
    return response


if __name__ == "__main__":
    args = get_args()
    main(args)
