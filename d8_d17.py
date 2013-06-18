#!/usr/bin/env python
# -*- coding:utf-8 -*-
# D8 version 0.2 par k3c: rtmpdump --resume, break→sys.exit(), typo
from urllib2 import urlopen
from lxml import objectify
import bs4 as BeautifulSoup
import sys, subprocess, re
a = urlopen(sys.argv[1]).read()
s = BeautifulSoup.BeautifulSoup(a)
url = ''
def get_HD(d8_cplus):
    zz = urlopen('http://service.canal-plus.com/video/rest/getVideosLiees/'+d8_cplus+'/'+id).read()
    root = objectify.fromstring(zz)
    for element in root.iter():
        if element.tag == 'HD':
            url = element.text
            arguments = 'rtmpdump -r "%s" -o "%s.mp4" --resume' % (url, titre)
            print arguments
            process = subprocess.Popen(arguments, stdout=subprocess.PIPE, shell=True).communicate()[0]
            sys.exit()
         
m = re.search('\d{6}$',sys.argv[1])
if m is None:
    try:
        id = s.findAll('div',attrs={"class":u"block-common block-player-programme"})[0]('canal:player')[0]['videoid']
    except:
		print 'imposiible de trouver l\'id de la  video'
		sys.exit()
else:
	id = m.group(0)
titre = s.findAll('meta',attrs={"property":u"og:title"})[0]['content'].replace(' ','_')
titre = titre.replace('/','_')
for x in ['d8','cplus']:
    get_HD(x)
