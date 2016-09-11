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
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GdkPixbuf
import sys
import os
import webbrowser
from mainwindow import MainWindow
from preferences_dialog import PreferencesDialog
from supportdialog import SupportDialog
import comun
from comun import _

SUPPORTED_MIMES = ['video/x-ms-asf', 'video/x-msvideo', 'video/x-flv',
                   'video/quicktime', 'video/mp4', 'video/mpeg',
                   'video/x-ms-wmv', 'video/ogg', 'video/x-matroska']


class MainApplication(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(
            self,
            application_id='es.atareao.togif',
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        self.license_type = Gtk.License.GPL_3_0
        print(3)

    def do_shutdown(self):
        Gtk.Application.do_shutdown(self)

    def on_quit(self, widget, data):
        self.quit()

    def do_startup(self):
        Gtk.Application.do_startup(self)
        print('do_startup')

        def create_action(name,
                          callback=self.action_clicked,
                          var_type=None,
                          value=None):
            if var_type is None:
                action = Gio.SimpleAction.new(name, None)
            else:
                action = Gio.SimpleAction.new_stateful(
                    name,
                    GLib.VariantType.new(var_type),
                    GLib.Variant(var_type, value)
                )
            action.connect('activate', callback)
            return action

        self.add_action(create_action("add"))
        self.add_action(create_action("update"))
        self.add_action(create_action("quit", callback=lambda *_: self.quit()))
        self.add_action(create_action("save"))
        self.add_action(create_action("set_interval", var_type='i', value=30))

        self.set_accels_for_action('app.add', ['<Ctrl>A'])
        self.set_accels_for_action('app.quit', ['<Ctrl>Q'])

        self.add_action(create_action(
            'open_file',
            callback=self.on_open_file_clicked))
        self.add_action(create_action(
            'create_gif',
            callback=self.on_create_gif_clicked))
        self.add_action(create_action(
            'set_preferences',
            callback=self.on_preferences_clicked))
        self.add_action(create_action(
            'goto_homepage',
            callback=lambda x, y: webbrowser.open(
                'http://www.atareao.es/apps/\
crear-un-gif-animado-de-un-video-en-ubuntu-en-un-solo-clic/')))
        self.add_action(create_action(
            'goto_bug',
            callback=lambda x, y: webbrowser.open(
                    'https://bugs.launchpad.net/2gif')))
        self.add_action(create_action(
            'goto_sugestion',
            callback=lambda x, y: webbrowser.open(
                    'https://blueprints.launchpad.net/2gif')))
        self.add_action(create_action(
            'goto_translation',
            callback=lambda x, y: webbrowser.open(
                    'https://translations.launchpad.net/2gif')))
        self.add_action(create_action(
            'goto_questions',
            callback=lambda x, y: webbrowser.open(
                    'https://answers.launchpad.net/2gif')))
        self.add_action(create_action(
            'goto_twitter',
            callback=lambda x, y: webbrowser.open(
                    'https://twitter.com/atareao')))
        self.add_action(create_action(
            'goto_google_plus',
            callback=lambda x, y: webbrowser.open(
                    'https://plus.google.com/\
118214486317320563625/posts')))
        self.add_action(create_action(
            'goto_facebook',
            callback=lambda x, y: webbrowser.open(
                    'http://www.facebook.com/elatareao')))
        self.add_action(create_action(
            'goto_donate',
            callback=self.on_support_clicked))
        self.add_action(create_action(
            'about',
            callback=self.on_about_activate))

    def do_activate(self):
        print('activate')
        self.win = MainWindow(self)
        self.add_window(self.win)
        self.win.show()

    def action_clicked(self, action, variant):
        print(action, variant)
        if variant:
            action.set_state(variant)

    def on_support_clicked(self, widget, optional):
        dialog = SupportDialog(self.win)
        dialog.run()
        dialog.destroy()

    def on_create_gif_clicked(self, widget, optional):
        self.win.on_button_ok_clicked(widget)

    def on_open_file_clicked(self, widget, optional):
        filename = self.load_file_dialog()
        if filename is not None:
            self.win.process_file(filename)

    def on_button_output_clicked(self, widget):
        dialog = Gtk.FileChooserDialog('Select output file',
                                       self.win, Gtk.FileChooserAction.SAVE,
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
            self.win.button_output.set_label(filename)
        dialog.destroy()

    def on_about_activate(self, widget, optional):
        """Create and populate the about dialog."""
        about_dialog = Gtk.AboutDialog(parent=self.win)
        about_dialog.set_name(comun.APPNAME)
        about_dialog.set_version(comun.VERSION)
        about_dialog.set_copyright(
            'Copyrignt (c) 2015-2016\nLorenzo Carbonell Cerezo')
        about_dialog.set_comments(_('An app to convert video to gif'))
        about_dialog.set_license('''
This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.
''')
        about_dialog.set_website('http://www.atareao.es')
        about_dialog.set_website_label('http://www.atareao.es')
        about_dialog.set_authors([
            'Lorenzo Carbonell <https://launchpad.net/~lorenzo-carbonell>'])
        about_dialog.set_documenters([
            'Lorenzo Carbonell <https://launchpad.net/~lorenzo-carbonell>'])
        about_dialog.set_translator_credits('''
Lorenzo Carbonell <https://launchpad.net/~lorenzo-carbonell>\n
''')
        about_dialog.set_icon(GdkPixbuf.Pixbuf.new_from_file(comun.ICON))
        about_dialog.set_logo(GdkPixbuf.Pixbuf.new_from_file(comun.ICON))
        about_dialog.set_program_name(comun.APPNAME)
        about_dialog.run()
        about_dialog.destroy()

    def on_preferences_clicked(self, widget, optional):
        cm = PreferencesDialog(self.win)
        if cm.run() == Gtk.ResponseType.ACCEPT:
            cm.close_ok()
        cm.destroy()

    def load_file_dialog(self):
        filename = None
        dialog = Gtk.FileChooserDialog(_('Open file'),
                                       self.win,
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL,
                                        Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN,
                                        Gtk.ResponseType.OK))
        dialog.set_current_folder(os.path.expanduser("~"))
        filter_video = Gtk.FileFilter()
        filter_video.set_name(_('Video files'))
        for amimetype in SUPPORTED_MIMES:
            filter_video.add_mime_type(amimetype)
        dialog.add_filter(filter_video)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
        elif response == Gtk.ResponseType.CANCEL:
            pass
        dialog.destroy()
        return filename


def main():
    app = MainApplication()
    app.run('')

if __name__ == '__main__':
    main()
