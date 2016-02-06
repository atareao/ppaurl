#! /usr/bin/python3
# -*- coding: iso-8859-1 -*-
#
# com.py
#
# Copyright (C) 2012 Lorenzo Carbonell
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
#
#
#
__author__ = 'Lorenzo Carbonell <lorenzo.carbonell.cerezo@gmail.com>'
__date__ ='$07/01/2012'
__copyright__ = 'Copyright (c) 2011 Lorenzo Carbonell'
__license__ = 'GPLV3'
__url__ = 'http://www.atareao.es'
__version__ = '0.0.1.0'

import os
import locale
import gettext

######################################

def is_package():
	return __file__.find('src') < 0

######################################


VERSION = __version__
APP = '2gif'
APPNAME = '2gif'
APP_CONF = APP + '.conf'
CONFIG_DIR = os.path.join(os.path.expanduser('~'),'.config')
CONFIG_APP_DIR = os.path.join(CONFIG_DIR, APP)
# check if running from source
if is_package():
	ROOTDIR = '/opt/extras.ubuntu.com/2gif'
	APPDIR = os.path.join(ROOTDIR, 'share/2gif')
	LANGDIR = os.path.join(ROOTDIR, 'locale-langpack')
	BINDIR = os.path.join(ROOTDIR, 'bin')
	ICONDIR = os.path.join(ROOTDIR, 'share/icons')
	PIXMAPDIR = os.path.join(ROOTDIR, 'share/pixmaps')
else:
	VERSION = VERSION + '-src'
	ROOTDIR = os.path.dirname(__file__)
	LANGDIR = os.path.normpath(os.path.join(ROOTDIR, '../template1'))
	APPDIR = ROOTDIR
	ICONDIR = os.path.normpath(os.path.join(ROOTDIR, '../data'))
	PIXMAPDIR = ICONDIR
#
ICON = os.path.join(ICONDIR,'2gif.png')
BACKGROUND = os.path.join(PIXMAPDIR,'background.svg')
BACKGROUND_NONE = os.path.join(PIXMAPDIR,'background_none.svg')

try:
	current_locale, encoding = locale.getdefaultlocale()
	language = gettext.translation(APP, LANGDIR, [current_locale])
	language.install()
	if sys.version_info[0] == 3:
		_ = language.gettext
	else:
		_ = language.ugettext
except Exception as e:
	print(e)
	_ = str
