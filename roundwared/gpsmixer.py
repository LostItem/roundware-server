# Roundware Server is released under the GNU Affero General Public License v3.
# See COPYRIGHT.txt, AUTHORS.txt, and LICENSE.txt in the project root directory.

from __future__ import unicode_literals

import gobject

from roundware.rw.models import calculate_volume

gobject.threads_init()
import pygst
pygst.require("0.10")
import gst
import logging
import math
import httplib
import urlparse
import src_mp3_stream
logger = logging.getLogger(__name__)


class GPSMixer (gst.Bin):

    def __init__(self, listener, speakers):
        gst.Bin.__init__(self)
        self.sources = []
        self.speakers = []
        self.adder = gst.element_factory_make("adder")
        self.add(self.adder)
        pad = self.adder.get_pad("src")
        ghostpad = gst.GhostPad("src", pad)
        self.add_pad(ghostpad)
        addersinkpad = self.adder.get_request_pad('sink%d')
        logger.debug("Adding blank audio")
        blanksrc = BlankAudioSrc2()
        self.add(blanksrc)
        srcpad = blanksrc.get_pad('src')
        srcpad.link(addersinkpad)
        logger.debug("iterating through " + str(len(speakers)) + " speakers.")
        for speaker in speakers:
            vol = calculate_volume(speaker, listener)
            uri = None
            if check_stream(speaker.uri):
                uri = speaker.uri
                logger.debug("taking normal uri: " + uri)
            elif check_stream(speaker.backupuri):
                uri = speaker.backupuri
                logger.warning("Stream " + speaker.uri
                               + " is not a valid audio/mpeg stream."
                               + " using backup.")
            else:
                logger.warning("Stream " + speaker.uri
                               + " and backup "
                               #+ speaker['backupuri']
                               + " are not valid audio/mpeg streams."
                               + " Not adding anything.")
                continue

            logger.debug("vol is " + str(vol) + " for uri " + uri)
            if vol > 0:
                logger.debug("adding to bin")
                src = src_mp3_stream.SrcMP3Stream(uri, vol)
                self.add(src)
                srcpad = src.get_pad('src')
                addersinkpad = self.adder.get_request_pad('sink%d')
                srcpad.link(addersinkpad)
                self.sources.append(src)
            else:
                logger.debug("appending")
                self.sources.append(None)
            self.speakers.append(speaker)
        self.move_listener(listener)

    def move_listener(self, new_listener):
        self.listener = new_listener
        for i in range(len(self.speakers)):
            vol = calculate_volume(self.speakers[i], self.listener)
            logger.debug("Source # %s has a volume of %s" % (i, vol))
            if vol > 0:
                if self.sources[i] == None:
                    logger.debug("Allocating new source")
                    tempsrc = src_mp3_stream.SrcMP3Stream(
                        self.speakers[i].uri, vol)
                    self.sources[i] = tempsrc
                    logger.debug("Adding speaker: %s " % self.speakers[i].id)
                    self.add(self.sources[i])
                    # self.set_state(gst.STATE_PLAYING)

                    srcpad = self.sources[i].get_pad('src')
                    addersinkpad = self.adder.get_request_pad('sink%d')
                    srcpad.link(addersinkpad)
                    self.sources[i].set_state(gst.STATE_PLAYING)
                    # self.set_state(gst.STATE_PLAYING)
                else:
                    logger.debug("already added, setting vol: " + str(vol))
                    self.sources[i].set_volume(vol)

            else:
                if self.sources[i] != None:
                    self.sources[i].set_volume(vol)
                    src_to_remove = self.sources[i].get_pad('src')
                    # src_to_remove.set_blocked(True)
                    # we crash whenever we set state to NULL, either here or after unlinking
                    # self.sources[i].set_state(gst.STATE_NULL)
                    sinkpad = self.adder.get_request_pad("sink%d")
                    src_to_remove.unlink(sinkpad)
                    self.adder.release_request_pad(sinkpad)
                    # self.remove(self.sources[i])
                    logger.debug("Removed speaker: %s" % self.speakers[i].id)
                    # self.sources[i] = None
                    # self.set_state(gst.STATE_PLAYING)


def lg(x):
    return math.log(x) / math.log(2)


def distance_in_meters(lat1, lon1, lat2, lon2):
    return distance_in_km(lat1, lon1, lat2, lon2) * 1000


def distance_in_km(lat1, lon1, lat2, lon2):
    # logger.debug(str.format("distance_in_km: lat1: {0}, lon1: {1}, lat2: {2}, lon2: {3}", lat1, lon1, lat2, lon2))
    R = 6371
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2) * math.sin(dLat / 2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon / 2) * math.sin(dLon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = R * c
    return d


def check_stream(url):
    try:
        o = urlparse.urlparse(url)
        h = httplib.HTTPConnection(o.hostname, o.port, timeout=10)
        h.request('GET', o.path)
        r = h.getresponse()
        content_type = r.getheader('content-type')
        h.close()
        return content_type == 'audio/mpeg'
    except:
        return False


class BlankAudioSrc2 (gst.Bin):

    def __init__(self, wave=4):
        gst.Bin.__init__(self)
        audiotestsrc = gst.element_factory_make("audiotestsrc")
        audiotestsrc.set_property("wave", wave)  # 4 is silence
        audioconvert = gst.element_factory_make("audioconvert")
        self.add(audiotestsrc, audioconvert)
        audiotestsrc.link(audioconvert)
        pad = audioconvert.get_pad("src")
        ghost_pad = gst.GhostPad("src", pad)
        self.add_pad(ghost_pad)
