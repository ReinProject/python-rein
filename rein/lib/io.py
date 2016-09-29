import requests
import click

from validate import filter_and_parse_valid_sigs
from util import unique


def remote_query(rein, user, urls, log, query_type, distinct):
    '''
    Sends specific query to registered servers and filters for uniqueness
    '''
    res = []
    for url in urls:
        sel_url = "{0}query?owner={1}&query={2}&testnet={3}"
        data = safe_get(log, sel_url.format(url, user.maddr, query_type, rein.testnet))
        if data is None or query_type not in data or len(data[query_type]) == 0:
            click.echo('None found')
        res += filter_and_parse_valid_sigs(rein, data[query_type])
    return unique(res, distinct)


def safe_get(log, url):
    log.info("GET {0}".format(url))

    try:
        answer = requests.get(url=url)
    except:
        click.echo('Error connecting to server.')
        log.error('server connect error ' + url)
        return None

    try:
        json = answer.json()
        return json
    except:
        log.error('non-json return from http get')
        return answer
