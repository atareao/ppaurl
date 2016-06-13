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
except Exception as e:
    print(e)
    exit(1)
from gi.repository import Gtk
import comun
import os
import shutil
from comun import _
from configurator import Configuration


class PreferencesDialog(Gtk.Dialog):
    def __init__(self, parent):
        #
        Gtk.Dialog.__init__(self,
                            '2Gif | '+_('Preferences'),
                            parent,
                            Gtk.DialogFlags.MODAL |
                            Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                                Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_icon_from_file(comun.ICON)
        #
        vbox0 = Gtk.VBox(spacing=5)
        vbox0.set_border_width(5)
        self.get_content_area().add(vbox0)
        # ***************************************************************
        notebook = Gtk.Notebook.new()
        vbox0.add(notebook)
        # ***************************************************************
        vbox11 = Gtk.VBox(spacing=5)
        vbox11.set_border_width(5)
        notebook.append_page(vbox11, Gtk.Label.new(_('General')))
        frame11 = Gtk.Frame()
        vbox11.pack_start(frame11, False, True, 1)
        table11 = Gtk.Table(2, 3, False)
        frame11.add(table11)
        # ***************************************************************
        label11 = Gtk.Label(_('Frames per second')+':')
        label11.set_alignment(0, 0.5)
        table11.attach(label11, 0, 1, 0, 1, xpadding=5, ypadding=5)
        adjustment4 = Gtk.Adjustment(8, 1, 100, 1, 5, 1)
        self.sample_time = Gtk.SpinButton()
        self.sample_time.set_adjustment(adjustment4)
        table11.attach(self.sample_time, 1, 2, 0, 1,
                       xpadding=5,
                       ypadding=5,
                       xoptions=Gtk.AttachOptions.SHRINK)
        label12 = Gtk.Label(_('Scale')+':')
        label12.set_alignment(0, 0.5)
        table11.attach(label12, 0, 1, 1, 2, xpadding=5, ypadding=5)
        self.scale = Gtk.Switch()
        self.scale.connect('state-set', self.on_scale)
        table11.attach(self.scale, 1, 2, 1, 2,
                       xpadding=5,
                       ypadding=5,
                       xoptions=Gtk.AttachOptions.SHRINK)
        label14 = Gtk.Label(_('Width')+':')
        label14.set_alignment(0, 0.5)
        table11.attach(label14, 0, 1, 3, 4, xpadding=5, ypadding=5)
        self.modify_width = Gtk.Switch()
        self.modify_width.set_sensitive(False)
        self.modify_width.connect('state-set', self.on_modify_width)
        table11.attach(self.modify_width, 1, 2, 3, 4,
                       xpadding=5,
                       ypadding=5,
                       xoptions=Gtk.AttachOptions.SHRINK)
        adjustment_width = Gtk.Adjustment(1, 1, 10025, 1, 5, 1)
        self.width = Gtk.SpinButton()
        self.width.set_sensitive(False)
        self.width.set_adjustment(adjustment_width)
        self.width.set_sensitive(False)
        table11.attach(self.width, 2, 3, 3, 4,
                       xpadding=5,
                       ypadding=5,
                       xoptions=Gtk.AttachOptions.SHRINK)
        label15 = Gtk.Label(_('Height')+':')
        label15.set_alignment(0, 0.5)
        table11.attach(label15, 0, 1, 4, 5, xpadding=5, ypadding=5)
        self.modify_height = Gtk.Switch()
        self.modify_height.set_sensitive(False)
        self.modify_height.connect('state-set', self.on_modify_height)
        table11.attach(self.modify_height, 1, 2, 4, 5,
                       xpadding=5,
                       ypadding=5,
                       xoptions=Gtk.AttachOptions.SHRINK)
        adjustment_height = Gtk.Adjustment(1, 1, 10025, 1, 5, 1)
        self.height = Gtk.SpinButton()
        self.height.set_sensitive(False)
        self.height.set_adjustment(adjustment_height)
        table11.attach(self.height, 2, 3, 4, 5,
                       xpadding=5,
                       ypadding=5,
                       xoptions=Gtk.AttachOptions.SHRINK)
        #
        self.load_preferences()
        self.show_all()

    def on_scale(self, widget, data):
        self.modify_width.set_sensitive(data)
        self.width.set_sensitive(data & self.modify_width.get_active())
        self.modify_height.set_sensitive(data)
        self.height.set_sensitive(data & self.modify_height.get_active())

    def on_modify_width(self, widget, data):
        self.width.set_sensitive(data & self.scale.get_active())

    def on_modify_height(self, widget, data):
        self.height.set_sensitive(data & self.scale.get_active())

    def load_preferences(self):
        configuration = Configuration()
        self.sample_time.set_value(configuration.get('frames'))
        self.scale.set_active(configuration.get('scale'))
        self.modify_width.set_active(configuration.get('modify-width'))
        self.width.set_value(configuration.get('width'))
        self.modify_height.set_active(configuration.get('modify-height'))
        self.height.set_value(configuration.get('height'))

    def save_preferences(self):
        configuration = Configuration()
        configuration.set('frame', self.sample_time.get_value())
        configuration.set('scale', self.scale.get_active())
        configuration.set('modify-width', self.modify_width.get_active())
        configuration.set('width', self.width.get_value())
        configuration.set('modify-height', self.modify_height.get_active())
        configuration.set('height', self.height.get_value())
        configuration.save()

if __name__ == "__main__":
    cm = PreferencesDialog(None)
    if cm.run() == Gtk.ResponseType.ACCEPT:
        print(1)
        cm.close_ok()
    cm.hide()
    cm.destroy()
    exit(0)
