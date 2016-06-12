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

from idleobject import IdleObject
from threading import Thread
from gi.repository import GObject
import subprocess
import re
import shlex


def timestr_to_seconds(time_str):
        hours, minutes, seconds = time_str.split(':')
        return float(hours) * 3600.0 + float(minutes) * 60.0 + float(seconds)


class ConvertVideo(IdleObject, Thread):
    __gsignals__ = {
        'processed': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (int,)),
        'interrupted': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ()),
        'finished': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ()),
        }

    def __init__(self, input_file, output_file, start_position, duration,
                 frames, scale_t):
        IdleObject.__init__(self)
        Thread.__init__(self)
        self.input_file = input_file
        self.output_file = output_file
        self.start_position = start_position
        self.duration = duration
        self.frames = frames
        self.scale_t = scale_t
        self.daemon = True
        self.stop = False

    def stop_it(self, anobject=None):
        self.stop = True

    def run(self):
        comando = 'avconv -t %s -ss %s -i "%s" -r %s %s "%s"' % (
            self.duration, self.start_position, self.input_file, self.frames,
            self.scale_t, self.output_file)
        args = shlex.split(comando)
        p = subprocess.Popen(args, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, close_fds=True)
        contador = 0
        for line in p.stdout:
            line = line.decode().rstrip()
            m = re.search('time=([0-9,\.\:]+)\ bitrate=', line)
            if m:
                contador += 1
                found = m.group(1)
                self.emit('processed',
                          int(timestr_to_seconds(found)/float(98)*100.0))
                if self.stop:
                    p.kill()
                    self.emit('interrupted')
        self.emit('finished')
