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
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GObject
import os
import tempfile
import shutil
import urllib
import urllib.request
import mimetypes
import comun
from comun import _
from videosnapshooter import VideoSnapShooter
from getthumbnailforvideo import GetThumbnailForVideo
from configurator import Configuration
from progreso import Progreso
from convertvideo import ConvertVideo

SUPPORTED_MIMES = ['video/x-ms-asf', 'video/x-msvideo', 'video/x-flv',
                   'video/quicktime', 'video/mp4', 'video/mpeg',
                   'video/x-ms-wmv', 'video/ogg', 'video/x-matroska']


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        Gtk.ApplicationWindow.__init__(self, application=app)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_icon_from_file(comun.ICON)
        self.connect('destroy', self.on_destroy)
        #
        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.props.title = comun.APPNAME
        self.set_titlebar(hb)

        menu_button_open = Gio.Menu()
        menu_button_open.append_item(
            Gio.MenuItem.new(_('Open video file'), 'app.open_file'))

        button_open = Gtk.MenuButton()
        button_open.add(Gtk.Image.new_from_gicon(
            Gio.ThemedIcon.new_with_default_fallbacks(
                'document-open-symbolic'),
            Gtk.IconSize.BUTTON))
        button_open.set_menu_model(menu_button_open)
        hb.pack_start(button_open)
        #
        menu_button_about = Gio.Menu()
        menu_button_about.append_item(
            Gio.MenuItem.new(_('Homepage'), 'app.goto_homepage'))
        menu_button_about.append_item(
            Gio.MenuItem.new(_('Report a bug'), 'app.goto_bug'))
        menu_button_about.append_item(
            Gio.MenuItem.new(_('Make a suggestion'),
                             'app.goto_sugestion'))
        menu_button_about.append_item(
            Gio.MenuItem.new(_('Translate this application'),
                             'app.goto_translation'))
        menu_button_about.append_item(
            Gio.MenuItem.new(_('Get help online'),
                             'app.goto_questions'))
        menu_button_about.append_item(
            Gio.MenuItem.new('', None))
        menu_button_about.append_item(
            Gio.MenuItem.new(_('Follow me on Twitter'),
                             'app.goto_twitter'))
        menu_button_about.append_item(
            Gio.MenuItem.new(_('Follow me on Facebook'),
                             'app.goto_facebook'))
        menu_button_about.append_item(
            Gio.MenuItem.new(_('Follow me on Google+'),
                             'app.goto_google_plus'))
        menu_button_about.append_item(
            Gio.MenuItem.new('', None))
        menu_button_about.append_item(
            Gio.MenuItem.new(_('Donate'),
                             'app.goto_donate'))
        menu_button_about.append_item(
            Gio.MenuItem.new('', None))
        menu_button_about.append_item(
            Gio.MenuItem.new(_('About...'),
                             'app.about'))

        button_about = Gtk.MenuButton()
        button_about.add(
            Gtk.Image.new_from_gicon(
                Gio.ThemedIcon.new_with_default_fallbacks(
                    'dialog-information-symbolic'),
                Gtk.IconSize.BUTTON))
        button_about.set_menu_model(menu_button_about)
        hb.pack_end(button_about)

        menu_button_preferences = Gio.Menu()
        menu_button_preferences.append_item(
            Gio.MenuItem.new(_('Configuration'), 'app.set_preferences'))

        button_preferences = Gtk.MenuButton()
        button_preferences.add(
            Gtk.Image.new_from_gicon(
                Gio.ThemedIcon.new_with_default_fallbacks(
                    'preferences-system-symbolic'),
                Gtk.IconSize.BUTTON))
        button_preferences.set_menu_model(menu_button_preferences)
        hb.pack_end(button_preferences)
        #
        hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)
        self.add(hbox)
        self.vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
        hbox.pack_start(self.vbox, False, False, 5)
        frame = Gtk.Frame()
        self.vbox.pack_start(frame, True, True, 5)
        table = Gtk.Table(4, 2, False)
        frame.add(table)
        self.begin = Gtk.Image.new_from_file(comun.BACKGROUND)
        self.begin.set_tooltip_text(_('Drag and drop video here'))
        table.attach(self.begin, 0, 1, 0, 1,
                     xpadding=5,
                     ypadding=5,
                     xoptions=Gtk.AttachOptions.SHRINK,
                     yoptions=Gtk.AttachOptions.EXPAND)
        self.end = Gtk.Image.new_from_file(comun.BACKGROUND_NONE)
        table.attach(self.end, 1, 2, 0, 1,
                     xpadding=5,
                     ypadding=5,
                     xoptions=Gtk.AttachOptions.SHRINK,
                     yoptions=Gtk.AttachOptions.EXPAND)

        # set icon for drag operation
        self.begin.connect('drag-begin', self.drag_begin)
        self.begin.connect('drag-data-get', self.drag_data_get_data)
        self.begin.connect('drag-data-received', self.drag_data_received)
        #
        dnd_list = [Gtk.TargetEntry.new('text/uri-list', 0, 100),
                    Gtk.TargetEntry.new('text/plain', 0, 80)]
        self.begin.drag_source_set(Gdk.ModifierType.BUTTON1_MASK,
                                   dnd_list,
                                   Gdk.DragAction.COPY)
        self.begin.drag_source_add_uri_targets()
        dnd_list = Gtk.TargetEntry.new("text/uri-list", 0, 0)
        self.begin.drag_dest_set(Gtk.DestDefaults.MOTION |
                                 Gtk.DestDefaults.HIGHLIGHT |
                                 Gtk.DestDefaults.DROP,
                                 [dnd_list],
                                 Gdk.DragAction.MOVE)
        self.begin.drag_dest_add_uri_targets()
        #
        self.spinbutton_begin = Gtk.SpinButton()
        self.spinbutton_begin.set_tooltip_text(_('First second'))
        self.spinbutton_begin.set_editable(False)
        table.attach(self.spinbutton_begin, 0, 1, 1, 2,
                     xpadding=5,
                     ypadding=5,
                     xoptions=Gtk.AttachOptions.SHRINK,
                     yoptions=Gtk.AttachOptions.SHRINK)
        self.spinbutton_end = Gtk.SpinButton()
        self.spinbutton_end.set_tooltip_text(_('Last second'))
        self.spinbutton_end.set_editable(False)
        table.attach(self.spinbutton_end, 1, 2, 1, 2,
                     xpadding=5,
                     ypadding=5,
                     xoptions=Gtk.AttachOptions.SHRINK,
                     yoptions=Gtk.AttachOptions.SHRINK)
        #
        self.button_output = Gtk.Button(
            os.path.join(os.path.expanduser('~'), 'output.gif'))
        self.button_output.connect('clicked', self.on_button_output_clicked)
        table.attach(self.button_output, 0, 2, 2, 3,
                     xpadding=5,
                     ypadding=5,
                     xoptions=Gtk.AttachOptions.SHRINK,
                     yoptions=Gtk.AttachOptions.SHRINK)
        #
        hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)
        self.vbox.pack_start(hbox, False, False, 5)

        self.button_ok = Gtk.Button.new_from_stock(Gtk.STOCK_EXECUTE)
        self.button_ok.connect('clicked', self.on_button_ok_clicked)
        hbox.pack_start(self.button_ok, False, False, 5)
        self.button_cancel = Gtk.Button.new_from_stock(Gtk.STOCK_QUIT)
        self.button_cancel.connect('clicked', self.on_button_cancel_clicked)
        hbox.pack_end(self.button_cancel, False, False, 5)
        #
        self.duration_in_seconds = 0
        self.fps = 0
        self.filename = None
        self.tmp_folder = tempfile.mkdtemp()
        if os.path.exists(self.tmp_folder):
            shutil.rmtree(self.tmp_folder)
            os.makedirs(self.tmp_folder)
        #
        self.init_menu()
        #
        self.spinbutton_begin.connect('value-changed',
                                      self.on_spinbutton_begin_value_changed)
        self.spinbutton_end.connect('value-changed',
                                    self.on_spinbutton_end_value_changed)
        self.show_all()

    def init_menu(self):
        menubar = Gtk.MenuBar()
        self.vbox.pack_start(menubar, False, False, 0)
        accel_group = Gtk.AccelGroup()
        self.add_accel_group(accel_group)
        self.filemenu = Gtk.Menu.new()
        self.filem = Gtk.MenuItem.new_with_label(_('File'))
        self.filem.set_submenu(self.filemenu)
        #
        self.menus = {}
        #
        self.menus['open-file'] = Gtk.ImageMenuItem.new_with_label(_(
            'Open file'))
        self.menus['open-file'].add_accelerator('activate',
                                                accel_group,
                                                ord('O'),
                                                Gdk.ModifierType.CONTROL_MASK,
                                                Gtk.AccelFlags.VISIBLE)
        self.filemenu.append(self.menus['open-file'])
        #
        self.filemenu.append(Gtk.SeparatorMenuItem())
        menubar.append(self.filem)
        #
        self.filehelp = Gtk.Menu.new()
        self.fileh = Gtk.MenuItem.new_with_label(_('Help'))
        #
        menubar.append(self.fileh)

    def on_button_output_clicked(self, widget):
        dialog = Gtk.FileChooserDialog('Select output file',
                                       None, Gtk.FileChooserAction.SAVE,
                                       (Gtk.STOCK_CANCEL,
                                        Gtk.ResponseType.REJECT,
                                        Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        dialog.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        dialog.set_filename(self.button_output.get_label())
        dialog.set_current_name(self.button_output.get_label().split('/')[-1])
        filter = Gtk.FileFilter()
        filter.set_name('Gif file')
        filter.add_mime_type("image/gif")
        dialog.add_filter(filter)
        if dialog.run() == Gtk.ResponseType.ACCEPT:
            dialog.hide()
            filename = dialog.get_filename()
            if not filename.endswith('.gif'):
                filename += '.gif'
            self.button_output.set_label(filename)
        dialog.destroy()

    def on_destroy(self, widget):
        if os.path.exists(self.tmp_folder):
            shutil.rmtree(self.tmp_folder)

    def on_spinbutton_begin_value_changed(self, widget):
        value = self.spinbutton_begin.get_value()
        temp_begin_image = os.path.join(self.tmp_folder, 'begin.png')
        if os.path.exists(temp_begin_image):
            os.remove(temp_begin_image)
        gtfv = GetThumbnailForVideo(self.filename, temp_begin_image, value)
        gtfv.connect('finished', self.on_get_thumbnailforvideo_begin)
        gtfv.start()

    def on_get_thumbnailforvideo_begin(self, anobject, pixbuf):
        self.begin.set_from_pixbuf(pixbuf)

    def on_spinbutton_end_value_changed(self, widget):
        value = self.spinbutton_end.get_value()
        temp_end_image = os.path.join(self.tmp_folder, 'end.png')
        if os.path.exists(temp_end_image):
            os.remove(temp_end_image)
        gtfv = GetThumbnailForVideo(self.filename, temp_end_image, value)
        gtfv.connect('finished', self.on_get_thumbnailforvideo_end)
        gtfv.start()

    def on_get_thumbnailforvideo_end(self, anobject, pixbuf):
        self.end.set_from_pixbuf(pixbuf)

    def on_button_ok_clicked(self, widget):
        start_position = self.spinbutton_begin.get_value()
        end_position = self.spinbutton_end.get_value()
        duration = end_position - start_position
        output_file = self.button_output.get_label()
        if os.path.exists(output_file):
            os.remove(output_file)
        if os.path.exists(output_file + '.tmp'):
            os.remove(output_file + '.tmp')
        if self.filename is not None and\
                os.path.exists(self.filename) and duration > 0:
            configuration = Configuration()
            frames = configuration.get('frames')
            scale = configuration.get('scale')
            modify_width = configuration.get('modify-width')
            width = configuration.get('width')
            modify_height = configuration.get('modify-height')
            height = configuration.get('height')
            if scale is True:
                if modify_width is True:
                    t_width = str(width)
                else:
                    t_width = '-1'
                if modify_height is True:
                    t_height = str(height)
                else:
                    t_height = '-1'
                if t_width != '-1' or t_height != '-1':
                    scale_t = ' -vf scale=%s:%s ' % (t_width, t_height)
                else:
                    scale_t = ''
            else:
                scale_t = ''
            # input_file, output_file, start_position, duration,
            #             frames, scale_t):
            progreso = Progreso(_('Converting video'), self, 100)
            convertVideo = ConvertVideo(self.filename, output_file,
                                        start_position, duration, frames,
                                        scale_t)
            progreso.connect('i-want-stop', convertVideo.stop_it)
            convertVideo.connect('processed', progreso.set_value)
            convertVideo.connect('interrupted', progreso.close)
            convertVideo.start()
            progreso.run()

    def on_button_cancel_clicked(self, widget):
        self.on_destroy(None)
        exit()

    def drag_begin(self, widget, context):
        pass

    def drag_data_get_data(self, treeview, context, selection, target_id,
                           etime):
        pass

    def drag_data_received(self, widget, drag_context, x, y, selection_data,
                           info, timestamp):
        if len(selection_data.get_uris()) > 0:
            filename = selection_data.get_uris()[0]
            if len(filename) > 8:
                filename = urllib.request.url2pathname(filename)
                self.process_file(filename[7:])
        return True

    def process_file(self, filename):
        self.filename = filename
        vss = VideoSnapShooter(filename)
        mime = mimetypes.guess_type(self.filename)
        if os.path.exists(self.filename):
            mime = mimetypes.guess_type(self.filename)[0]
            if mime in SUPPORTED_MIMES:
                self.duration_in_seconds = int(vss.get_duration())
                self.spinbutton_begin.set_value(0)
                self.spinbutton_begin.set_editable(True)
                self.spinbutton_begin.set_adjustment(
                    Gtk.Adjustment(0, 0, self.duration_in_seconds,
                                   1, 10, 0))
                self.spinbutton_end.set_value(self.duration_in_seconds)
                self.spinbutton_end.set_editable(True)
                self.spinbutton_end.set_adjustment(
                    Gtk.Adjustment(self.duration_in_seconds, 0,
                                   self.duration_in_seconds, 1,
                                   10, 0))


def main():
    GObject.threads_init()
    mw = MainWindow(None)
    mw.show_all()
    Gtk.main()
    exit(1)

if __name__ == '__main__':
    main()
