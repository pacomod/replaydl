#!/usr/bin/env python
# -*- coding:utf-8 -*-
# D8 version 0.4 par k3c et Jul1en094: titre de la vidéo dans le nom de fichier
from urllib2 import urlopen
from lxml import objectify
import bs4 as BeautifulSoup
import sys, subprocess, re
import unicodedata
import string

validFilenameChars = "-_.() %s%s" % (string.ascii_letters, string.digits)

def removeDisallowedFilenameChars(filename):
    "Remove invalid filename characters" 
    cleanedFilename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore')
    cleanedFilename = cleanedFilename.replace(' ', '_')
    return ''.join(c for c in cleanedFilename if c in validFilenameChars)

def getHD(d8_cplus, titre, vid):
    "Get video url and download"
    titre = removeDisallowedFilenameChars(titre)
    zz = urlopen('http://service.canal-plus.com/video/rest/getVideosLiees/'+d8_cplus+'/' + vid).read()
    root = objectify.fromstring(zz)
    isGoodId = False
    for element in root.iter():
        if element.tag == 'ID': 
            if element.text == str(vid) :
                isGoodId = True
        if element.tag == 'HD' and isGoodId:
            url = element.text
            arguments = 'rtmpdump -r "%s" -o "%s_%s.mp4" --resume' % (url, titre, d8_cplus)
            print arguments
            subprocess.Popen(arguments, stdout=subprocess.PIPE, shell=True).communicate()[0]
            isGoodId = False
            sys.exit()

def main():
    "main function"
    a = urlopen(sys.argv[1]).read()
    s = BeautifulSoup.BeautifulSoup(a)
    m = re.search('pid\d{6}', sys.argv[1])
    if m is None:
        try:
            vid = s.findAll('div', attrs={"class":u"block-common block-player-programme"})[0]('canal:player')[0]['videoid']
        except:
            print 'impossible de trouver l\'id de la  video'
            sys.exit()
    else:
        vid = m.group(0)
    titre = s.findAll('meta', attrs={"property":u"og:title"})[0]['content']
    for x in ['d8','cplus']:
        getHD(x, titre, vid)

if __name__ == '__main__':
    main()
