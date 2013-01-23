"""
MakeMKV CLI Wrapper

This class acts as a python wrapper to the MakeMKV CLI.


Released under the MIT license
Copyright (c) 2012, Jason Millward

@category   misc
@version    $Id: 1.2, 2013-01-20 11:08:00 CST $;
@author     Jason Millward <jason@jcode.me>
@license    http://opensource.org/licenses/MIT
"""

#
#   IMPORTS
#

import commands
import imdb
import os
import re

#
#   CODE
#


class makeMKV(object):

    """ Function:   __init__
            Removes the log file and the input movie because these files are
                no longer needed by this script

        Inputs:
            log         (Str): File path of the log to remove
            oldMovie    (Str): File path of the movie to remove

        Outputs:
            None
    """
    def __init__(self):
        self.movieName = ""
        self.imdbScaper = imdb.IMDb()

    """ Function:   _queueMovie
            Removes the log file and the input movie because these files are
                no longer needed by this script

        Inputs:
            log         (Str): File path of the log to remove
            oldMovie    (Str): File path of the movie to remove

        Outputs:
            None
    """
    def _queueMovie(self):
        home = os.path.expanduser("~")
        if os.path.exists('%s/.makemkvautoripper' % home) == False:
            os.makedirs('%s/.makemkvautoripper' % home)

        os.chdir('%s/%s' % (self.path, self.movieName))
        for files in os.listdir("."):
            if files.endswith(".mkv"):
                movie = files
                break

        with open("%s/.makemkvautoripper/queue" % home, "a+") as myfile:
            myfile.write("%s|%s|%s|%s.mkv\n"
                %
                (self.path, self.movieName, movie, self.movieName))

    """ Function:   _cleanTitle
            Removes the log file and the input movie because these files are
                no longer needed by this script

        Inputs:
            log         (Str): File path of the log to remove
            oldMovie    (Str): File path of the movie to remove

        Outputs:
            None
    """
    def _cleanTitle(self):
        tmpName = self.movieName
        # A little fix for extended editions (eg; Die Hard 4)
        tmpName = tmpName.title().replace("Extended_Edition", "")

        # Remove Special Edition
        tmpName = tmpName.replace("Special_Edition", "")

        # Remove Disc X from the title
        tmpName = re.sub(r"Disc_(\d)", "", tmpName)

        # Clean up the disc title so IMDb can identify it easier
        tmpName = tmpName.replace("\"", "").replace("_", " ")

        # Clean up the edges and remove whitespace
        self.movieName = tmpName.strip()

    """ Function:   ripDisc
            Removes the log file and the input movie because these files are
                no longer needed by this script

        Inputs:
            log         (Str): File path of the log to remove
            oldMovie    (Str): File path of the movie to remove

        Outputs:
            None
    """
    def ripDisc(self, path, length, cache, queue):
        self.path = path
        # Start the making of the mkv
        commands.getstatusoutput(
            'makemkvcon mkv disc:%s 0 "%s/%s" --cache=%d --noscan --minlength=%d'
            %
            (self.discIndex, self.path, self.movieName, cache, length))

        # Add some checking here
        # Seriously, check to see if makemkv worked like it should :(
        if queue:
            self._queueMovie()
        return True

    """ Function:   findDisc
            Removes the log file and the input movie because these files are
                no longer needed by this script

        Inputs:
            log         (Str): File path of the log to remove
            oldMovie    (Str): File path of the movie to remove

        Outputs:
            None
    """
    def findDisc(self, output):
        # Execute the info gathering
        # Save output into /tmp/ for interpreting 3 or 4 lines later
        commands.getstatusoutput('makemkvcon -r info > %s' % output)

        # Open the info file from /tmp/
        tempFile = open(output, 'r')
        for line in tempFile.readlines():
            if line[:4] == "DRV:":
                if "/dev/" in line:
                    drive = line.split(',')
                    self.discIndex = drive[0].replace("DRV:", "")
                    self.movieName = drive[5]
                    break

        if len(self.discIndex) == 0:
            return False
        else:
            return True

    """ Function:   getTitle
            Removes the log file and the input movie because these files are
                no longer needed by this script

        Inputs:
            log         (Str): File path of the log to remove
            oldMovie    (Str): File path of the movie to remove

        Outputs:
            None
    """
    def getTitle(self):
        self._cleanTitle()

        result = self.imdbScaper.search_movie(self.movieName, results=1)

        if len(result) > 0:
            self.movieName = result[0]

        return self.movieName