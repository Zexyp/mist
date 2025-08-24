from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from .log import *

def url_strip_utm(url: str) -> str:
    utm_parameters = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"}

    parsed_url = urlparse(url)
    query = parse_qs(parsed_url.query)

    if not any(param in query for param in utm_parameters):
        return url
    log_warning("removing utm params, better luck next time")

    query = {k: v for k, v in query.items() if k not in utm_parameters}

    pure_query = urlencode(query, doseq=True)
    pure_url = urlunparse(parsed_url._replace(query=pure_query))
    return pure_url

def url_strip_share_identifier(url: str) -> str:
    share_identifier_param = "si"

    parsed_url = urlparse(url)
    query = parse_qs(parsed_url.query)

    if not share_identifier_param:
        return url
    log_warning("removing share identifier param, better luck next time")

    query.pop(share_identifier_param, None)

    new_query = urlencode(query, doseq=True)
    pure_url = urlunparse(parsed_url._replace(query=new_query))
    return pure_url