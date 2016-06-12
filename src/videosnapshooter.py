#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of 2gif
#
# Copyright (C) 2015-2016 Lorenzo Carbonell
# lorenzo.carbonell.cerezo@gmail.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import gi
try:
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gst', '1.0')
except Exception as e:
    print(e)
    exit(1)
from gi.repository import Gtk
from gi.repository import Gst
import sys
import os

Gtk.init(None)
Gst.init(None)


class VideoSnapShooter():
    def __init__(self, videofilename):
        descr = 'uridecodebin uri=file://%s ! videoconvert ! videoscale !\
gdkpixbufsink name=sink' % (videofilename)
        self.pipeline = Gst.parse_launch(descr)
        self.sink = self.pipeline.get_by_name('sink')
        ret = self.pipeline.set_state(Gst.State.PAUSED)
        if ret == Gst.StateChangeReturn.FAILURE:
            print('failed to play the file (1)\n')
        elif ret == Gst.StateChangeReturn.NO_PREROLL:
            print('live sources not supported yet\n')
        ret = self.pipeline.get_state(5 * Gst.SECOND)
        if ret[0] == Gst.StateChangeReturn.FAILURE:
            print('failed to play the file (2)\n')
        self.duration = self.pipeline.query_duration(Gst.Format.TIME)[1]

    def get_duration(self):
        return self.duration/Gst.SECOND

    def firstsnapshoot(self, screenshootfilename):
        self.snapshoot(screenshootfilename, 0)

    def lastsnapshoot(self, screenshootfilename):
        self.snapshoot(screenshootfilename, self.get_duration())

    def snapshoot(self, screenshotfilename, position):
        position = position * Gst.SECOND
        ret = self.pipeline.seek_simple(Gst.Format.TIME,
                                        Gst.SeekFlags.KEY_UNIT |
                                        Gst.SeekFlags.FLUSH,
                                        position)
        ret = self.pipeline.get_state(5 * Gst.SECOND)
        # error check
        if not ret:
            print('failed to seek forward\n')
            sys.exit()
        if ret == Gst.StateChangeReturn.FAILURE:
            print('failed to play the file (1)\n')
            sys.exit()
        elif ret == Gst.StateChangeReturn.NO_PREROLL:
            print('live sources not supported yet\n')
        pixbuf = self.sink.props.last_pixbuf
        if pixbuf is not None:
            pixbuf.savev(screenshotfilename, "png", [], [])

    def ft(self, value, maxvalue):
        return (len(str(maxvalue))-len(str(value)))*'0'+str(value)

    def snapshootrate(self, pathfolder, filename, starttime=-1, endtime=-1,
                      framerate=0.5):
        if starttime < 0:
            starttime = 0
        if endtime < 0 or endtime < starttime or endtime > self.get_duration():
            endtime = self.get_duration()
        snaps = int((endtime - starttime)/framerate)
        position = starttime
        for i in range(snaps):
            screenshotfilename = os.path.join(pathfolder,
                                              filename + self.ft(i, snaps) +
                                              '.png')
            self.snapshoot(screenshotfilename, position)
            position += framerate

if __name__ == '__main__':
    image = '/home/lorenzo/Escritorio/sample.png'
    firstimage = '/home/lorenzo/Escritorio/first-sample.png'
    lastimage = '/home/lorenzo/Escritorio/last-sample.png'
    video = '/home/lorenzo/sample.mkv'
    vss = VideoSnapShooter(video)
    print(vss.get_duration())
    vss.snapshoot(image, 3)
    vss.firstsnapshoot(firstimage)
    vss.lastsnapshoot(lastimage)
    vss.snapshootrate('/home/lorenzo/Escritorio/samples', 'sample')
