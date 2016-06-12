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
from gi.repository import GdkPixbuf
import webbrowser
import comun
from comun import _


class SupportDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self,
                            '2Gif | '+_('Donate'),
                            parent,
                            Gtk.DialogFlags.MODAL |
                            Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_size_request(300, 300)
        self.connect('close', self.close_ok)
        self.set_icon_from_file(comun.ICON)
        #
        hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)
        hbox.set_border_width(5)
        self.get_content_area().add(hbox)
        vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
        vbox.set_border_width(5)
        hbox.pack_start(vbox, True, True, 5)
        frame = Gtk.Frame()
        vbox.pack_start(frame, True, True, 5)
        internal_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
        frame.add(internal_box)
        label = Gtk.Label()
        label.set_markup('<b>%s</b>' % ('Help to support 2Gif'))
        internal_box.pack_start(label, False, False, 5)
        internal_box.pack_start(
            Gtk.Image.new_from_pixbuf(
                GdkPixbuf.Pixbuf.new_from_file_at_size(comun.ICON, 150, -1)),
            False, False, 5)
        internal_box.pack_start(Gtk.Label(_('Via')+':'), False, False, 5)
        logo1 = Gtk.EventBox()
        logo1.add(Gtk.Image.new_from_pixbuf(
             GdkPixbuf.Pixbuf.new_from_file_at_size(
                comun.PAYPAL_LOGO, 150, -1,)))
        logo1.connect('button_press_event',
                      self.on_support_clicked)
        internal_box.pack_start(logo1, False, False, 5)
        logo2 = Gtk.EventBox()
        logo2.add(Gtk.Image.new_from_pixbuf(
             GdkPixbuf.Pixbuf.new_from_file_at_size(
                comun.BITCOIN_LOGO, 150, -1,)))
        logo2.connect('button_press_event',
                      self.on_support_clicked)
        internal_box.pack_start(logo2, False, False, 5)
        logo3 = Gtk.EventBox()
        logo3.add(Gtk.Image.new_from_pixbuf(
             GdkPixbuf.Pixbuf.new_from_file_at_size(
                comun.FLATTR_LOGO, 150, -1,)))
        logo3.connect('button_press_event',
                      self.on_support_clicked)
        internal_box.pack_start(logo3, False, False, 5)
        self.show_all()

    def close_ok(self, widget):
        pass

    def on_support_clicked(self, widget, optional):
        webbrowser.open('http://www.atareao.es/donar/')
        self.destroy()

if __name__ == "__main__":
    dialog = SupportDialog(None)
    if dialog.run() == Gtk.ResponseType.ACCEPT:
        print(1)
        dialog.close_ok()
    dialog.hide()
    dialog.destroy()
    exit(0)
