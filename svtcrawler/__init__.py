# -*- coding: utf-8 -*-
#
# ----------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# Peppe Bergqvist <p@bergqvi.st> wrote this file. As long as you retain this
# notice you can do whatever you want with this stuff. If we meet some day,
# and you think this stuff is worth it, you can buy me a beer in return.
# ----------------------------------------------------------------------------
#

from datetime import datetime, timedelta
from urllib2 import HTTPError
from pytz import timezone, utc
from dateutil.parser import parse, parserinfo
from pyquery import PyQuery

TIME_ZONE = 'Europe/Stockholm'


class sverje(parserinfo):
    WEEKDAYS = [(u"Mån", u"Måndag"),
                ("Ti", "Tis", "Tisdag"),
                ("On", "Ons", "Onsdag"),
                ("To", "Tor", "Torsdag"),
                ("Fr", "Fre", "Fredag"),
                (u"Lör", u"Lördag"),
                (u"Sön", u"Söndag")]
    MONTHS   = [("Jan", "Januari"),
                ("Feb", "Februari"),
                ("Mar", "Mars"),
                ("Apr", "April"),
                ("May", "Maj"),
                ("Jun", "Juni"),
                ("Jul", "Juli"),
                ("Aug", "Augusti"),
                ("Sep", "Sept", "September"),
                ("Okt", "Oktober"),
                ("Nov", "November"),
                ("Dec", "December")]


def shellquote(s):
    s = s.replace('/', '-')
    valid_chars = u' -_.():0123456789abcdefghijklmnpoqrstuvwxyzåäöABCDEFGHIJKLMNOPQRSTUVZXYZÅÄÖ'
    s = ''.join(c for c in s if c in valid_chars)
    s = s.strip()

    return s


def numerics(s):
    n = 0
    for c in s:
        if not c.isdigit():
            return n
        else:
            n = n * 10 + int(c)
    return n


def swe_to_eng_date(s):
    rep = [
        ('maj', 'may'),
        ('okt', 'oct'),
        ('tor', 'thu'),
        ('fre', 'fri'),
        ('ons', 'wed'),
        ('tis', 'tue'),
        ('mån', 'mon')
    ]
    for a in rep:

        s = s.replace(a[0], a[1])

    return s


def parse_date(datum, typ):
    datum = unicode(datum)
    tz = timezone(TIME_ZONE)
    current_timezone = datetime.utcnow().replace(tzinfo=tz)
    if datum.find('dag') != -1:
        days = numerics(datum)
        if typ == '+':
            ret = current_timezone + timedelta(days=days)
        else:
            ret = current_timezone - timedelta(days=days)
    elif datum.find('tim') != -1:
        hours = numerics(datum)
        if typ == '+':
            ret = current_timezone + timedelta(hours=hours)
        else:
            ret = current_timezone - timedelta(hours=hours)
    else:
        return current_timezone

    return ret


def sanitize_description(value):
    cleaned = PyQuery(value)
    cleaned = cleaned.remove('span.playMetaText')
    cleaned.remove('span.playMetaText')
    cleaned.remove('time')
    cleaned.remove('strong')

    return cleaned.html().split('<span>')[-1:][0].replace('</span>', '')


class Show:
    def __init__(self, title, url, thumbnail):
        self.title = title
        self.url = url


class Episode:
    pass


class Episodes:
    def __init__(self, crawler, url):
        self.crawler = crawler
        self.i = 0
        self.kind_of = 'ee'

        self.episodes = PyQuery(url)
        self.episodes_iter = self.episodes.find('article.svtUnit')


    def __iter__(self):
        return self

    def __len__(self):
        return len(self.episodes_iter)

    def next(self):
        if self.i == self.episodes_iter.length:
            raise StopIteration

        # Index all episodes
        link = self.episodes_iter[self.i]

        # Parse the current episode from the long list of episodes
        article = PyQuery(link)
        episode = article.find('a')
        full_url = article.find('a').attr('href')
        broadcasted = article.find('time').attr('datetime')

        if len(broadcasted) < 1:
            broadcasted = '1970-01-01 00:00:00'

        #Check if the url contains an extra /Random-Title, if so, remove it
        if len(full_url.split('/')) == 6:
            url = full_url.rpartition('/')[0]
        else:
            url = full_url

        if (url.find('video') != -1) and len(broadcasted) > 1:

            available = parse_date(article.attr('data-available'), '+')

            try:
                # Get the episode from url
                article_full = PyQuery(url)
                thumbnail = article_full.find('img.svtHide-No-Js').eq(0).attr('data-imagename')
                playerLink = article_full.find('a#player')
                if PyQuery(playerLink).attr('data-available-on-mobile'):
                    on_device = 1
                else:
                    on_device = 2

                desc = article_full.find('.svt-text-bread').text()
                desc = sanitize_description(unicode(desc))
                episodeTitle = article_full.find('title').eq(0).text().replace('| oppetarkiv.se', '')
                length = playerLink.attr('data-length')

                episode = Episode()
                episode.title = episodeTitle
                episode.title_slug = shellquote(episodeTitle)
                episode.http_status = 200
                episode.http_status_checked_date = datetime.utcnow().replace(tzinfo=utc)
                episode.date_available_until = available
                episode.date_broadcasted = broadcasted
                episode.length = length
                episode.description = desc
                episode.viewable_on_device = on_device
                # episode.viewable_in = rights
                episode.kind_of = self.kind_of
                episode.thumbnail_url = thumbnail

                self.i += 1
                return episode

            except HTTPError as err:
                self.i += 1
                return self.next()


class Shows:
    def __init__(self, crawler):
        self.crawler = crawler
        self.categories = PyQuery(self.crawler.url)
        self.categories_iter = self.categories.find("li.svtoa-anchor-list-item a")
        self.i = 0

    def __iter__(self):
        return self

    def next(self):
        if self.i == self.categories_iter.length:
            raise StopIteration

        link = self.categories_iter[self.i]

        py_link = PyQuery(link)
        href = py_link.attr('href')
        html_class = href.split('/')[-1:][0]
        title = py_link.text()
        # thumbnail_url = self.crawler.baseurl + PyQuery(link).find('img').attr('src')
        url = href

        show = Show(title, url, html_class)
        show.clips = Episodes(self.crawler, url)

        self.i += 1
        return show


class SvtCrawler:
    def __init__(self):
        self.timezone = 'Europe/Stockholm'
        self.baseurl = 'http://www.svtplay.se'
        self.url = 'http://www.oppetarkiv.se/kategori/titel'
        self.category_url = 'http://www.svtplay.se%s/?tab=titles&sida=1000'

        self.shows = Shows(self)

