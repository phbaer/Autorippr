# -*- coding: utf-8 -*-
"""
FileBot class


Released under the MIT license
Copyright (c) 2012, Jason Millward

@category   misc
@version    $Id: 1.7.0, 2016-08-22 14:53:29 ACST $;
@author     Jason Millward
@license    http://opensource.org/licenses/MIT
"""

import re
import subprocess

import logger


class FileBot(object):

    def __init__(self, debug, silent):
        self.log = logger.Logger("Filebot", debug, silent)

    def rename(self, dbvideo, movePath):
        """
            Renames video file upon successful database lookup

            Inputs:
                dbvideo (Obj): Video database object

            Outputs:
                Bool    Was lookup successful
        """

        if dbvideo.vidtype == "tv":
            db = "TheTVDB"
        else:
            db = "TheMovieDB"

        vidname = re.sub(r'S(\d)', '', dbvideo.vidname)
        vidname = re.sub(r'D(\d)', '', vidname)

        proc = subprocess.Popen(
            [
                'filebot',
                '-rename',
                u'%s/%s' % (dbvideo.path, dbvideo.filename),
                '--q',
                u'"%s"' % vidname,
                '-non-strict',
                '--db',
                u'%s' % db,
                '--output',
                u'%s' % movePath
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        (results, errors) = proc.communicate()

        if proc.returncode is not 0:
            self.log.error(
                "Filebot (rename) returned status code: %d" % proc.returncode)

        renamedvideo = ""
        checks = 0

        if results is not None:
            results = results.decode('utf-8')

        #if errors is not None:
        #    errors = errors.decode('utf-8')

        if len(results) is not 0:
            lines = results.split(u"\n")
            for line in lines:
                self.log.debug(line.strip())
                if "MOVE" in line:
                    renamedvideo = line.split(u"] to [", 1)[1].rstrip(']')
                    checks += 1

                if "Processed" in line:
                    checks += 1

                if "Done" in line:
                    checks += 1

        if checks >= 3 and renamedvideo:
            return [True, renamedvideo]
        else:
            return [False]

    def get_subtitles(self, dbvideo, lang):
        """
            Downloads subtitles of specified language

            Inputs:
                dbvideo (Obj): Video database object
                lang    (Str): Language of subtitles to download

            Outputs:
                Bool    Was download successful
        """
        proc = subprocess.Popen(
            [
                'filebot',
                '-get-subtitles',
                u'"%s"' % dbvideo.path,
                '--q',
                u'"%s"' % dbvideo.vidname,
                '--lang',
                lang,
                '--output',
                'srt',
                '--encoding',
                'utf8',
                '-non-strict'
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        (results, errors) = proc.communicate()

        if proc.returncode is not 0:
            self.log.error(
                "Filebot (get_subtitles) returned status code: %d" % proc.returncode)

        checks = 0

        if results is not None:
            results = results.decode('utf-8')

        #if errors is not None:
        #    errors = errors.decode('utf-8')

        if len(results) is not 0:
            lines = results.split(u"\n")
            for line in lines:
                self.log.debug(line.strip())

                if "Processed" in line:
                    checks += 1

                if "Done" in line:
                    checks += 1

        if checks >= 2:
            return True
        else:
            return False
