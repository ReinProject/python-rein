import requests
import click

from util import unique

import config
rein = config.Config()

def safe_get(log, url):
    click.echo('GET {}'.format(url))
    log.info("GET {}".format(url))

    try:
        answer = requests.get(url=url, proxies=rein.proxies)
    except requests.ConnectionError:
        click.echo('Error connecting to server.')
        log.error('server connect error ' + url)
        return None

    try:
        json = answer.json()
        return json
    except:
        log.error('non-json return from http get')
        return None
