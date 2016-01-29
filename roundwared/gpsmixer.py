# Roundware Server is released under the GNU Affero General Public License v3.
# See COPYRIGHT.txt, AUTHORS.txt, and LICENSE.txt in the project root directory.

from __future__ import unicode_literals

import gobject
import time
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db.models import Q

from roundware.rw.models import calculate_volume, Speaker

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

    def __init__(self, listener, project):
        gst.Bin.__init__(self)

        self.project = project

        self.sources = {}
        self.speakers = {}
        self.known_speakers = {}

        logger.debug("initializing GPSMixer")

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

        self.move_listener(listener)

    def inspect_speaker(self, speaker):

        if not self.known_speakers.get(speaker.id, False):
            if check_stream(speaker.uri):
                uri = speaker.uri
                logger.debug("taking normal uri: " + uri)
            elif check_stream(speaker.backupuri):
                uri = speaker.backupuri
                logger.warning("Stream " + speaker.uri + " is not a valid audio/mpeg stream. using backup.")
            else:
                logger.warning("Stream " + speaker.uri + " and backup are not valid audio/mpeg streams.")
                uri = None

            self.known_speakers[speaker.id] = {'speaker': speaker, 'uri': uri}

        return self.known_speakers.get(speaker.id)

    def remove_speaker_from_stream(self, speaker):
        source = self.sources.get(speaker.id, None)
        self.speakers[speaker.id] = None

        if not source:
            return

        logger.debug("fading audio to 0 before removing")
        source.set_volume(0)
        src_to_remove = source.get_pad('src')
        sinkpad = self.adder.get_request_pad("sink%d")
        src_to_remove.unlink(sinkpad)
        self.adder.release_request_pad(sinkpad)
        self.remove(src_to_remove)

        self.sources[speaker.id] = None


    def add_speaker_to_stream(self, speaker, volume):
        validated_speaker = self.inspect_speaker(speaker)
        if validated_speaker['uri']:
            tempsrc = src_mp3_stream.SrcMP3Stream(validated_speaker['uri'], volume)
            self.sources[speaker.id] = tempsrc
            logger.debug("Allocated new source: {}".format(self.sources[speaker.id]))

            logger.debug("Adding speaker: {} ".format(speaker.id))

            self.add(self.sources[speaker.id])
            srcpad = self.sources[speaker.id].get_pad('src')
            addersinkpad = self.adder.get_request_pad('sink%d')
            srcpad.link(addersinkpad)

            # see if the state changes at all...
            current_state = self.sources[speaker.id].get_state()
            logger.debug("current state of {source}: {current_state}".format(source=self.sources[speaker.id],
                                                                             current_state=current_state))
            time.sleep(2)
            current_state = self.sources[speaker.id].get_state()
            logger.debug("current state of {source}: {current_state}".format(source=self.sources[speaker.id],
                                                                             current_state=current_state))

            self.speakers[speaker.id] = speaker
        else:
            logger.debug("No valid uri for speaker")

    def set_speaker_volume(self, speaker, volume):
        source = self.sources.get(speaker.id, None)

        if not source:
            self.add_speaker_to_stream(speaker, volume)
        else:
            logger.debug("already added, setting vol: " + str(volume))
            source.set_volume(volume)

    def get_current_speakers(self):
        logger.info("filtering speakers")
        listener = Point(float(self.listener['longitude']), float(self.listener['latitude']))

        # get active speakers for this project, and select from those all speakers our listener is inside
        # and additionally all speakers with a minvolume greater than 0
        speakers = Speaker.objects.filter(activeyn=True, project=self.project).filter(
            Q(shape__dwithin=(listener, D(m=0))) | Q(minvolume__gt=0)
        )

        logger.info(speakers)

        # make sure all the current speakers are registered in the self.speakers dict
        for s in speakers:
            self.speakers[s.id] = s

        return list(speakers)

    def move_listener(self, new_listener):

        self.listener = new_listener

        current_speakers = self.get_current_speakers()

        for _, speaker in self.speakers.items():

            if speaker in current_speakers:
                vol = calculate_volume(speaker, self.listener)
            else:
                # set speakers that are not in range to minvolume
                vol = speaker.minvolume


            if vol == 0:
                logger.debug("Speaker {} is off, removing from stream".format(speaker.id))
                self.remove_speaker_from_stream(speaker)
                logger.debug("Removed speaker: %s" % speaker.id)
            else:
                logger.debug("Source # %s has a volume of %s" % (speaker.id, vol))
                self.set_speaker_volume(speaker, vol)


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
