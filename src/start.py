import logging

from crawlers.ratebeer import RateBeerCrawler
from shop import StrefaPiwa, SwiatPiwa, Testowy, RegionalneAlkohole
from crawlers.untapped import UntappdCrawler

# real inventories
strefa = StrefaPiwa()
swiat = SwiatPiwa()
reg_alk = RegionalneAlkohole()  # works only with use_existing_files = True

# test inventories
test = Testowy()

selected = [reg_alk, strefa, swiat]
crawler = UntappdCrawler
download_ratings = True  # download beer ratings, True by default
use_existing_files = False  # download new files with inventory from shops, False by default
use_ratings_cache = True

level = logging.DEBUG if test in selected else logging.INFO
logging.basicConfig(level=level)

beers_by_ratings = []
for shop in selected:
    beers_by_ratings.extend(crawler(shop, download_ratings, use_ratings_cache,
                                    use_existing_files).get_beers_with_ratings())

print("=====================================, beers: {}".format(len(beers_by_ratings)))

beers_by_ratings.sort(reverse=True, key=lambda x: x.rating)
for b in beers_by_ratings:
    print("{:6} | {:1.2f} | {} | {} | {} | {} | #{}/{}".format(
        str(b.line) if b.variant is None else str(b.line) + "/" + str(b.variant),
        b.rating, b.beer_name, b.brewery_name, b.beer_style,
        "{:1.2f} zł".format(b.price) if b.price is not None else "?", b.file, b.shop.name))
