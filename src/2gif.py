#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# 2gif.py
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
#
#
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import GdkPixbuf
import webbrowser
import tempfile
import re
import comun
import shlex
import subprocess
import mimetypes
import os
import urllib
import urllib.request
import shutil
import threading
from videosnapshooter import VideoSnapShooter
import ctypes


_ = str

SUPPORTED_MIMES = ['video/x-ms-asf', 'video/x-msvideo', 'video/x-flv',
                   'video/quicktime', 'video/mp4', 'video/mpeg',
                   'video/x-ms-wmv', 'video/ogg', 'video/x-matroska']

GObject.threads_init()


def terminate_thread(thread):
    """Terminates a python thread from another thread.

    :param thread: a threading.Thread instance
    """
    if thread is None or not thread.isAlive():
        thread = None
        return

    exc = ctypes.py_object(SystemExit)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_long(thread.ident), exc)
    thread = None
    if res == 0:
        raise ValueError("nonexistent thread id")
    elif res > 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def ejecuta(comando):
    print(comando)
    args = shlex.split(comando)
    p = subprocess.Popen(args, bufsize=10000, stdout=subprocess.PIPE)
    valor = p.communicate()[0]
    return valor


def get_thumb_for_video(vss, start_position, output,
                        output_image):
    t = threading.Thread(target=_get_thumbnail_for_video, args=(vss,
                                                                start_position,
                                                                output,
                                                                output_image))
    t.daemon = True
    t.start()
    return t


def _get_thumbnail_for_video(vss, start_position, output, update_image):
    print('a')
    vss.snapshoot(output, start_position)
    print('b')
    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(output, 300, 300)
    print('c')
    update_image.set_from_pixbuf(pixbuf)
    print('d')


def _get_thumbnail_for_video2(filename, start_position, output, update_image):
    ejecuta('avconv -i "%s" -f image2 -ss %s -vf scale=-1:300 -vframes 1 %s -y'
            % (filename, start_position, output))
    update_image.set_from_file(output)


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


class Convert2GifDialog(Gtk.Window):
    def __init__(self):
        self.code = None
        Gtk.Window.__init__(self)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_title(comun.APPNAME)
        self.set_icon_from_file(comun.ICON)
        self.set_default_size(300, 300)
        self.connect('destroy', self.on_destroy)
        #
        self.vbox = Gtk.VBox(False, 2)
        self.add(self.vbox)
        table = Gtk.Table(4, 2, False)
        self.vbox.pack_end(table, False, False, 0)
        self.begin = Gtk.Image.new_from_file(comun.BACKGROUND)
        self.begin.set_tooltip_text('Drag and drop video here')
        table.attach(self.begin, 0, 1, 0, 1, xpadding=5, ypadding=5)
        self.end = Gtk.Image.new_from_file(comun.BACKGROUND_NONE)
        table.attach(self.end, 1, 2, 0, 1, xpadding=5, ypadding=5)
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
        self.spinbutton_begin.set_tooltip_text('First second')
        self.spinbutton_begin.set_editable(False)
        table.attach(self.spinbutton_begin, 0, 1, 1, 2,
                     xpadding=5,
                     ypadding=5,
                     xoptions=Gtk.AttachOptions.SHRINK)
        self.spinbutton_end = Gtk.SpinButton()
        self.spinbutton_end.set_tooltip_text('Last second')
        self.spinbutton_end.set_editable(False)
        table.attach(self.spinbutton_end, 1, 2, 1, 2,
                     xpadding=5,
                     ypadding=5,
                     xoptions=Gtk.AttachOptions.SHRINK)
        #
        self.button_output = Gtk.Button(
            os.path.join(os.path.expanduser('~'), 'output.gif'))
        self.button_output.connect('clicked', self.on_button_output_clicked)
        table.attach(self.button_output, 0, 2, 2, 3,
                     xpadding=5,
                     ypadding=5,
                     xoptions=Gtk.AttachOptions.SHRINK)
        #
        self.button_ok = Gtk.Button('Ok')
        self.button_ok.connect('clicked', self.on_button_ok_clicked)
        table.attach(self.button_ok, 0, 1, 3, 4,
                     xpadding=5,
                     ypadding=5,
                     xoptions=Gtk.AttachOptions.SHRINK)
        self.button_cancel = Gtk.Button('Cancel')
        self.button_cancel.connect('clicked', self.on_button_cancel_clicked)
        table.attach(self.button_cancel, 1, 2, 3, 4,
                     xpadding=5,
                     ypadding=5,
                     xoptions=Gtk.AttachOptions.SHRINK)
        #
        self.duration_in_seconds = 0
        self.fps = 0
        self.filename = None
        self.first_image_thread = None
        self.last_image_thread = None
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

    def load_file_dialog(self):
        filename = None
        dialog = Gtk.FileChooserDialog("Open file",
                                       self,
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
        self.menus['open-file'].connect('activate',
                                        self.on_toolbar_clicked,
                                        'open-file')
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
        self.fileh.set_submenu(self.get_help_menu())
        #
        menubar.append(self.fileh)

    def get_help_menu(self):
        help_menu = Gtk.Menu()
        #
        homepage_item = Gtk.MenuItem(label=_(
            'Homepage'))
        homepage_item.connect('activate',
                              lambda x: webbrowser.open(
                                'http://www.atareao.es/'))
        homepage_item.show()
        help_menu.append(homepage_item)
        #
        help_item = Gtk.MenuItem(label=_(
            'Get help online...'))
        help_item.connect('activate',
                          lambda x: webbrowser.open(
                            'https://answers.launchpad.net/utext'))
        help_item.show()
        help_menu.append(help_item)
        #
        translate_item = Gtk.MenuItem(label=_(
            'Translate this application...'))
        translate_item.connect('activate',
                               lambda x: webbrowser.open(
                                'https://translations.launchpad.net/utext'))
        translate_item.show()
        help_menu.append(translate_item)
        #
        bug_item = Gtk.MenuItem(label=_(
            'Report a bug...'))
        bug_item.connect('activate',
                         lambda x: webbrowser.open(
                            'https://bufs.launchpad.net/utext'))
        bug_item.show()
        help_menu.append(bug_item)
        #
        separator = Gtk.SeparatorMenuItem()
        separator.show()
        help_menu.append(separator)
        #
        twitter_item = Gtk.MenuItem(label=_(
            'Follow me in Twitter'))
        twitter_item.connect('activate',
                             lambda x: webbrowser.open(
                                'https://twitter.com/atareao'))
        twitter_item.show()
        help_menu.append(twitter_item)
        #
        googleplus_item = Gtk.MenuItem(label=_(
            'Follow me in Google+'))
        googleplus_item.connect('activate',
                                lambda x: webbrowser.open(
                                    'https://plus.google.com/\
118214486317320563625/posts'))
        googleplus_item.show()
        help_menu.append(googleplus_item)
        #
        facebook_item = Gtk.MenuItem(label=_(
            'Follow me in Facebook'))
        facebook_item.connect('activate',
                              lambda x: webbrowser.open(
                                'http://www.facebook.com/elatareao'))
        facebook_item.show()
        help_menu.append(facebook_item)
        #
        about_item = Gtk.MenuItem.new_with_label(_('About'))
        about_item.connect('activate', self.on_about_activate)
        about_item.show()
        separator = Gtk.SeparatorMenuItem()
        separator.show()
        help_menu.append(separator)
        help_menu.append(about_item)
        #
        help_menu.show()
        return help_menu

    def on_about_activate(self, widget):
        """Create and populate the about dialog."""
        about_dialog = Gtk.AboutDialog(parent=self)
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

    def on_toolbar_clicked(self, widget, option):
        if option == 'open-file':
            filename = self.load_file_dialog()
            if filename is not None:
                self.process_file(filename)

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

    def on_destroy(self):
        if os.path.exists(self.tmp_folder):
            shutil.rmtree(self.tmp_folder)
        if self.first_image_thread is not None:
            self.first_image_thread.kill()
        if self.last_image_thread is not None:
            self.last_image_thread.kill()

    def on_spinbutton_begin_value_changed(self, widget):
        terminate_thread(self.first_image_thread)
        if self.first_image_thread is None:
            value = self.spinbutton_begin.get_value()
            temp_begin_image = os.path.join(self.tmp_folder, 'begin.png')
            if os.path.exists(temp_begin_image):
                os.remove(temp_begin_image)
            self.first_image_thread = \
                _get_thumbnail_for_video(self.vss,
                                         value,
                                         temp_begin_image,
                                         self.begin)

    def on_spinbutton_end_value_changed(self, widget):
        terminate_thread(self.last_image_thread)
        if self.last_image_thread is None:
            value = self.spinbutton_end.get_value()
            temp_end_image = os.path.join(self.tmp_folder, 'end.png')
            if os.path.exists(temp_end_image):
                os.remove(temp_end_image)
            self.last_image_thread = \
                _get_thumbnail_for_video(self.vss,
                                         value,
                                         temp_end_image,
                                         self.end)

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
            '''
            self.vss.snapshootrate(self.tmp_folder,
                                   'out',
                                   start_position,
                                   end_position,
                                   1)
            '''
            ejecuta('avconv -t %s -ss %s -i "%s" -r 1/1 "%s"' %
                    (duration, start_position, self.filename,
                     os.path.join(self.tmp_folder, 'out%04d.png')))
            ejecuta('convert -delay 1x1 -loop 0 "%s" "%s"' %
                    (os.path.join(self.tmp_folder, 'out*.png'),
                     os.path.join(self.tmp_folder, 'temporal.gif')))
            ejecuta('convert -layers Optimize "%s" "%s"' %
                    (os.path.join(self.tmp_folder, 'temporal.gif'),
                     output_file))
            self.on_destroy()
            exit()

    def on_button_cancel_clicked(self, widget):
        self.on_destroy()
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
        self.vss = VideoSnapShooter(filename)
        mime = mimetypes.guess_type(self.filename)
        if os.path.exists(self.filename):
            mime = mimetypes.guess_type(self.filename)[0]
            if mime in SUPPORTED_MIMES:
                if self.first_image_thread is not None:
                    self.first_image_thread.kill()
                if self.last_image_thread is not None:
                    self.last_image_thread.kill()
                self.duration_in_seconds = int(self.vss.get_duration())
                self.spinbutton_begin.set_adjustment(
                    Gtk.Adjustment(0, 0, self.duration_in_seconds,
                                   1, 10, 0))
                self.spinbutton_begin.set_value(0)
                self.spinbutton_begin.set_editable(True)
                self.spinbutton_end.set_adjustment(
                    Gtk.Adjustment(self.duration_in_seconds, 0,
                                   self.duration_in_seconds, 1,
                                   10, 0))
                self.spinbutton_end.set_value(self.duration_in_seconds)
                self.spinbutton_end.set_editable(True)
                temp_begin_image = os.path.join(self.tmp_folder, 'begin.png')
                temp_end_image = os.path.join(self.tmp_folder, 'end.png')
                '''
                self.vss.snapshoot(temp_begin_image, 0)
                set_image_from_file_at_size(self.end, temp_end_image, 300, 300)
                #self.begin.set_from_file(temp_begin_image)
                self.vss.snapshoot(temp_end_image, self.duration_in_seconds)
                set_image_from_file_at_size(self.end, temp_end_image, 300, 300)
                #self.end.set_from_file(temp_end_image)
                '''
                '''
                print(1)
                terminate_thread(self.first_image_thread)
                self.first_image_thread = \
                    get_thumb_for_video(self.vss,
                                        0,
                                        temp_begin_image,
                                        self.begin)
                print(2)
                terminate_thread(self.last_image_thread)
                self.last_image_thread = \
                    get_thumb_for_video(self.vss,
                                        self.duration_in_seconds,
                                        temp_end_image,
                                        self.end)
                print(3)
                '''
if __name__ == '__main__':
    ld = Convert2GifDialog()
    Gtk.main()
