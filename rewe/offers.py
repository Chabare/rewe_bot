import re
from typing import Dict, List, Union

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

from .logger import Logger
from .product import Product


class Offer(Product):
    def __init__(self, outer_soup: Tag):
        self.outer_soup = outer_soup
        self.soup: Tag = outer_soup.find(class_="dotdot").find("div")
        name: str = self.get_name()
        price: float = self.get_price()
        picture_link: str = self.get_picture_link()

        super().__init__(name=name, price=price, picture_link=picture_link)

    def get_price(self) -> float:
        if self.price:
            return self.price
        price_text = self.outer_soup.find(class_="price").text
        price = re.findall(r"\d+.*", price_text)[0]

        return float(price)

    def get_name(self) -> str:
        if self.name:
            return self.name
        text: str = self.soup.text
        oneline_text = text.replace("\n", " ")
        single_whitespace_name = re.sub("\s+", " ", oneline_text)

        return single_whitespace_name

    def __eq__(self, other):
        return self.get_name() == other.get_name()

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        return "[{}] {}".format(self.get_name(), self.get_price())

    def get_picture_link(self) -> str:
        link_w_query = self.outer_soup.find('img').get('data-src')
        link = link_w_query

        if link_w_query.rfind("?") != -1:
            link = link_w_query.rsplit("?")[0]

        return link

    def get_picture(self) -> Union[bytes, str]:
        link = self.get_picture_link()

        return requests.get(link).content

    def get(self) -> Dict[str, Union[str, float]]:
        """
        Returns a dictionary with 'name' and 'price' as keys.
        :return: Dict[{"name", "price"}, ...]
        """
        return {"name": self.get_name(), "price": self.get_price()}


class OffersWebsite:
    def __init__(self, market_id: str, *, base_url=None, log_level: str = "INFO"):
        self.log = Logger("OffersWebsite", level=log_level)
        if not base_url:
            base_url = "https://www.rewe.de/angebote/?marketChosen="

        self.url = "".join([base_url, market_id])
        self.log.debug("URL for offers website: %s", self.url)

    def get_content(self) -> Union[bytes, str]:
        req = requests.get(self.url)
        if req.ok:
            return req.content

        raise ConnectionError("Couldn't read data from {}: {}".format(self.url, req.reason))

    @staticmethod
    def soupify_html(content: str) -> BeautifulSoup:
        root_soup = BeautifulSoup(content, "html.parser")

        return root_soup.find_all(class_="controller product")

    def get_offers(self) -> List[Offer]:
        content = self.get_content()
        outer_soup_products = self.soupify_html(content)

        result = list(set([Offer(soup) for soup in outer_soup_products]))
        return result
