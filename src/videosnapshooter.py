#!/usr/bin/env python3

from gi.repository import Gtk
from gi.repository import Gst
import sys
import os

Gtk.init(None)
Gst.init(None)


class VideoSnapShooter():
    def __init__(self, videofilename):
        descr = 'uridecodebin uri=file://%s ! videoconvert ! videoscale !\
gdkpixbufsink name=sink' % (videofilename)
        self.pipeline = Gst.parse_launch(descr)
        self.sink = self.pipeline.get_by_name('sink')
        ret = self.pipeline.set_state(Gst.State.PAUSED)
        if ret == Gst.StateChangeReturn.FAILURE:
            print('failed to play the file (1)\n')
        elif ret == Gst.StateChangeReturn.NO_PREROLL:
            print('live sources not supported yet\n')
        ret = self.pipeline.get_state(5 * Gst.SECOND)
        if ret[0] == Gst.StateChangeReturn.FAILURE:
            print('failed to play the file (2)\n')
        self.duration = self.pipeline.query_duration(Gst.Format.TIME)[1]

    def get_duration(self):
        return self.duration/Gst.SECOND

    def firstsnapshoot(self, screenshootfilename):
        self.snapshoot(screenshootfilename, 0)

    def lastsnapshoot(self, screenshootfilename):
        self.snapshoot(screenshootfilename, self.get_duration())

    def snapshoot(self, screenshotfilename, position):
        position = position * Gst.SECOND
        ret = self.pipeline.seek_simple(Gst.Format.TIME,
                                        Gst.SeekFlags.KEY_UNIT |
                                        Gst.SeekFlags.FLUSH,
                                        position)
        ret = self.pipeline.get_state(5 * Gst.SECOND)
        # error check
        if not ret:
            print('failed to seek forward\n')
            sys.exit()
        if ret == Gst.StateChangeReturn.FAILURE:
            print('failed to play the file (1)\n')
            sys.exit()
        elif ret == Gst.StateChangeReturn.NO_PREROLL:
            print('live sources not supported yet\n')
        pixbuf = self.sink.props.last_pixbuf
        pixbuf.savev(screenshotfilename, "png", [], [])

    def ft(self, value, maxvalue):
        return (len(str(maxvalue))-len(str(value)))*'0'+str(value)

    def snapshootrate(self, pathfolder, filename, starttime=-1, endtime=-1,
                      framerate=0.5):
        if starttime < 0:
            starttime = 0
        if endtime < 0 or endtime < starttime or endtime > self.get_duration():
            endtime = self.get_duration()
        snaps = int((endtime - starttime)/framerate)
        position = starttime
        for i in range(snaps):
            screenshotfilename = os.path.join(pathfolder,
                                              filename + self.ft(i, snaps) +
                                              '.png')
            self.snapshoot(screenshotfilename, position)
            position += framerate

if __name__ == '__main__':
    image = '/home/lorenzo/Escritorio/sample.png'
    firstimage = '/home/lorenzo/Escritorio/first-sample.png'
    lastimage = '/home/lorenzo/Escritorio/last-sample.png'
    video = '/home/lorenzo/sample.mkv'
    vss = VideoSnapShooter(video)
    print(vss.get_duration())
    vss.snapshoot(image, 3)
    vss.firstsnapshoot(firstimage)
    vss.lastsnapshoot(lastimage)
    vss.snapshootrate('/home/lorenzo/Escritorio/samples', 'sample')
