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

import tempfile
import os
import re


def get_seconds(value):
    values = value.split(':')
    return float(values[0]) * 3600.0 + float(values[1]) * 60.0 +\
        float(values[2])


def getVideoDetails(filepath):
    tmpf = tempfile.NamedTemporaryFile()
    os.system("avconv -i \"%s\" 2> %s" % (filepath, tmpf.name))
    lines = tmpf.readlines()
    tmpf.close()
    metadata = {}
    metadata['video'] = {}
    metadata['audio'] = {}
    print(lines)
    metadata['duration'] = 0
    metadata['duration_in_seconds'] = 0
    metadata['bitrate'] = 0
    metadata['video']['resolution'] = 0
    metadata['video']['width'], metadata['video']['height'] = 0, 0
    metadata['video']['resolution'] = 0
    metadata['video']['bitrate'] = 0
    metadata['video']['fps'] = 0
    metadata['fps'] = 0
    metadata['audio']['codec'] = 0
    metadata['audio']['frequency'] = 0
    metadata['audio']['bitrate'] = 0
    for l in lines:
        l = l.decode()
        print(l)
        l = l.strip()
        if l.startswith('Duration'):
            metadata['duration'] = re.search('Duration: (.*?),', l).group(0).\
                split(':', 1)[1].strip(' ,')
            metadata['duration_in_seconds'] = get_seconds(metadata['duration'])
            metadata['bitrate'] = re.search("bitrate: (\d+ kb/s)", l).\
                group(0).split(':')[1].strip()
        if l.startswith('Stream #') and l.split(': ') == 'Video':
            metadata['video'] = {}
            try:
                metadata['video']['codec'], metadata['video']['profile'] = \
                    [e.strip(' , ()') for e in re.search(
                        'Video: (.*? \(.*?\)),? ', l).group(0).split(':')[1].
                        split('(')]
                metadata['video']['resolution'] = re.search('([1-9]\d+x\d+)',
                                                            l).group(1)
                metadata['video']['width'], metadata['video']['height'] =\
                    metadata['video']['resolution'].split('x')
                metadata['video']['width'] = float(metadata['video']['width'])
                metadata['video']['height'] = \
                    float(metadata['video']['height'])
                metadata['video']['bitrate'] = re.search('(\d+ kb/s)',
                                                         l).group(1)
                metadata['video']['fps'] = re.search('(\d+ fps)', l).group(1)
                metadata['fps'] = int(metadata['video']['fps'].split(' ')[0])
            except Exception:
                pass
        if l.startswith('Stream #') and l.split(': ') == 'Audio':
            try:
                metadata['audio'] = {}
                metadata['audio']['codec'] = re.search('Audio: (.*?) ',
                                                       l).group(1)
                metadata['audio']['frequency'] = re.search(', (.*? Hz),',
                                                           l).group(1)
                metadata['audio']['bitrate'] = re.search(', (\d+ kb/s)',
                                                         l).group(1)
            except Exception:
                pass
    return metadata
