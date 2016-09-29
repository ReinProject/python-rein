import requests
import click

from util import unique


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
