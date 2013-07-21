#!/usr/bin/python
#-*- coding:utf-8 -*-
# Gulli 0.1 par k3c

# args & log
import argparse
from time import localtime, strftime
import logging

import subprocess, re, sys, shlex
import socket
import urllib2                  # → urlopen & exceptions
from urllib2 import URLError
from urllib2 import urlopen
import time, random
import bs4 as BeautifulSoup
from urlparse import urlparse
import string
import unicodedata

# global var
scriptName = 'gulli.py'
scriptVersion = '0.1'
validFilenameChars = "-_.() %s%s" % (string.ascii_letters, string.digits)


# programmes externes utilisés
ffmpegEx = 'ffmpeg'               # ou avconv
rtmpdumpEx = 'rtmpdump'
curlEx = 'curl'

def removeDisallowedFilenameChars(filename):
    "Remove invalid filename characters" 
    filename = filename.decode('ASCII', 'ignore')
    cleanedFilename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore')
    cleanedFilename = cleanedFilename.replace(' ', '_')
    return ''.join(c for c in cleanedFilename if c in validFilenameChars)

listeUserAgents = [ 
    'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_5; fr-fr) AppleWebKit/525.18 (KHTML, like Gecko) Version/3.1.2 Safari/525.20.1',
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.186 Safari/535.1',
    'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.27 Safari/525.',
    'Mozilla/5.0 (X11; U; Linux x86_64; en-us) AppleWebKit/528.5+ (KHTML, like Gecko, Safari/528.5+) midori',
    'Mozilla/5.0 (Windows NT 6.0) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.107 Safari/535.1',
    'Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en-us) AppleWebKit/312.1 (KHTML, like Gecko) Safari/312',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.12 Safari/535.11',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.8 (KHTML, like Gecko) Chrome/17.0.940.0 Safari/535.8' ]

# random user agent
ua = random.choice(listeUserAgents)

# global logger
log = logging.getLogger(__name__)

defaultSwfPlayerUrl = "http://cdn1-gulli.ladmedia.fr/extension/lafrontoffice/design/standard/flash/jwplayer/release/player.swf" 

def checkExternalProgram(prog, optArg='', expectedValue=''):
    """ Permet de vérifier la présence des programmes externes requis """
    log.debug('→checkExternalProgram(%s, %s, %s)'%(prog, optArg, expectedValue))
    args = shlex.split('%s %s' % (prog, optArg))
    try:
        process = subprocess.Popen(args,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)
        stdout, stderr = process.communicate()
        if expectedValue == '':
            return True
        elif expectedValue in stdout: # à améliorer pour versions > ...
            return True
        else:
            return False
    except OSError:
        log.error('Le programme %s n\'est pas présent sur votre système' % (prog))
        return False

def get_soup(url, ua):
    """ on récupère la soupe """
    req  = urllib2.Request(url)
    req.add_header('User-Agent', ua)
    soup = urllib2.urlopen(req).read()
    # log.debug('←get_soup(%s, %s, %s): %s' % (url, ua, soup))
    return soup


def rtmpDownload(rtmpUrl,
                 swfPlayerUrl,
                 swfForceRefresh):
    """ Appel de rtmpdump avec traitement des options et reprise (récursif)
    """
    global titre
    log.debug('→rtmpDownload(%s, %s, %s)' % (
            rtmpUrl, swfPlayerUrl, swfForceRefresh))
#exemple de commande
#rtmpdump -r "rtmp://stream2.lgdf.yacast.net/gulli_replay/" -a "gulli_replay/" -f "LNX 11,2,202,291" 
#-W "http://cdn1-gulli.ladmedia.fr/extension/lafrontoffice/design/standard/flash/jwplayer/release/player.swf" 
#-p "http://replay.gulli.fr/replay/video/series/les_parent/VOD360869" -y "mp4:29248VOD317.mp4" -o le_nom_qu_on_veut
    titre = re.sub('__+', '_', titre)
    rtmpCmd = '%s -r %s -a %s -f %s -W %s -p %s -y %s -o %s --port 443 --timeout 10' % (rtmpdumpEx, "rtmp://stream2.lgdf.yacast.net/gulli_replay/", "gulli_replay/", "LNX 11,2,202,291", "http://cdn1-gulli.ladmedia.fr/extension/lafrontoffice/design/standard/flash/jwplayer/release/player.swf" , sys.argv[1], lemp4, titre )    # initialisation de la commande
    log.info(rtmpCmd)
    rtmpCall = shlex.split(rtmpCmd)

    rtmpProc = subprocess.Popen(rtmpCall,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
    (stdout, stderr) = rtmpProc.communicate()


    if rtmpProc.returncode == 1:   # sortie en erreur →
        if swfComputeHashSize:     # on ré-essaye avec le calcul par rtmpdump
            return rtmpDownload(rtmpUrl, swfPlayerUrl, True,
                                False)
        else:               # rtmpdump computation & refresh KO →
            log.warning ('Veuillez ré-essayer plus tard (pb réseau ou algo?)')
    elif rtmpProc.returncode == 2:   # téléchargement incomplet →
        log.info('Téléchargement incomplet: nouvel essai dans 3s...')
        time.sleep(3)                # petite temporisation
        
    else:
        return rtmpProc.returncode # = 0

def downloadVideo(videoUrl, swfPlayerUrl, swfForceRefresh):
    """ recuperation de vidéos sur Gulli"""
    log.debug('→downloadVideo(%s, %s, %s)' % (videoUrl, swfPlayerUrl, swfForceRefresh))
    # timeout en secondes
    socket.setdefaulttimeout(90)
    get_id(sys.argv[1])
    global lemp4
    url_smil = "http://replay.gulli.fr/replay/smil/" + str(ident)
    try:
        le_smil = urllib2.urlopen(url_smil).read()
        # contient un truc du genre
        # {"smil":"http:\/\/cdn1-gulli.ladmedia.fr\/var\/storage\/imports\/replay\/smil\/VOD360869.smil","filename":"29248VOD317.mp4"}
        m = re.search('[0-9]+VOD[0-9\.]?.*mp4', le_smil)
        lemp4 = 'mp4:' + m.group(0)
        # par exemple m.group(0) va valoir dans ce cas 29248VOD317.mp4
    except URLError, e :
        print e.code                
        log.error( URLError, e, url_smil)
        return
    rtmpDownload("rtmp://stream2.lgdf.yacast.net/gulli_replay/",
                 swfPlayerUrl,
                 swfForceRefresh)
        

def get_id(url):
    """ récupère l'identifiant de la vidéo"""
    # exemple d'url
    # http://replay.gulli.fr/replay/video/series/la_methode_becky/VOD361555
    global ident
    global titre
    html = urlopen(sys.argv[1]).read()
    soup = BeautifulSoup.BeautifulSoup(html, "html5lib")
    titre = soup.title.contents[0].encode('ascii', errors='replace')
    titre = removeDisallowedFilenameChars(titre) + ".flv"
    centre = urlparse(url)
    lepath = centre.path
    # dans ce cas lepath vaut '/replay/video/series/la_methode_becky/VOD361555'
    ident = lepath.split('/')[-1:]
    # par exemple ['VOD361555']
    ident = ''.join(ident)        
    # renvoie 'VOD361555'
    return ident

def main():
    """
    Analyse les arguments et lance le téléchargement
    """

    parser = argparse.ArgumentParser(prog=scriptName,
                                   description='Récuperation de vidéos sur' +
                                   ' Gulli.',
                                   version='%s v%s' % (scriptName,
                                                       scriptVersion))
    verbOrLog = parser.add_mutually_exclusive_group()
    verbOrLog.add_argument('-V', '--verbose',
                           help="affiche des messages",
                           dest='verbose',
                           action='store_true',
                           default=False)
    verbOrLog.add_argument('-l', '--log',
                           help="logue les messages",
                           dest='log',
                           action='store_const',
                           const='%s-%s.log' % (scriptName,
                                                strftime("%Y%m%d%H%M%S",
                                                         localtime())),
                           metavar='FILE')
    parser.add_argument('-p', '--swf-player-url',
                        help='url du player swf à utiliser (défaut= %s)' % (
            defaultSwfPlayerUrl),
                        dest='swfPlayerUrl',
                        default=defaultSwfPlayerUrl,
                        action='store',
                        metavar='URL')
    parser.add_argument('-f', '--swf-force-refresh',
                        help='force la vérification du hash/size du player swf' +
                        ' (met éventuellement à jour ~/.swfinfo)',
                        dest='swfForceRefresh',
                        default=False,
                        action='store_true')
    parser.add_argument('url',
                        help='url de la page de la video',
                        metavar='URL',
                        nargs='+')
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(format='%(levelname)s:\t%(asctime)s: %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.INFO)
        log.info('verbose mode')
    else:
        if args.log:
            logging.basicConfig(filename=args.log,
                                format='%(levelname)s:\t%(asctime)s: %(message)s',
                                datefmt='%H:%M:%S',
                                level=logging.DEBUG)
            log.info(args.log)
        else:
            logging.basicConfig(format='%(message)s',
                                datefmt='%H:%M:%S',
                                level=logging.WARNING)
    if args.url:
        for url in args.url:
            log.info('url: %s' % (args.url))
            downloadVideo(url,
                             args.swfPlayerUrl,
                             args.swfForceRefresh)

if __name__ == "__main__":
    main()
