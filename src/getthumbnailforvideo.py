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
    gi.require_version('GdkPixbuf', '2.0')
except Exception as e:
    print(e)
    exit(1)
from idleobject import IdleObject
from threading import Thread
from gi.repository import GObject
from gi.repository import GdkPixbuf
from videosnapshooter import VideoSnapShooter
import time

class GetThumbnailForVideo(IdleObject, Thread):
    __gsignals__ = {
        'finished': (GObject.SIGNAL_RUN_FIRST,
                     GObject.TYPE_NONE,
                     (GdkPixbuf.Pixbuf,))
        }

    def __init__(self, input_file, output_file, start_position):
        IdleObject.__init__(self)
        Thread.__init__(self)
        self.input_file = input_file
        self.output_file = output_file
        self.start_position = start_position
        self.daemon = True

    def run(self):
        emited = False
        contador = 0
        while ((not emited) and (contador < 3)):
            try:
                contador += 1
                vss = VideoSnapShooter(self.input_file)
                vss.snapshoot(self.output_file, self.start_position)
                time.sleep(0.5)
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
                    self.output_file, 300, 300)
                self.emit('finished', pixbuf)
                emited = True
            except Exception as e:
                time.sleep(0.5)
                print(e)
