#!/usr/bin/python
#-*- coding:utf-8 -*-
# TF1 TMC NT1 HD1 V0.9.4.3: swfPlayerHashAndSize(), log

# args & log
import argparse
from time import localtime, strftime
import logging

import subprocess, re, sys, shlex
import socket
import urllib2                  # → urlopen & exceptions
import hashlib                  # → sha256sum
import hmac
import zlib
import StringIO
import time, md5, random, urllib2, json
import bs4 as BeautifulSoup
import os                       # → os.rename
from urlparse import urlparse

# global var
scriptName='tmc_tf1.py'
scriptVersion='0.9.4.3'

# programmes externes utilisés
ffmpegEx='ffmpeg'               # ou avconv
rtmpdumpEx='rtmpdump'
curlEx='curl'

# Player swf
swfPlayerUrl='http://www.wat.tv/images/v40/PlayerWat.swf'
KEY = "Genuine Adobe Flash Player 001"

# hash et size du player swf (valide au 05/2013)
swfHashValid='0818931e9bfa764b9c33e42de6d06f924ac7fc244d0d4941019b9cdfe8706705'
swfSizeValid=352043


listeUserAgents = [ 
    'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_5; fr-fr) AppleWebKit/525.18 (KHTML, like Gecko) Version/3.1.2 Safari/525.20.1',
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.186 Safari/535.1',
    'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.27 Safari/525.',
    'Mozilla/5.0 (X11; U; Linux x86_64; en-us) AppleWebKit/528.5+ (KHTML, like Gecko, Safari/528.5+) midori',
    'Mozilla/5.0 (Windows NT 6.0) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.107 Safari/535.1',
    'Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en-us) AppleWebKit/312.1 (KHTML, like Gecko) Safari/312',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.12 Safari/535.11',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.8 (KHTML, like Gecko) Chrome/17.0.940.0 Safari/535.8' ]

WEBROOTWAT="http://www.wat.tv"
wat_url="/web/"
jsonVideosInfos=""

# random user agent
ua=random.choice(listeUserAgents)

# global logger
log=logging.getLogger(__name__)

def checkExternalProgram(prog, optArg='', expectedValue=''):
    """ Permet de vérifier la présence des programmes externes requis """
    log.debug('→checkExternalProgram(%s, %s, %s)'%(prog, optArg, expectedValue))
    args=shlex.split('%s %s' % (prog, optArg))
    try:
        process=subprocess.Popen(args,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)
        stdout, stderr = process.communicate()
        if expectedValue == '':
            return True
        else:
            if expectedValue in stdout: # à améliorer pour versions > ...
                return True
            else:
                return False
    except OSError:
        log.error('Le programme %s n\'est pas présent sur votre système' % (prog))
        return False

def get_soup(url, referer, ua):
    """ on récupère la soupe """
    req  = urllib2.Request(url)
    req.add_header('User-Agent', ua)
    req.add_header('Referer', referer)
    soup = urllib2.urlopen(req).read()
    log.debug('←get_soup(%s, %s, %s): %s' % (url, referer, ua, soup))
    return soup

def get_wat(id, HDFlag):
    """la fonction qui permet de retrouver une video sur wat"""
    def base36encode(number):
        if not isinstance(number, (int, long)):
            raise TypeError('number must be an integer')
        if number < 0:
            raise ValueError('number must be positive')
        alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        base36 = ''
        while number:
            number, i = divmod(number, 36)
            base36 = alphabet[i] + base36
        return base36 or alphabet[0]
    if HDFlag:
        wat_url = "/webhd/"
    else:
        wat_url = "/web/"
    ts = base36encode(int(time.time())-60)
    timesec = hex(int(ts, 36))[2:]
    while(len(timesec)<8):
        timesec = "0"+timesec
    token = md5.new("9b673b13fa4682ed14c3cfa5af5310274b514c4133e9b3a81e6e3aba00912564"+wat_url+str(id)+""+timesec).hexdigest()
    id_url1 = WEBROOTWAT+"/get"+wat_url+str(id)+"?token="+token+"/"+str(timesec)+"&country=FR&getURL=1"
    log.debug('←get_wat(%s, %s):%s' %(id, HDFlag, id_url1))
    return id_url1

def swfPlayerHashAndSize(swfPlayerUrl):
    """
    Calcule et renvoie le tuple  (hash, taille) du player swf
    ← (swfHash, swfSize)
    """
    global KEY
    try:
        swfPlayer= urllib2.urlopen(swfPlayerUrl).read()
    except (ValueError, urllib2.URLError):
        log.error('→swfPlayerHashAndSize(%s): Url invalide!' % (swfPlayerUrl))
        raise
    except urllib2.HTTPError:
        log.error('→swfPlayerHashAndSize(%s): Pb http!' % (swfPlayerUrl))
        raise

    swfPlayerHash=hashlib.sha256(swfPlayer).hexdigest()
    if type(swfPlayer) is str:
        swfData=StringIO.StringIO(swfPlayer)
    swfData.seek(0, 0)
    magic=swfData.read(3)
    if magic != "CWS":
        log.error("Pas de CWS...")
        return False
    else:
        unzPlayer="FWS" + swfData.read(5) + zlib.decompress(swfData.read())
        unzPlayerSize=len(unzPlayer)
        unzPlayerHash = hmac.new(KEY, unzPlayer, hashlib.sha256).hexdigest()
    log.debug('←computeSwfPlayerHash(%s):(%s, %s)' %(
            swfPlayerUrl, unzPlayerSize, unzPlayerHash))
    return (unzPlayerHash, unzPlayerSize)

def downloadWatVideo(videoUrl):
    """ recuperation de vidéos sur TF1/TMC/NT1/HD1 (donc WAT)"""
    # timeout en secondes
    log.debug('→downloadWatVideo(%s)' %(videoUrl))
    socket.setdefaulttimeout(90)
    debut_id = ''
    html = urllib2.urlopen(videoUrl).read()
    log.debug('html=%s' %(html))
    nom = videoUrl.split('/')[-1:][0]
    no = nom.split('.')[-2:][0]
    soup = BeautifulSoup.BeautifulSoup(html)
    log.debug('soup=%s' %(soup))
    site = urlparse(videoUrl).netloc
    if 'tmc.tv' in site or 'tf1.fr' in site:
        debut_id = str(soup.find('div', attrs={'class' : 'unique' }))
    if 'nt1.tv' in site or 'hd1.tv' in site:
        debut_id = str(soup.find('section', attrs={'class' : 'player-unique' }))
    id = [x.strip() for x in re.findall("mediaId :([^,]*)", debut_id)][0]
    referer = [x.strip() for x in re.findall('url : "(.*?)"', debut_id)][0]
    jsonVideoInfos = get_soup(WEBROOTWAT+'/interface/contentv3/'+id, referer, ua)
    videoInfos = json.loads(jsonVideoInfos)
    log.debug('videoInfos=%s' % (videoInfos))
    try:
        HD = videoInfos["media"]["files"][0]["hasHD"]
    except:
        HD = False

    NumberOfParts = len(videoInfos["media"]["files"])
    ListOfIds = []
    for iPart in range(NumberOfParts):
        ListOfIds.append(videoInfos["media"]["files"][iPart]["id"])
    log.debug('NumberOfParts=%s' % (NumberOfParts))
    for PartId in ListOfIds:
        id_url1 = get_wat(PartId, HD)
        req  = urllib2.Request(id_url1)
        req.add_header('User-Agent', ua)
        req.add_header('Referer', referer)
        data = urllib2.urlopen(req).read()
        log.debug('data=%s' % (data))
        if data[0:4] == 'http':
            if not checkExternalProgram(curlEx):
                log.warning('Ce script requiert %s' % (curlEx))
            else:
                arguments = '%s "%s" -C - -L -g -A "%s" -o "%s.mp4"' % (
                    curlEx, data, ua, no + "-" + str(PartId))
                log.info(arguments)
                process = subprocess.Popen(arguments,
                                           stdout=subprocess.PIPE,
                                           shell=True).communicate()[0]
            # no retry loop?
        if data[0:4] == 'rtmp':
            # vérification de la présence de rtmpdump v2.4 ou v2.5
            if not (checkExternalProgram(rtmpdumpEx, '-help', 'v2.4') or 
                    checkExternalProgram(rtmpdumpEx, '-help', 'v2.5')): # pas top
                log.warning('Ce script requiert %s v2.4 ou v2.5' % (rtmpdumpEx))
            else:
                try:
                    (swfHash, swfSize)=swfPlayerHashAndSize(swfPlayerUrl)
                except:
                    log.warning('Impossible de calculer dynamiquement le (hash, size) du player swf! Utilisation des valeurs par défaut.')
                    swfHash=swfHashValid
                    swfSize=swfSizeValid

                if '.hd' in data:
                    data0 = re.search('rtmpte://(.*)hd', data).group(0)
                if '.h264' in data:
                    data0 = re.search('rtmpte://(.*)h264', data).group(0)
                log.debug('data0=%s'%(data0))
                data0 = data0.replace('rtmpte','rtmpe')
                fName=str(no) + '-' + str(PartId) # nom du fichier sans extension
                fileName=fName+'.mp4'             # nom du fichier avec extension
                rtmpCmd = '%s -e -r "%s" -c 443 -m 10 -w %s -x %i -o "%s"' % (
                    rtmpdumpEx, data0, swfHash, swfSize, fileName)
                log.info(rtmpCmd)
                arguments = shlex.split( rtmpCmd )
                cpt = 0 
                while True:
                    p = subprocess.Popen(arguments,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
                    stdout, stderr = p.communicate()
                    if p.returncode != 0:
                        log.error('Le sous-process s\'est terminé avec le code d\'erreur ' + str(p.returncode) + ')')
                        if cpt > 5:
                            break
                        cpt += 1
                        log.error('Essai de reprise...')
                        time.sleep(3) 
                    else:
                        # ffmpeg est-il disponible?
                        if not checkExternalProgram(ffmpegEx):
                            log.info("L'installation de ffmpeg sur votre système permettrait de corriger automatiquement le conteneur de la vidéo (flash→mp4).")
                        else:
                            log.debug('conversion ffmpeg fileName → tmpFileName (pour corriger le conteneur)')
                            tmpFileName=fName+'.tmp.mp4'
                            ffmpegCmd='%s -i "%s" -acodec copy -vcodec copy "%s"' % (
                                ffmpegEx, fileName, tmpFileName)
                            arguments=shlex.split(ffmpegCmd)
                            p=subprocess.Popen(arguments,
                                               stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE)
                            stdout, stderr = p.communicate()
                            if p.returncode != 0:
                                log.error('La conversion ffmpeg s\'est terminée avec le code d\'erreur %i.\nLe fichier %s est néanmois disponible' % (
                                        p.returncode, fileName))
                            else:
                                log.debug('remplacement tmpFileName → fileName')
                                os.rename(tmpFileName, fileName)
                        break
    log.debug('Fini!')

def main():
    """
    Analyse les arguments et lance le téléchargement
    """
    parser=argparse.ArgumentParser(prog=scriptName,
                                   description='Récuperation de vidéos sur TF1/TMC/NT1/HD1 (donc WAT).',
                                   version='%s v%s' % (scriptName, scriptVersion))
    verbOrLog=parser.add_mutually_exclusive_group()
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
    parser.add_argument('url',
                        help='url de la page de la video',
                        metavar='URL',
                        nargs='?')
    args=parser.parse_args()
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
        log.info('url: %s' % (args.url))
        downloadWatVideo(args.url)

if __name__ == "__main__":
    main()
