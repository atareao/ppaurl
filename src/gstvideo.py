#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# webcam.py
#
# This file is part of Backlight Indicator
#
# Copyright (C) 2016
# Lorenzo Carbonell Cerezo <lorenzo.carbonell.cerezo@gmail.com>
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
from gi.repository import Gst
from PIL import Image
from PIL import ImageStat
import os
import sys
import time
import tempfile
try:
    gi.require_version('Gst', '1.0')
except Exception as e:
    print(e)
    exit(1)

Gst.init(None)


class GstVideo:
    def __init__(self, filename):
        self.temp_file = tempfile.NamedTemporaryFile(
            prefix='tmp_calculate_backlight_').name + '.jpg'
        self.pipeline = Gst.Pipeline()
        src = Gst.ElementFactory.make('uridecodebin', None)
        src.set_property('uri', 'file://%s' % (filename))
        print('file://%s' % (filename))
        filter1 = Gst.ElementFactory.make('videoconvert', None)
        filter2 = Gst.ElementFactory.make('videoscale', None)
        sink = Gst.ElementFactory.make('gdkpixbufsink', 'sink')
        sink.set_property('name', 'sink')
        self.pipeline.add(src)
        self.pipeline.add(filter1)
        self.pipeline.add(filter2)
        self.pipeline.add(sink)
        src.link(filter1)
        filter1.link(filter2)
        filter2.link(sink)
        ret = self.pipeline.set_state(Gst.State.PAUSED)
        print(ret)
        if ret == Gst.StateChangeReturn.FAILURE:
            print('failed to play the file (1)\n')
        elif ret == Gst.StateChangeReturn.NO_PREROLL:
            print('live sources not supported yet\n')
        duration = self.pipeline.query_duration(Gst.Format.TIME)[1]
        print('duration', duration)
        ret = self.pipeline.get_state(1 * Gst.SECOND)
        print(ret)
        #  error check
        if ret[0] == Gst.StateChangeReturn.FAILURE:
            print('failed to play the file (2)\n')
            # sys.exit()
        # getting the duration
        # choices besides TIME to put thru query_duration?
        duration = self.pipeline.query_duration(Gst.Format.TIME)[1]
        print('duration', duration)
        pixbuf = sink.props.last_pixbuf
        h = pixbuf.get_height()
        w = pixbuf.get_width()
        rowstride = w*3 + (w*3 % 4)
        print(w, h)


        caps = Gst.Caps.from_string("image/png")
        self.pipeline.set_state(Gst.State.PAUSED)
        self.pipeline.get_state(Gst.CLOCK_TIME_NONE)
        offset = 1
        assert self.pipeline.seek_simple(Gst.Format.TIME,
                                         Gst.SeekFlags.FLUSH,
                                         offset * Gst.SECOND)
        sample = self.pipeline.emit('convert-sample', caps)
        self.buffer = self.pipeline.emit('convert-sample', caps).get_buffer()
        self.pipeline.set_state(Gst.State.NULL)
        '''
        filter1 = Gst.ElementFactory.make('videoconvert', None)
        filter2 = Gst.ElementFactory.make('videoscale', None)
        filter3 = Gst.ElementFactory.make('videorate', None)
        caps = Gst.Caps.from_string('video/x-raw, framerate=1/1')
        camerafilter = Gst.ElementFactory.make("capsfilter", "capsfilter")
        camerafilter.set_property('caps', caps)
        filter4 = Gst.ElementFactory.make('jpegenc', None)
        filter5 = Gst.ElementFactory.make('multifilesink', None)
        # filter5.set_property('location', 'test%010d.jpg')
        filter5.set_property('location', self.temp_file)
        self.pipeline.add(src)
        self.pipeline.add(filter1)
        self.pipeline.add(filter2)
        self.pipeline.add(filter3)
        self.pipeline.add(camerafilter)
        self.pipeline.add(filter4)
        self.pipeline.add(filter5)
        src.link(filter1)
        filter1.link(filter2)
        filter2.link(filter3)
        filter3.link(camerafilter)
        camerafilter.link(filter4)
        filter4.link(filter5)
        '''

    def create(self):
        with file('frame.png', 'w') as fh:
            # This (i.e. getting the data from the buffer) does not work. See https://bugzilla.gnome.org/show_bug.cgi?id=678663
            fh.write(bytes(self.buffer))
    def get_backlight(self):
        self.pipeline.set_state(Gst.State.PLAYING)
        time.sleep(5)
        self.pipeline.set_state(Gst.State.NULL)
        im = Image.open(self.temp_file).convert('L')
        stat = ImageStat.Stat(im)
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)
        return int(stat.rms[0]/255.0*100)


if __name__ == '__main__':
    gstVideo = GstVideo('/home/lorenzo/out.ogv')
