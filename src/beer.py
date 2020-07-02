from shop import Shop


class Beer:
    def __init__(self, beer_name: str, rating: float, shop: Shop, line: int, variant: int = None,
                 brewery_name: str = None, beer_style: str = None, file_name: str = None,
                 price: float = None, beer_id: str = None):
        self.beer_id = beer_id  # id in the ratings site
        self.beer_name = beer_name  # name from ratings site
        self.rating = rating  # rating as float, 0 if unknown
        self.shop = shop  # from which shop
        self.line = line  # in which line of inventory exists
        self.file_name = file_name  # id of a file name (first char)
        self.price = price  # if exists
        self.variant = variant  # if there are more than 1 result for query by name
        self.brewery_name = brewery_name  # brewery name from ratings site
        self.beer_style = beer_style  # beer style from ratings site

    def __str__(self):
        return str((self.rating, "#{}".format(self.line), self.beer_name, self.brewery_name,
                    self.beer_style))

