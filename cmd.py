# -*- coding: utf-8 -*-
#
# ----------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# Peppe Bergqvist <p@bergqvi.st> wrote this file. As long as you retain this
# notice you can do whatever you want with this stuff. If we meet some day,
# and you think this stuff is worth it, you can buy me a beer in return.
# ----------------------------------------------------------------------------
#
from datetime import datetime
import optparse
import sys

from svtcrawler import SvtCrawler


def main():
    print '*********'
    print 'CRAWLING!'
    print '*********'

    obj = SvtCrawler()

    for b in obj.shows:

        print '\t', b.title, b.url

        print '\tKlipp:'
        for c in b.clips:
            print '\t\t', c.title, c.date_broadcasted

if __name__ == '__main__':
    main()

