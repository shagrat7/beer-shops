from unidecode import unidecode
from crawler import Crawler
from beer import Beer
from shop import Shop
import logging
import time
from random import randrange
import requests

logger = logging.getLogger(__name__)


class UntappdCrawler(Crawler):
    def __init__(self, shop: Shop, download_ratings=True, use_ratings_cache=True,
                 use_existing_inventory_files=False):
        super().__init__(shop, download_ratings, use_ratings_cache, use_existing_inventory_files)
        self.ratings_site = "untappd"

    def parse_response(self, beer, json, line) -> []:
        ret = []
        variants = len(json['hits'])
        if variants == 1:
            bl = json['hits'][0]

            logger.debug("{} [{}] beer {} from {}, style: {}, rating: {}".format(
                line, beer, bl['beer_name'], bl['brewery_name'], bl['type_name'],
                bl.get('rating_score', '0')))

            ret.append(Beer(bl['beer_name'], float(bl.get('rating_score', '0')), self.shop, line,
                            brewery_name=bl['brewery_name'],
                            beer_style=bl['type_name']))
        elif variants > 1:
            logger.debug("[{}, hits: {}] Too many results :(".format(beer, variants))

            # we want to get only the best match but we store also other if there is no ideal match
            query = self._clean_beer_name_to_compare(beer)
            eliminated_beers = []

            for variant in range(0, variants):
                bl = json['hits'][variant]

                index = self._clean_beer_name_to_compare(bl['beer_index'])

                logger.debug("\t{} [{}] beer {} from {}, style: {}, rating: {}".format(
                    line, beer, bl['beer_name'], bl['brewery_name'], bl['type_name'],
                    bl.get('rating_score', '0')))

                beer_data = Beer(bl['beer_name'], float(bl.get('rating_score', '0')),
                                 self.shop, line,
                                 variant=variant + 1,
                                 brewery_name=bl['brewery_name'],
                                 beer_style=bl['type_name'])
                if index == query:
                    ret.append(beer_data)
                else:
                    eliminated_beers.append(beer_data)
                    logger.debug("{} is not eq to {} for beer {}".format(index, query,
                                                                         bl['beer_name']))
                # we don't want to lose beers if there is no match
                if len(eliminated_beers) == variants:
                    ret.extend(eliminated_beers)
        else:
            logger.debug("[{}, hits: {}] No results :(".format(beer, variants))
        return ret

    def _clean_beer_name_to_compare(self, beer):
        query = unidecode(beer).lower().replace('browar', '').replace('brouwerij', '').\
            replace('brewery', '').replace('brasserie', '').strip().split(' ')
        query = list(set(filter(None, query)))
        query.sort()
        return query

    def query_page(self, beer):
        url = "https://9wbo4rq3ho-dsn.algolia.net/1/indexes/beer/query?x-algolia-agent=Algolia%20for%20vanilla%20JavaScript%203.24.8&x-algolia-application-id=9WBO4RQ3HO&x-algolia-api-key=1d347324d67ec472bb7132c66aead485"
        headers = {
            "accept": "application/json",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "pl,en-US;q=0.9,en;q=0.8,pl-PL;q=0.7",
            "content-type": "application/x-www-form-urlencoded; charset=utf-8",
            "Host": "9wbo4rq3ho-dsn.algolia.net",
            "Origin": "https://untappd.com",
            "Referer": "https://untappd.com/home",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36"
        }
        # to not to overload page
        time.sleep(randrange(self.crawler_sleep_range()[0], self.crawler_sleep_range()[1]))
        r = requests.post(url=url,
                          data='{"params":"query=!!!&hitsPerPage=3&clickAnalytics=true&analytics=true"}'.replace(
                              '!!!', beer.replace(' ', '%20')).encode('utf-8'),
                          headers=headers)
        return r

