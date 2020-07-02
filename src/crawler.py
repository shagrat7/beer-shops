import base64
import glob
import json
from datetime import date
import requests
from shop import Shop
import logging
import csv
import re
import sqlite3
from sqlite3 import Error, IntegrityError

logger = logging.getLogger(__name__)


class Crawler:
    def __init__(self, shop: Shop, download_ratings=True, use_ratings_cache=True,
                 use_existing_inventory_files=False):
        self.download_ratings = download_ratings  # download ratings
        self.use_ratings_cache = use_ratings_cache  # use cache of downloaded ratings where possible
        self.use_existing_files = use_existing_inventory_files  # do not download new beer inventory
        self.shop = shop
        self.file_paths = []
        self.ratings_site = None

    def get_beers_with_ratings(self) -> []:
        self._prepare_file_paths()
        beers = self._prepare_list_of_beers()
        return self._download_ratings(beers) if self.download_ratings else []

    def _prepare_file_paths(self):
        if self.shop.online_csv and self.use_existing_files is False:
            i = 0
            for r in self._download_beer_list():
                if r.status_code == 200:
                    i += 1
                    filename = "../data/{}/{}_{}.csv".format(self.shop.name, i, date.today())
                    self.file_paths.append(filename)
                    f = open(filename, "w")
                    f.write(r.text)
                    logger.debug("Downloaded list from {}, file name {}".
                                 format(self.shop.name, filename))
        else:  # use existing files to download ratings
            for filename in glob.glob("../data/{}/*.csv".format(self.shop.name)):
                self.file_paths.append(filename)
                logger.debug("Using list from {}, file name {}".format(self.shop.name, filename))

    def _prepare_list_of_beers(self) -> []:
        beers = []
        line = 0  # 0 is for headers, next lines also may be used
        for path in self.file_paths:
            with open(path) as csv_file:
                reader = csv.DictReader(csv_file, delimiter=self.shop.get_csv_delimiter())
                for row in reader:
                    line += 1
                    if line < self.shop.start_line:
                        continue  # rows without beers

                    row_with_beer_name = row[reader.fieldnames[0]]
                    beer_name = self._filter_out_beer_name(row_with_beer_name)
                    price = None
                    file = re.search(r"([0-9]+)_[0-9]{4}-[0-9]{2}-[0-9]{2}.csv", path).group(1)

                    # TODO: move this logic to Shop
                    if self.shop.name != "regionalne-alko":
                        x_or_price = row[reader.fieldnames[1]]

                        # strefa piwa
                        if x_or_price == "X":
                            continue
                        # avoid headers in the beer_name list, swiat piwa
                        if beer_name in ['ANGLIA', 'BELGIA', 'BRAZYLIA', 'DANIA', 'ESTONIA',
                                         'HOLANDIA', 'NIEMCY', 'NORWEGIA', 'NOWA ZELANDIA',
                                         'ROSJA', 'SZWECJA', 'USA']:
                            continue

                        # swiat piwa
                        pr = re.search(r"([0-9]+,[0-9]+) zł", x_or_price)
                        if pr is not None:
                            price = float(pr.group(1).replace(',', '.'))

                    beers.append({"name": beer_name, "price": price, "file": file, "line": line})
        return beers

    def _filter_out_beer_name(self, beer_with_type):
        beer = re.findall("[^()]+", beer_with_type)[0].strip()
        # filter out capacity, eg. 0,33l (all shops)
        # filter out packaging: BZW, PKA (swiat piwa issue)
        beer_parts = beer.split(" ")
        b = ''
        for part in beer_parts:
            add = True
            for pattern in self.shop.beer_name_part_exclude_patterns():
                if re.match(pattern, part):
                    add = False
            if add:
                b += ' ' + part
        beer = b.lower()
        for phrase in self.shop.beer_name_replace_phrases():
            beer = beer.replace(phrase[0], phrase[1])
        beer = beer.strip()
        return beer

    def _download_ratings(self, beers) -> []:
        enhanced_beers = []
        line = self.shop.start_line

        conn = self._create_ratings_cache_connection()
        for beer in beers:
            query = beer['name']
            if self.use_ratings_cache:
                cur = conn.cursor()
                cur.execute('SELECT * FROM ratings WHERE query="{}";'.format(query))
                # 0 - id, 1 - query, 2 - response, 3 - created
                rows = cur.fetchall()
                if len(rows) == 0:
                    resp_as_json = self._query_and_get_json(query, conn)
                else:
                    resp_as_json = json.loads(rows[0][2].replace("'", '"'))
                    logger.debug(resp_as_json)
            else:
                resp_as_json = self._query_and_get_json(query, conn)

            try:
                list_of_beers = self.parse_response(query, resp_as_json, line)
                for b in list_of_beers:
                    b.price = beer['price']
                    b.file = beer['file']
                    b.line = beer['line']
                enhanced_beers.extend(list_of_beers)
            except Exception as e:
                logger.error("Ups, json: {}".format(resp_as_json), e)

        if conn:
            conn.close()
        return enhanced_beers

    def _query_and_get_json(self, query, conn):
        r = self.query_page(query)
        r.encoding = 'utf-8'
        resp_as_json = None
        if r.status_code == 200:
            resp_as_json = r.json(encoding='utf-8')
            logger.debug("{}: {}".format(query, resp_as_json))
            try:
                conn.execute(
                    'INSERT INTO ratings(query, response, created) '
                    'VALUES("{}", "{}", datetime(\'now\'));'.format(
                        query, json.dumps(resp_as_json).replace("'", '*').replace('"', "'")))
                conn.commit()
            except IntegrityError:
                conn.execute(
                    'UPDATE ratings SET response="{}", created=datetime(\'now\') '
                    'WHERE query="{}";'.format(json.dumps(resp_as_json).replace("'", '*').
                                               replace('"', "'"), query))
                conn.commit()
        return resp_as_json

    def _create_ratings_cache_connection(self):
        conn = None
        try:
            conn = sqlite3.connect("../data/ratings/{}.db".format(self.ratings_site))
            return conn
        except Error as e:
            logger.error(e)
            if conn:
                conn.close()

    def parse_response(self, beer, json, line):
        raise NotImplementedError

    def query_page(self, beer):
        raise NotImplementedError

    def crawler_sleep_range(self):
        return 1, 2

    def _download_beer_list(self):
        headers = {
            "Accept": "text/csv",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "pl,en-US;q=0.9,en;q=0.8,pl-PL;q=0.7",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36"
        }
        for url in self.shop.get_csv_download_urls():
            r = requests.get(url=url, headers=headers)
            yield r
