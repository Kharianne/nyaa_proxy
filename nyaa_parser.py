import dataclasses
import urllib.error
from urllib import parse
from dataclasses import dataclass, field
from typing import List
import urllib.request as r
import gzip
from lxml import html
from .utils import retry


class InvalidHTTPCode(Exception):
    """Raised when the response code is invalid."""


class PageNotFoundError(InvalidHTTPCode):
    """Raised on HTTP status code 404 for page."""


class Not200CodeError(InvalidHTTPCode):
    """Raised when the response code is not 200."""


class UnexpectedFilesTreeStructure(Exception):
    """Raised when the files' tree structure is unexpected."""


class Config:

    @staticmethod
    def get_page(**kwargs):
        pass


class NyaaSearchConfig(Config):
    BASE_URL = "https://nyaa.si"
    ROW_SELECTOR = "//tbody/tr"
    NEXT_PAGE_SELECTOR = "//*[@class='next']/a/@href"

    DATA_SELECTOR_SEARCH_CATEGORY = \
        "td//a/img[@class='category-icon']/@alt"
    DATA_SELECTOR_SEARCH_NAME = \
        "td//a[contains(@href, 'view') and not(contains(@href, 'comments'))]/text()"
    DATA_SELECTOR_SEARCH_SIZE = \
        "(td//a[contains(@href, 'magnet')]/ancestor::td/following-sibling::td)[1]/text()"
    DATA_SELECTOR_SEARCH_ID = \
        "td//a[contains(@href, 'view') and not(contains(@href, 'comments'))]/@href"
    DATA_SELECTOR_SEARCH_MAGNET = \
        "td//a[contains(@href, 'magnet')]/@href"
    DATA_SELECTOR_SEARCH_UPLOADED = \
        "td/@data-timestamp"

    @staticmethod
    def get_page(**kwargs):
        try:
            return f"https://nyaa.si/?f=0&c=0_0&q={parse.quote(kwargs['query'], safe='')}" \
                   f"&p={kwargs['page_num']+1}"
        except KeyError:
            raise KeyError("Missing required keywords arguments. Required arguments: query and page.")


class NyaaDetailConfig(Config):
    DATA_SELECTOR_DETAIL_FILES_ROOT = \
        "//div[contains(@class, 'torrent-file-list')]"
    DATA_SELECTOR_DETAIL_ROOT_FOLDER = \
        "ul"
    DATA_SELECTOR_DETAIL_UPLOADED = \
        "//@data-timestamp"
    DATA_SELECTOR_DETAIL_NAME = \
        "(//*[contains(@class, 'panel-heading')]/*[contains(@class, 'panel-title')])[1]/text()"
    DATA_SELECTOR_DETAIL_MAGNET = \
        "//a[contains(@href, 'magnet')]/@href"

    @staticmethod
    def get_page(**kwargs):
        try:
            return f"https://nyaa.si/view/{kwargs['torrent_id']}"
        except KeyError:
            raise KeyError("Missing required keywords arguments. Required arguments: torrent_id.")


class Downloader:
    @staticmethod
    def get(url):
        try:
            headers = {
                'User-Agent': "python-requests/2.25.1",
                'Accept-Encoding': 'gzip',
                'Accept': '*/*',
                'Connection': 'keep-alive',
            }
            req = r.Request(url, headers=headers)
            res = r.urlopen(req)
            encoding = res.getheader('Content-Encoding')
            data = res.read()

            if encoding == 'gzip':
                data = gzip.decompress(data)
            elif encoding == 'identity' or not encoding:
                pass
            else:
                raise RuntimeError(f"Encoding is not supported: {encoding}.")

            return data.decode('utf8')

        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise PageNotFoundError("Could not find given page.")
            else:
                raise Not200CodeError(f'Request ended with status code: '
                                      f'{e.code}')
        except Exception as e:
            raise RuntimeError("Could not connect to host.") from e


@dataclass
class TorrentRow:
    name: str
    magnet: str
    uploaded: int
    id: int

    def __str__(self):
        return f'{self.name} [{self.id}] {self.magnet}' \
               f' {self.uploaded}'


@dataclass
class TorrentDetail:
    id: int
    uploaded: int
    name: str
    magnet: str
    files: List

    def __str__(self):
        return f"ID: {self.id} \n" \
               f"Uploaded: {self.uploaded} \n" \
               f"Name: {self.name} \n" \
               f"Magnet: {self.magnet} \n" \
               f"Files: {self.files}"


@dataclass
class SearchParseResult:
    next_page_num: int = field(default=None)
    rows: List[TorrentRow] = field(default_factory=list)


class Parser:
    def __init__(self, config):
        self.config = config

    def parse(self, page, **kwargs):
        pass


class SearchParser(Parser):

    def parse(self, page, **kwargs):
        result = SearchParseResult()
        tree = html.fromstring(page)

        try:
            page_num = kwargs['page_num']
        except KeyError:
            raise KeyError("Argument page_num is missing")

        try:
            self.config.BASE_URL + tree.xpath(self.config.NEXT_PAGE_SELECTOR)[0]
        except IndexError:
            result.next_page_num = None
        else:
            result.next_page_num = page_num + 1

        rows = tree.xpath(self.config.ROW_SELECTOR)
        for row in rows:
            _id = row.xpath(self.config.DATA_SELECTOR_SEARCH_ID)[0]
            result.rows.append(TorrentRow(
                id=int(_id.split('/')[2]),
                uploaded=int(row.xpath(self.config.DATA_SELECTOR_SEARCH_UPLOADED)[0]),
                name=row.xpath(self.config.DATA_SELECTOR_SEARCH_NAME)[0],
                magnet=row.xpath(self.config.DATA_SELECTOR_SEARCH_MAGNET)[0],
            ))
        return result


class DetailParser(Parser):

    def parse(self, page, **kwargs):
        tree = html.fromstring(page)
        return TorrentDetail(
            id=kwargs['torrent_id'],
            uploaded=tree.xpath(self.config.DATA_SELECTOR_DETAIL_UPLOADED)[0],
            name=tree.xpath(self.config.DATA_SELECTOR_DETAIL_NAME)[0].strip(),
            magnet=tree.xpath(self.config.DATA_SELECTOR_DETAIL_MAGNET)[0],
            files=self.get_files(tree)
        )

    def get_files(self, tree):
        roots = tree.xpath(self.config.DATA_SELECTOR_DETAIL_FILES_ROOT)
        if len(roots) != 1:
            raise UnexpectedFilesTreeStructure()

        root_folders = roots[0].xpath(self.config.DATA_SELECTOR_DETAIL_ROOT_FOLDER)
        if len(root_folders) != 1:
            raise UnexpectedFilesTreeStructure()

        return self.process_folder(root_folders[0])

    def process_folder(self, folder):
        files = []
        li = folder.xpath("li")
        for l in li:
            if l.xpath("a[contains(@class, 'folder')]"):

                sub_ul = l.xpath("ul")
                if len(sub_ul) != 1:
                    raise UnexpectedFilesTreeStructure()
                files.append({"type": "dir",
                              "name": "".join(l.xpath('a/text()')).strip(),
                              "files": self.process_folder(sub_ul[0])})
            else:
                files.append(
                    {"type": "file",
                     "name": "".join(l.xpath('text()')).strip()
                     }
                )
        return files


class ParserDriver:
    def __init__(self, config, downloader, parser):
        self.config = config
        self.downloader = downloader
        self.parser = parser

    def run(self, **kwargs):
        url = self.config.get_page(**kwargs)
        page = self.downloader.get(url)
        return self.parser.parse(page, **kwargs)


@retry((RuntimeError, Not200CodeError))
def get_search_results(query, page_num, retries=None):
    down = Downloader()
    parser = SearchParser(NyaaSearchConfig)
    driver = ParserDriver(NyaaSearchConfig, down, parser)
    parse_result = driver.run(query=query, page_num=page_num)
    results = [dataclasses.asdict(row) for row in parse_result.rows]
    return results, parse_result.next_page_num


@retry((RuntimeError, Not200CodeError))
def get_details(torrent_id, retries=None):
    down = Downloader()
    parser = DetailParser(NyaaDetailConfig)
    driver = ParserDriver(NyaaDetailConfig, down, parser)
    return dataclasses.asdict(driver.run(torrent_id=torrent_id))

