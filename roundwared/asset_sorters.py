import logging
from operator import itemgetter
import random
from roundware.rw import models
from datetime import date, timedelta


def order_assets_by_like(assets):
    unplayed = []
    for asset in assets:
        count = models.Asset.get_likes(asset)
        unplayed.append((count, asset))
    logging.info('Ordering Assets by Like. Input: ' +
                 str([(u[0], u[1].filename) for u in unplayed]))
    unplayed = sorted(unplayed, key=itemgetter(0), reverse=True)
    logging.info('Ordering Assets by Like. Output: ' +
                 str([(u[0], u[1].filename) for u in unplayed]))
    return [x[1] for x in unplayed]


def order_assets_by_weight(assets):
    unplayed = []
    for asset in assets:
        weight = asset.weight
        unplayed.append((weight, asset))
    logging.debug('Ordering Assets by Weight. Input: ' +
                  str([(u[0], u[1].filename) for u in unplayed]))
    unplayed = sorted(unplayed, key=itemgetter(0), reverse=True)
    logging.debug('Ordering Assets by Weight. Output: ' +
                  str([(u[0], u[1].filename) for u in unplayed]))
    return [x[1] for x in unplayed]


def order_assets_randomly(assets):
    logging.debug("Ordering Assets Randomly. Input: %s" % (assets,))
    random.shuffle(assets)
    logging.debug("Ordering Assets Randomly. Output: %s" % (assets,))
    return assets


def _within_10km(*args, **kwargs):
    if "assets" in kwargs and "request" in kwargs:
        assets = kwargs["assets"]
        listener = kwargs["request"]
    else:
        raise TypeError("Function requires assets=[] and request=")

    returning_assets = ([asset for asset in assets if asset.distance(listener) <= 10000])
    return returning_assets


def _ten_most_recent_days(*args, **kwargs):
    if "assets" in kwargs:
        assets = kwargs["assets"]
    else:
        raise TypeError("Function requires assets=[]")

    returning_assets = ([asset for asset in assets if date(asset.created.year, asset.created.month, asset.created.day) >= (date.today() - timedelta(10))])
    logging.debug("returning filtered assets: %s" % (returning_assets,))
    return returning_assets