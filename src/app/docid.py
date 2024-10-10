import nameparser
import dateparser
import requests
import defusedxml.ElementTree as DET

from importlib.metadata import version
import datetime

from app.idparser import IDType

nameparser.config.CONSTANTS.force_mixed_case_capitalization = True
nameparser.config.CONSTANTS.string_format = "{last}"
nameparser.config.CONSTANTS.initials_format = "{first} {middle}"


headers = {
    "User-Agent": "CommunalGrowth/%s (mailto:admin@communalgrowth.org; tel:+1-269-491-5579)"
    % version("webserver")
}


def get_url(url):
    """Simple wrapper over requests.get() with header and timeout"""
    return requests.get(url, headers=headers, timeout=5)


def ok_response(response):
    """Check if response succeeded with HTTP 200 code"""
    return response.status_code == requests.codes["ok"]


def normalize_human_name(name):
    name = name.strip()
    if " " not in name:
        name = nameparser.HumanName(last=name)
    else:
        name = nameparser.HumanName(name)
    name.capitalize()
    initials = name.initials()
    ret = f"{initials} " if initials else ""
    ret += str(name)
    return ret


# Try with:
# ISBN-10: 0140328726
# ISBN-13: 9780140328721
def lookup_isbn(isbn):
    """Lookup an ISBN-10 or ISBN-13 from openlibrary.org"""
    isbn10_default = isbn if len(isbn) == 10 else None
    isbn13_default = isbn if len(isbn) == 13 else None
    isbn_url = f"https://openlibrary.org/isbn/{isbn}.json"
    authors_url = f"https://openlibrary.org/search.json?isbn={isbn}&fields=author_name"
    response = get_url(isbn_url)
    if not ok_response(response):
        return {}
    response2 = get_url(authors_url)
    if not ok_response(response2):
        return {}
    try:
        data = response.json()
        title = data["title"]
        subtitle = data.get("subtitle", "")
        publish_date = data.get("publish_date", "1984-01-01")
        date = dateparser.parse(publish_date).strftime("%Y-%m-%dT%H:%M:%SZ")
        isbn_10 = data.get("isbn_10", [isbn10_default])[0]
        isbn_13 = data.get("isbn_13", [isbn13_default])[0]
        data2 = response2.json()
        authors = [
            normalize_human_name(x)
            for x in data2.get("docs", [{}])[0].get("author_name", ["Unknown"])
        ]
        return dict(
            title=title,
            subtitle=subtitle,
            published=date,
            authors=authors,
            isbn10=isbn_10,
            isbn13=isbn_13,
        )
    except:
        return {}


# Try with:
# DOI: 10.1038/248030a0
def lookup_doi(doi):
    doi_url = f"https://api.crossref.org/works/{doi}"
    response = get_url(doi_url)
    if not ok_response(response):
        return {}
    try:
        data = response.json()
        message = data["message"]
        title = " ".join(message["title"])
        year, month, day = message.get("published", {}).get(
            "date-parts", [[1984, 1, 1]]
        )[0]
        date = datetime.date(year, month, day).strftime("%Y-%m-%dT%H:%M:%SZ")
        authors = message.get("author", [dict(given="", family="Unknown")])
        authors_list = []
        for d in authors:
            name = normalize_human_name(f"{d['given']} {d['family']}")
            authors_list += [name]
        return dict(title=title, published=date, authors=authors_list, doi=doi)
    except:
        return {}


# Try with:
# arXiv: 1708.05919
def lookup_arxiv(arxiv):
    namespaces = dict(
        atom="http://www.w3.org/2005/Atom",
        opensearch="http://a9.com/-/spec/opensearch/1.1/",
        arxiv="http://arxiv.org/schemas/atom",
    )
    arxiv_url = f"http://export.arxiv.org/api/query?id_list={arxiv}"
    response = get_url(arxiv_url)
    if not ok_response(response):
        return {}
    try:
        et = DET.fromstring(response.text)
        title = et.find("atom:entry/atom:title", namespaces)
        if title is None:
            return {}
        else:
            title = title.text
        published = et.find("atom:entry/atom:published", namespaces)
        if published is None:
            published = "1984-01-01T00:00:00Z"
        else:
            published = published.text
        authors = []
        for author in et.findall("atom:entry/atom:author/atom:name", namespaces):
            authors += [normalize_human_name(author.text)]
        if not authors:
            authors = ["Unknown"]
        return dict(title=title, published=published, authors=authors, arxiv=arxiv)
    except:
        return {}


def lookup_doc(doctype, docid):
    """Find document details with an internet lookup.

    Returns a dictionary with keys such as title, authors, etc."""
    match doctype:
        case x if x in [IDType.ISBN10, IDType.ISBN13]:
            return lookup_isbn(docid)
        case IDType.DOI:
            return lookup_doi(docid)
        case IDType.ARXIV:
            return lookup_arxiv(docid)
        case IDType.TITLE:
            return {}
