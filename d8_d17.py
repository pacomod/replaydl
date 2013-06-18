#!/usr/bin/env python
# -*- coding:utf-8 -*-
# D8 version 0.3 par k3c et Julien974: check videoId, id→vid, typos
from urllib2 import urlopen
from lxml import objectify
import bs4 as BeautifulSoup
import sys, subprocess, re
a = urlopen(sys.argv[1]).read()
s = BeautifulSoup.BeautifulSoup(a)
url = ''
def get_HD(d8_cplus,vid):
    zz = urlopen('http://service.canal-plus.com/video/rest/getVideosLiees/'+d8_cplus+'/'+vid).read()
    root = objectify.fromstring(zz)
    isGoodId = False
    for element in root.iter():
        if element.tag == 'ID': 
            if element.text == str(vid) :
                isGoodId = True
        if element.tag == 'HD' and isGoodId :
            url = element.text
            arguments = 'rtmpdump -r "%s" -o "%s.mp4" --resume' % (url, titre)
            print arguments
            process = subprocess.Popen(arguments, stdout=subprocess.PIPE, shell=True).communicate()[0]
            isGoodId = False
            sys.exit()
         
m = re.search('pid\d{6}',sys.argv[1])
if m is None:
    try:
        vid = s.findAll('div',attrs={"class":u"block-common block-player-programme"})[0]('canal:player')[0]['videoid']
    except:
		print 'impossible de trouver l\'id de la  video'
		sys.exit()
else:
	vid = m.group(0)
titre = s.findAll('meta',attrs={"property":u"og:title"})[0]['content'].replace(' ','_')
titre = titre.replace('/','_').replace('!','')
for x in ['d8','cplus']:
    get_HD(x,vid)
