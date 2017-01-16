# -*- coding: utf-8 -*-
"""
MakeMKV CLI Wrapper


Released under the MIT license
Copyright (c) 2012, Jason Millward

@category   misc
@version    $Id: 1.7.0, 2016-08-22 14:53:29 ACST $;
@author     Jason Millward
@license    http://opensource.org/licenses/MIT
"""

import codecs
import datetime
import re
import subprocess
import time

import logger


class MakeMKV(object):

    def __init__(self, config):
        self.discIndex = 0
        self.vidName = ""
        self.path = ""
        self.vidType = ""
        self.minLength = int(config['makemkv']['minLength'])
        self.maxLength = int(config['makemkv']['maxLength'])
        self.cacheSize = int(config['makemkv']['cache'])
        self.ignore_region = bool(config['makemkv']['ignore_region'])
        self.log = logger.Logger("Makemkv", config['debug'], config['silent'])
        self.makemkvconPath = config['makemkv']['makemkvconPath']
        self.saveFiles = []

    def _clean_title(self):
        """
            Removes the extra bits in the title and removes whitespace

            Inputs:
                None

            Outputs:
                None
        """
        tmpname = self.vidName
        tmpname = tmpname.title().replace("Extended_Edition", "")
        tmpname = tmpname.replace("Special_Edition", "")
        tmpname = re.sub(r"Disc_(\d)(.*)", r"D\1", tmpname)
        tmpname = re.sub(r"Disc\s*(\d)(.*)", r"D\1", tmpname)
        tmpname = re.sub(r"Season_(\d)", r"S\1", tmpname)
        tmpname = re.sub(r"Season(\d)", r"S\1", tmpname)
        tmpname = re.sub(r"S(\d)_", r"S\1", tmpname)
        tmpname = tmpname.replace("_t00", "")
        tmpname = tmpname.replace("\"", "").replace("_", " ")

        # Clean up the edges and remove whitespace
        self.vidName = tmpname.strip()

    @staticmethod
    def _remove_duplicates(title_list):
        seen_titles = set()
        new_list = []
        for obj in title_list:
            if obj['title'] not in seen_titles:
                new_list.append(obj)
                seen_titles.add(obj['title'])

        return new_list

    @staticmethod
    def _read_mkv_messages(stype, sid=None, scode=None):
        """
            Returns a list of messages that match the search string
            Parses message output.

            Inputs:
                stype   (Str): Type of message
                sid     (Int): ID of message
                scode   (Int): Code of message

            Outputs:
                result  (List)
        """
        result = []

        with codecs.open('/tmp/makemkvMessages', 'r', 'utf-8') as messages:
            for line in messages:
                element = None

                if line[:len(stype)] == stype:
                    values = line[len(stype)+1:].strip().split(',')

                    if sid is not None:
                        if int(values[0]) == int(sid):
                            if scode is not None:
                                if int(values[1]) == int(scode):
                                    element = values[3]
                            else:
                                element = values[2]

                    else:
                        element = values[0]

                if element is not None:
                    element = element.strip('"')

                    if element not in result:
                        result.append(element)

        return result

    def set_title(self, vidname):
        """
            Sets local video name

            Inputs:
                vidName   (Str): Name of video

            Outputs:
                None
        """
        self.vidName = vidname

    def set_index(self, index):
        """
            Sets local disc index

            Inputs:
                index   (Int): Disc index

            Outputs:
                None
        """
        self.discIndex = int(index)

    def rip_disc(self, path, titleIndex):
        """
            Passes in all of the arguments to makemkvcon to start the ripping
                of the currently inserted DVD or BD

            Inputs:
                path    (Str):  Where the video will be saved to
                output  (Str):  Temp file to save output to

            Outputs:
                Success (Bool)
        """
        self.path = path

        fullpath = u'%s/%s' % (self.path, self.vidName)

        proc = subprocess.Popen(
            [
                '%smakemkvcon' % self.makemkvconPath,
                'mkv',
                'disc:%d' % self.discIndex,
                titleIndex,
                fullpath,
                '--cache=%d' % self.cacheSize,
                '--noscan',
                '--minlength=%d' % self.minLength
            ],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE
        )

        (results, errors) = proc.communicate()

        if results is not None:
            results = results.decode('utf-8')

        if errors is not None:
            errors = errors.decode('utf-8')

        if proc.returncode is not 0:
            self.log.error(
                "MakeMKV (rip_disc) returned status code: %d" % proc.returncode)

        if errors is not None:
            if len(errors) is not 0:
                self.log.error("MakeMKV encountered the following error: ")
                self.log.error(errors)
                return False

        checks = 0

        lines = results.split("\n")
        for line in lines:
            if "skipped" in line:
                continue

            badstrings = [
                "failed",
                "fail",
                "error"
            ]

            if any(x in line.lower() for x in badstrings):
                if self.ignore_region and "RPC protection" in line:
                    self.log.warn(line)
                elif "Failed to add angle" in line:
                    self.log.warn(line)
                else:
                    self.log.error(line)
                    return False

            if "Copy complete" in line:
                checks += 1

            if "titles saved" in line:
                checks += 1

        if checks >= 2:
            return True
        else:
            return False

    def find_disc(self):
        """
            Use makemkvcon to list all DVDs or BDs inserted
            If more then one disc is inserted, use the first result

            Inputs:
                output  (Str): Temp file to save output to

            Outputs:
                Success (Bool)
        """
        drives = []
        proc = subprocess.Popen(
            ['%smakemkvcon' % self.makemkvconPath, '-r', 'info', 'disc:-1'],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE
        )

        (results, errors) = proc.communicate()

        if results is not None:
            results = results.decode('utf-8')

        if errors is not None:
            errors = errors.decode('utf-8')

        if proc.returncode is not 0:
            self.log.error(
                "MakeMKV (find_disc) returned status code: %d" % proc.returncode)

        if errors is not None:
            if len(errors) is not 0:
                self.log.error("MakeMKV encountered the following error: ")
                self.log.error(errors)
                return []

        if "This application version is too old." in results:
            self.log.error("Your MakeMKV version is too old."
                           "Please download the latest version at http://www.makemkv.com"
                           " or enter a registration key to continue using MakeMKV.")

            return []

        # Passed the simple tests, now check for disk drives
        lines = results.split(u"\n")
        for line in lines:
            if line[:4] == "DRV:":
                if "/dev/" in line:
                    out = line.split(u',')

                    if len(out[5]) > 3:

                        drives.append(
                            {
                                "discIndex": out[0].replace("DRV:", ""),
                                "discTitle": out[5],
                                "location": out[6]
                            }
                        )

        return drives

    def get_disc_info(self):
        """
            Returns information about the selected disc

            Inputs:
                None

            Outputs:
                None
        """

        proc = subprocess.Popen(
            [
                '%smakemkvcon' % self.makemkvconPath,
                '-r',
                'info',
                'disc:%d' % self.discIndex,
                '--minlength=%d' % self.minLength,
                '--messages=/tmp/makemkvMessages'
            ],
            stderr=subprocess.PIPE
        )

        (results, errors) = proc.communicate()

        if results is not None:
            results = results.decode('utf-8')

        if errors is not None:
            errors = errors.decode('utf-8')

        if proc.returncode is not 0:
            self.log.error(
                "MakeMKV (get_disc_info) returned status code: %d" % proc.returncode)

        if errors is not None:
            if len(errors) is not 0:
                self.log.error("MakeMKV encountered the following error: ")
                self.log.error(errors)
                return False

        foundtitles = int(self._read_mkv_messages("TCOUNT")[0])

        self.log.debug("MakeMKV found {} titles".format(foundtitles))

        if foundtitles > 0:
            for titleNo in self._read_mkv_messages("TINFO"):
                disc_title = self._read_mkv_messages("CINFO", 2)[0].title()
                title = self._read_mkv_messages("TINFO", titleNo, 2)[0].title()
                filename = self._read_mkv_messages("TINFO", titleNo, 27)[0]
                chapters = self._read_mkv_messages("TINFO", titleNo, 8)

                if (len(chapters) == 0) or (int(chapters[0]) == 0):
                    self.log.debug(u"Skipping title {} ({}) because chapters found.".format(titleNo, title))
                    continue

                durTemp = self._read_mkv_messages("TINFO", titleNo, 9)[0]
                x = time.strptime(durTemp, u'%H:%M:%S')
                titleDur = datetime.timedelta(
                    hours=x.tm_hour,
                    minutes=x.tm_min,
                    seconds=x.tm_sec
                ).total_seconds()

                if self.vidType == "tv" and titleDur > self.maxLength:
                    self.log.debug(u"Excluding title {} ({}). Exceeds maxLength".format(titleNo, title))
                    continue

                rip_filename = self._read_mkv_messages("TINFO", titleNo, 27)[0]
                if self.vidType == "movie" and not re.search('t00', rip_filename):
                    self.log.debug(u"Excluding title {} ({}), only the first title is extracted.".format(titleNo, title))
                    continue

                self.log.debug(u"{}: {} ({})".format(disc_title, titleNo, title))

                self.saveFiles.append({
                    'index': titleNo,
                    'title': filename
                })

    def get_type(self):
        """
            Returns the type of video (tv/movie)

            Inputs:
                None

            Outputs:
                vidType   (Str)
        """
        titlePattern = re.compile(
            r'(DISC_(\d))|(DISC(\d))|(D(\d))|(SEASON_(\d))|(SEASON(\d))|(S(\d))'
        )

        if titlePattern.search(self.vidName):
            self.log.debug(u"Detected TV {}".format(self.vidName))
            self.vidType = "tv"
        else:
            self.log.debug(u"Detected movie {}".format(self.vidName))
            self.vidType = "movie"
        return self.vidType

    def get_title(self):
        """
            Returns the current videos title

            Inputs:
                None

            Outputs:
                vidName   (Str)
        """
        self._clean_title()
        return self.vidName

    def get_savefiles(self):
        """
            Returns the current videos title

            Inputs:
                None

            Outputs:
                vidName   (Str)
        """
        return self._remove_duplicates(self.saveFiles)
