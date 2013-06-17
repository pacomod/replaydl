# -*- coding: utf-8 -*-
# os and lib modules
# cherie25 et nrj  v 0.3 k3c
import subprocess
import sys 
import urllib2
import shlex
from urlparse import urlparse
# pyamf
from pyamf.remoting.client import RemotingService
# parseDOM
import bs4 as BeautifulSoup
import unicodedata
import string

__addonID__      = "plugin.video.NRJ12Replay"
__author__       = "k3c,JUL1EN094 ,vilain_mamuth"
__date__         = "05-04-2013"
__version__      = "0.3"
__credits__      = "Merci aux auteurs des autres addons replay du dépôt Passion-XBMC et de la communauté open-source"  

# Web variable
#WEBROOT = "http://www.nrj12.fr"
#WEBSITE = WEBROOT + "/replay-4203/collectionvideo/"        
INFOSITE = "http://prod-kernnrj12v5.integra.fr/videoinfo"        
validFilenameChars = "-_.() %s%s" % (string.ascii_letters, string.digits)

def removeDisallowedFilenameChars(filename):
    "Remove invalid filename characters" 
    filename = filename.decode('ASCII', 'ignore')
    cleanedFilename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore')
    cleanedFilename = cleanedFilename.replace(' ', '_')
    return ''.join(c for c in cleanedFilename if c in validFilenameChars)              

def get_soup(url):
    "analyse de la page par BeautifulSoup"
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 5.1; rv:15.0) Gecko/20100101 Firefox/15.0.1')           
    sou = urllib2.urlopen(req).read()
    soup = BeautifulSoup.BeautifulSoup(sou)
    print "le findAll "
    zz = urlparse(sys.argv[1])
    mediaiId = ''
    try: 
        if 'cherie25' in zz.netloc:
            mediaId = soup.findAll('div', attrs={"class":u"page_video"})[0]('img')[0]['id'] 
        elif 'nrj' in zz.netloc:
            mediaId = soup.findAll('div', attrs={"class":u"img-une"})[0]('img')[0]['id']
        else:
            print "cette video ne vient ni de nrj12 ni de cherie25"
            sys.exit()
# on enlève mediaId_
        mediaId = mediaId[8:]
#    print mediaId
    except:
        print 'impossible de trouver l\'id de la  video'
        sys.exit()
    return mediaId

def get_url(url, mediaId):
    "appel à pyamf pour l'adresse de la vidéo"
    client = RemotingService(url)
    vi = client.getService('Nrj_VideoInfos')
    mi = vi.mediaInfo(mediaId)
    url_episode = mi["url"]
    titre = mi["title"].replace(' ','_') 
    return url_episode, titre 
                                       
#######################################################################################################################    
# BEGIN !
#######################################################################################################################
def main():
    "main function"
    mediaId = get_soup(sys.argv[1])
    url_episode, titre = get_url(INFOSITE, mediaId)
    cmds = 'msdl -c --no-proxy %s -s 5 -o \"%s_%s.mp4\"' % (url_episode, titre, mediaId)
    print cmds
    arguments = shlex.split( cmds )
    print arguments
    subprocess.Popen( arguments, stdout = subprocess.PIPE).communicate()[0]
#    stdout, stderr = p.communicate()
#    if p.returncode != 0:
#        print "Erreur : le sous-process s\'est terminé avec (le code d\'erreur est " + str(p.returncode) + ")"

if __name__ == '__main__':
    main()
