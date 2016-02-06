#! /usr/bin/python3
# -*- coding: utf-8 -*-
#
#
# LoginDialog
# 
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
from gi.repository import Gtk, Gdk
from gi.repository import GObject
import tempfile, re, math
import comun, shlex, subprocess, mimetypes, os
import urllib, urllib.request
import shutil
import threading

SUPPORTED_MIMES = ['video/x-ms-asf','video/x-msvideo','video/x-flv','video/quicktime','video/mp4','video/mpeg','video/x-ms-wmv']



GObject.threads_init()


def ejecuta(comando):
	print(comando)
	args = shlex.split(comando)
	p = subprocess.Popen(args, bufsize=10000, stdout=subprocess.PIPE)
	valor = p.communicate()[0]
	return valor
def get_thumbnail_for_video_thread(filename,start_position,output, output_image):
	t = threading.Thread(target=get_thumbnail_for_video,args=(filename,start_position,output,output_image))
	t.daemon = True
	t.start()
	
	
def get_thumbnail_for_video(filename,start_position,output, update_image):
	ejecuta('ffmpeg -i "%s" -f image2 -ss %s -vf scale=-1:300 -vframes 1 %s -y'%(filename,start_position,output))
	update_image.set_from_file(output)

def get_seconds(value):
	values = value.split(':')
	return float(values[0])*3600.0 + float(values[1])*60.0 + float(values[2])
def getVideoDetails(filepath):
	tmpf = tempfile.NamedTemporaryFile()
	os.system("ffmpeg -i \"%s\" 2> %s" % (filepath, tmpf.name))
	lines = tmpf.readlines()
	tmpf.close()
	metadata = {}
	print(lines)
	for l in lines:
		l = l.decode()
		print(l)
		l = l.strip()
		if l.startswith('Duration'):
			metadata['duration'] = re.search('Duration: (.*?),', l).group(0).split(':',1)[1].strip(' ,')
			metadata['duration_in_seconds'] = get_seconds(metadata['duration'])
			metadata['bitrate'] = re.search("bitrate: (\d+ kb/s)", l).group(0).split(':')[1].strip()
		if l.startswith('Stream #0:0'):
			metadata['video'] = {}
			try:
				metadata['video']['codec'], metadata['video']['profile'] = \
				[e.strip(' ,()') for e in re.search('Video: (.*? \(.*?\)),? ', l).group(0).split(':')[1].split('(')]
			except Exception:
				pass
			metadata['video']['resolution'] = re.search('([1-9]\d+x\d+)', l).group(1)
			metadata['video']['width'],metadata['video']['height'] = metadata['video']['resolution'].split('x')
			metadata['video']['width'] = float(metadata['video']['width'])
			metadata['video']['height'] = float(metadata['video']['height'])
			metadata['video']['bitrate'] = re.search('(\d+ kb/s)', l).group(1)
			metadata['video']['fps'] = re.search('(\d+ fps)', l).group(1)
			metadata['fps'] = int(metadata['video']['fps'].split(' ')[0])
		if l.startswith('Stream #0:1'):
			metadata['audio'] = {}
			metadata['audio']['codec'] = re.search('Audio: (.*?) ', l).group(1)
			metadata['audio']['frequency'] = re.search(', (.*? Hz),', l).group(1)
			metadata['audio']['bitrate'] = re.search(', (\d+ kb/s)', l).group(1)
	return metadata
	
class Convert2WebpDialog(Gtk.Dialog):
	def __init__(self):
		self.code = None
		Gtk.Dialog.__init__(self)
		self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
		self.set_title(comun.APPNAME)
		self.set_icon_from_file(comun.ICON)
		self.set_default_size(300, 300)
		self.connect('destroy', self.on_destroy)
		#
		table = Gtk.Table(4, 2, False)
		self.get_content_area().add(table)
		self.begin = Gtk.Image.new_from_file(comun.BACKGROUND)
		self.begin.set_tooltip_text('Drag and drop video here')
		table.attach(self.begin,0,1,0,1, xpadding=5, ypadding=5)
		self.end = Gtk.Image.new_from_file(comun.BACKGROUND_NONE)
		table.attach(self.end,1,2,0,1, xpadding=5, ypadding=5)
		# set icon for drag operation
		self.begin.connect('drag-begin', self.drag_begin)
		self.begin.connect('drag-data-get', self.drag_data_get_data)
		self.begin.connect('drag-data-received',self.drag_data_received)
		#
		dnd_list = [Gtk.TargetEntry.new('text/uri-list', 0, 100),Gtk.TargetEntry.new('text/plain', 0, 80)]
		self.begin.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, dnd_list, Gdk.DragAction.COPY)
		self.begin.drag_source_add_uri_targets()
		dnd_list = Gtk.TargetEntry.new("text/uri-list", 0, 0)
		self.begin.drag_dest_set(Gtk.DestDefaults.MOTION | Gtk.DestDefaults.HIGHLIGHT | Gtk.DestDefaults.DROP,[dnd_list],Gdk.DragAction.MOVE )
		self.begin.drag_dest_add_uri_targets()
		#
		self.spinbutton_begin = Gtk.SpinButton()
		self.spinbutton_begin.set_tooltip_text('First second')
		self.spinbutton_begin.set_editable(False)
		self.spinbutton_begin.connect('value-changed',self.on_spinbutton_begin_value_changed)
		table.attach(self.spinbutton_begin,0,1,1,2, xpadding=5, ypadding=5, xoptions=Gtk.AttachOptions.SHRINK)
		self.spinbutton_end = Gtk.SpinButton()
		self.spinbutton_end.set_tooltip_text('Last second')
		self.spinbutton_end.set_editable(False)
		self.spinbutton_end.connect('value-changed',self.on_spinbutton_end_value_changed)
		table.attach(self.spinbutton_end,1,2,1,2, xpadding=5, ypadding=5, xoptions=Gtk.AttachOptions.SHRINK)
		#
		self.button_output = Gtk.Button(os.path.join(os.path.expanduser('~'),'output.gif'))
		self.button_output.connect('clicked',self.on_button_output_clicked)
		table.attach(self.button_output,0,2,2,3, xpadding=5, ypadding=5, xoptions=Gtk.AttachOptions.SHRINK)
		#
		self.button_ok = Gtk.Button('Ok')
		self.button_ok.connect('clicked',self.on_button_ok_clicked)
		table.attach(self.button_ok,0,1,3,4, xpadding=5, ypadding=5, xoptions=Gtk.AttachOptions.SHRINK)
		self.button_cancel = Gtk.Button('Cancel')
		self.button_cancel.connect('clicked',self.on_button_cancel_clicked)
		table.attach(self.button_cancel,1,2,3,4, xpadding=5, ypadding=5, xoptions=Gtk.AttachOptions.SHRINK)
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
		self.show_all()
		
	def on_button_output_clicked(self,widget):
		dialog =Gtk.FileChooserDialog('Select output file',None,Gtk.FileChooserAction.SAVE,(Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
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
		
	def on_spinbutton_begin_value_changed(self,widget):
		min_value = self.spinbutton_begin.get_value()
		max_value = self.duration_in_seconds		
		if self.spinbutton_end.get_value()<min_value:
			self.spinbutton_end.set_adjustment(Gtk.Adjustment(min_value, min_value,max_value, 1, 10, 0))
			self.spinbutton_end.set_value(min_value)
		else:		
			self.spinbutton_end.set_adjustment(Gtk.Adjustment(self.spinbutton_end.get_value(), min_value,max_value, 1, 10, 0))
		temporal_image = os.path.join(self.tmp_folder,'begin.png')
		if os.path.exists(temporal_image):
			os.remove(temporal_image)
		if self.first_image_thread is not None:
			self.first_image_thread.kill()
		self.first_image_thread = get_thumbnail_for_video_thread(self.filename,min_value,temporal_image,self.begin)

	def on_spinbutton_end_value_changed(self,widget):
		value = self.spinbutton_end.get_value()
		temporal_image = os.path.join(self.tmp_folder,'end.png')
		if os.path.exists(temporal_image):
			os.remove(temporal_image)
		if self.last_image_thread is not None:
			self.last_image_thread.kill()
		self.last_image_thread = get_thumbnail_for_video_thread(self.filename,value,temporal_image,self.end)
		

	def on_button_ok_clicked(self,widget):
		start_position = self.spinbutton_begin.get_value()
		end_position = self.spinbutton_end.get_value()
		duration = end_position-start_position
		output_file = self.button_output.get_label()
		if os.path.exists(output_file):
			os.remove(output_file)
		if os.path.exists(output_file+'.tmp'):
			os.remove(output_file+'.tmp')
		if os.path.exists(self.filename) and duration>0:
			#ejecuta('ffmpeg -t %s -ss %s -i "%s" -r 1/%s "%s"'%(duration,start_position,self.filename,self.fps, os.path.join(self.tmp_folder,'out%04d.png')))
			ejecuta('ffmpeg -t %s -ss %s -i "%s" -r 1/1 "%s"'%(duration,start_position,self.filename, os.path.join(self.tmp_folder,'out%04d.png')))
			#ejecuta('convert -delay 1x%s -loop 0 "%s" "%s"'%(self.fps,os.path.join(self.tmp_folder,'out*.png'),output_file+'.tmp'))
			ejecuta('convert -delay 1x1 -loop 0 "%s" "%s"'%(os.path.join(self.tmp_folder,'out*.png'),os.path.join(self.tmp_folder,'temporal.gif')))
			ejecuta('convert -layers Optimize "%s" "%s"'%(os.path.join(self.tmp_folder,'temporal.gif'),output_file))
			self.on_destroy()
			exit()
	
	def on_button_cancel_clicked(self,widget):
		self.on_destroy()
		exit()

	def drag_begin(self, widget, context):
		pass

	def drag_data_get_data(self, treeview, context, selection, target_id, etime):
		pass

	def drag_data_received(self,widget, drag_context, x, y, selection_data, info, timestamp):
		for filename in selection_data.get_uris():
			if len(filename)>8:
				filename = urllib.request.url2pathname(filename)
				self.filename = filename[7:]
				mime = mimetypes.guess_type(self.filename)
				if os.path.exists(self.filename):
					mime = mimetypes.guess_type(self.filename)[0]
					if mime in SUPPORTED_MIMES:
						if self.first_image_thread is not None:
							self.first_image_thread.kill()
						if self.last_image_thread is not None:
							self.last_image_thread.kill()						
						metadata = getVideoDetails(self.filename)
						self.fps = metadata['fps']
						self.duration_in_seconds = int(metadata['duration_in_seconds'])
						self.spinbutton_begin.set_adjustment(Gtk.Adjustment(0, 0, self.duration_in_seconds, 1, 10, 0))
						self.spinbutton_begin.set_value(0)
						self.spinbutton_begin.set_editable(True)
						self.spinbutton_end.set_adjustment(Gtk.Adjustment(self.duration_in_seconds, 0,self.duration_in_seconds, 1, 10, 0))
						self.spinbutton_end.set_value(self.duration_in_seconds)
						self.spinbutton_end.set_editable(True)
						#f = open(self.filename)
						
						temporal_begin_image = os.path.join(self.tmp_folder,'begin.png')
						temporal_end_image = os.path.join(self.tmp_folder,'end.png')
						
						#filename,start_position,output, update_image):
						self.first_image_thread = get_thumbnail_for_video_thread(self.filename,0,temporal_begin_image,self.begin)
						self.last_image_thread = get_thumbnail_for_video_thread(self.filename,self.duration_in_seconds-1,temporal_end_image,self.end)
						destinationfilename,originalextension = os.path.splitext(filename)
						destinationfilename+='.webp'
						quality = 80
						'''
						t = threading.Thread(target=ejecuta,args=('cwebp -q %s %s -o %s'%(quality,filename,destinationfilename),))
						t.daemon = True
						t.start()
						'''
		return True

if __name__ == '__main__':
	ld = Convert2WebpDialog()
	ld.run()
