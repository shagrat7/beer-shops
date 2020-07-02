class Shop:
    def __init__(self, name: str, online_csv: {} = {}, start_line=1):
        self.name = name
        self.start_line = start_line
        self.online_csv = online_csv

    def beer_name_part_exclude_patterns(self):
        raise NotImplementedError

    def beer_name_replace_phrases(self):
        raise NotImplementedError

    def get_csv_download_urls(self):
        for key in self.online_csv:
            for sheet in self.online_csv[key]:
                yield "https://docs.google.com/spreadsheets/d/{}/gviz/tq?tqx=out:csv&sheet={}" \
                    .format(key, sheet)

    def get_start_line(self):
        return self.start_line

    def get_csv_delimiter(self):
        return ","

    def __str__(self):
        return self.name


class StrefaPiwa(Shop):
    def __init__(self):
        super().__init__("strefa-piwa", {"1NCBWsezAbk95H5Fq_Vg_hhL2p9JHja91LxlDZND9Tog":
                                             ["POLSKA", "CZECHY", "ZAGRANICA"]})

    def beer_name_part_exclude_patterns(self):
        return ["[0-9,]+[ll]"]

    def beer_name_replace_phrases(self):
        return [('&', '%26')]


class SwiatPiwa(Shop):
    def __init__(self):
        super().__init__("swiat-piwa",
                         {"1DPIz3dzOZFmDGoXg-16xjOGds6ABxd7loTYzN3Z-Pcw": ["Shop%20stocks"]}, 2)

    def beer_name_part_exclude_patterns(self):
        return ["[0-9,]+[lL]", "(BZW|ZW|PKA)"]

    def beer_name_replace_phrases(self):
        return [('&', '%26'), ('100 mostów', 'stu mostow')]


class RegionalneAlkohole(Shop):
    # full inventory published at https://shorturl.at/lBFM1
    def __init__(self):
        super().__init__("regionalne-alko")

    def beer_name_part_exclude_patterns(self):
        return ["[0-9,]+L", "[0-9,]+%", "(BUTELKA|PUSZKA)"]

    def beer_name_replace_phrases(self):
        return [('&', '%26')]

    def get_csv_delimiter(self):
        return ";"


class Testowy(Shop):
    def __init__(self):
        super().__init__("test", {"1DPIz3dzOZFmDGoXg-16xjOGds6ABxd7loTYzN3Z-Pcw": ["Shop stocks"]},
                         2)

    def beer_name_part_exclude_patterns(self):
        return ["[0-9,]+[lL]", "(BZW|PKA)"]

    def beer_name_replace_phrases(self):
        return [('&', '%26'), ('100 mostów', 'stu mostow')]
