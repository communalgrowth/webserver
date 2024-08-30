import lark
import enum


class IDType(enum.Enum):
    ISBN10 = enum.auto()
    ISBN13 = enum.auto()
    ARXIV = enum.auto()
    DOI = enum.auto()
    TITLE = enum.auto()


class MyTransformer(lark.Transformer):
    def doi(self, xs):
        return (IDType.DOI, xs[-1])

    def doi_link(self, xs):
        return xs[-1]

    def doi_name(self, xs):
        return "/".join(xs)

    def arxiv(self, xs):
        return (IDType.ARXIV, str(xs[1]))

    def arxiv_code(self, xs):
        if len(xs) == 2:
            return ".".join(xs)
        else:
            return ".".join(xs[:-1])

    def isbn_code(self, xs):
        return "".join(xs)

    def isbn(self, xs):
        x = xs[-1]
        if len(x) == 10:
            return (IDType.ISBN10, x)
        else:
            return (IDType.ISBN13, x)


def idparse(s: str):
    """Identify the type of format followed by s

    Can be one of:
    1. ISBN (ISBN-10 or ISBN-13)
    3. DOI
    4. arXiv
    5. Title (book or article)
    """
    if not hasattr(idparse, "p"):
        setattr(
            idparse,
            "p",
            lark.Lark(
                """
?start: isbn
      | arxiv
      | doi

// Parse a DOI.

doi: doi_link "/"?
   | DOI_LITERAL doi_name

doi_link: HTTP? WWW? /doi.org\//i doi_name

doi_name: DOI_PREFIX "/" DOI_SUFFIX
DOI_PREFIX: ALNUM+ (("." | "-") ALNUM+)*
DOI_SUFFIX: ALNUM+ (("." | "-") ALNUM+)*
DOI_LITERAL: "doi:"

// Parse an arXiv identifier.

arxiv: arxiv_prefix arxiv_code ARXIV_CATEGORY? "/"?
arxiv_prefix: HTTP? WWW? ((/arxiv.org\//i (/(abs)|(pdf)/i) "/") | ARXIV_LITERAL)
arxiv_code: INT "." INT ARXIV_VERSION?

ARXIV_LITERAL.2: /arxiv:/i
ARXIV_CATEGORY: "[" WORD (("-" | ".") WORD)* "]"
ARXIV_VERSION: "v" INT

// Parse an ISBN number.

isbn: ISBN_PREFIX? isbn_code

isbn_code: INT ("-"? INT)*
ISBN_PREFIX: ISBN_LITERAL (/[-_]/? ("10" | "13") (" " | ":"))? ":"?

ISBN_LITERAL: /ISBN/i

// Common tokens.
HTTP: /https?:\/\//i
WWW: /www\./
ALNUM: DIGIT | LETTER

%import common.DIGIT
%import common.LETTER
%import common.INT
%import common.WORD
%ignore " "
""",
                parser="lalr",
            ).parse,
        )
    s = s.strip()
    try:
        tree = idparse.p(s)
        return MyTransformer().transform(tree)
    except:
        if "/" in s:
            return (IDType.DOI, s)
        else:
            return (IDType.TITLE, s)
