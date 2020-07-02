from crawler import Crawler
from beer import Beer
from shop import Shop
import logging
import time
from random import randrange
import requests

logger = logging.getLogger(__name__)


class RateBeerCrawler(Crawler):
    def __init__(self, shop: Shop, download_ratings=True, use_ratings_cache=True,
                 use_existing_inventory_files=False):
        super().__init__(shop, download_ratings, use_ratings_cache, use_existing_inventory_files)
        self.ratings_site = "ratebeer"

    def parse_response(self, beer, json, line):
        logger.debug(json)
        ret = []
        variants = json['data']['results']['totalCount']
        if variants == 1:
            bl = json['data']['results']['items'][0]['beer']

            logger.debug("{} [{}] beer {} from {}, style: {}, rating: {}".format(
                line, beer, bl['name'], bl['brewer']['name'], bl['style']['name'],
                bl['averageQuickRating']))

            ret.append(Beer(bl['name'],
                            float('0' if bl.get('averageQuickRating', '0') is None
                                  else bl.get('averageQuickRating')),
                            self.shop, line,
                            brewery_name=bl['brewer']['name'],
                            beer_style=bl['style']['name']))
        elif variants > 1:
            logger.debug("[{}, hits: {}] Too many results :(".format(beer, variants))
            for variant in range(0, min(10, variants)):  # TODO ath this moment max 10 per page
                bl = json['data']['results']['items'][variant]['beer']

                logger.debug("\t{} [{}] beer {} from {}, style: {}, rating: {}".format(
                    line, beer, bl['name'], bl['brewer']['name'], bl['style']['name'],
                    bl['averageQuickRating']))

                ret.append(Beer(bl['name'],
                                float('0' if bl.get('averageQuickRating', '0') is None
                                      else bl.get('averageQuickRating')),
                                self.shop, line,
                                variant=variant + 1,
                                brewery_name=bl['brewer']['name'],
                                beer_style=bl['style']['name']))
        else:
            logger.debug("[{}, hits: {}] No results :(".format(beer, variants))
        return ret

    def query_page(self, beer):
        url = "https://beta.ratebeer.com/v1/api/graphql/?operationName=SearchResultsBeer&variables=%7B%22query%22%3A%22!!!!!%22%2C%22order%22%3A%22MATCH%22%2C%22includePurchaseOptions%22%3Atrue%2C%22latlng%22%3A%5B50.07072067260742%2C19.93099021911621%5D%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%22d63bad785425ecffd4e80e09135471fa0b107d5f579ee82c8ea6b69a3497c524%22%7D%7D"
        headers = {
            "authority": "beta.ratebeer.com",
            "accept": "*/*",
            "locale": "pl",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36",
            "content-type": "application/json",
            "origin": "https://www.ratebeer.com",
            "sec-fetch-site": "same-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://www.ratebeer.com/search?q=&tab=beer",
            "accept-language": "pl,en-US;q=0.9,en;q=0.8,pl-PL;q=0.7",
        }
        # to not to overload page
        time.sleep(randrange(self.crawler_sleep_range()[0], self.crawler_sleep_range()[1]))
        r = requests.get(url=url.replace('!!!!!', beer.replace(' ', '%20')).encode('utf-8'),
                         headers=headers)
        return r
