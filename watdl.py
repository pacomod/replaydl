#!/usr/bin/python
#-*- coding:utf-8 -*-
# TF1 TMC NT1 HD1
# V0.9.4.9: modification de la base de calcul du token
# V0.9.4.8: modification du referer, redirection de l'url initiale, modification de get_wat

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
import time, md5, random, json
import bs4 as BeautifulSoup
import os                       # → os.rename
from urlparse import urlparse, parse_qs

# global var
scriptName='watdl.py'
scriptVersion='0.9.4.9'

# programmes externes utilisés
ffmpegEx='ffmpeg'               # ou avconv
rtmpdumpEx='rtmpdump'
curlEx='curl'

# Player swf
defaultSwfPlayerUrl='http://www.wat.tv/images/v40/PlayerWat.swf'
#defaultSwfPlayerUrl='http://www.wat.tv/images/v60/PlayerWat.swf'
KEY = "Genuine Adobe Flash Player 001"

urlOpenTimeout = 30

listeUserAgents = [
    'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:22.0) Gecko/20100101 Firefox/22.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:24.0) Gecko/20100101 Firefox/24.0',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20130406 Firefox/23.0',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:23.0) Gecko/20131011 Firefox/23.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:21.0) Gecko/20130331 Firefox/21.0',
    'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.27 Safari/525.',
    'Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en-us) AppleWebKit/312.1 (KHTML, like Gecko) Safari/312',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.8 (KHTML, like Gecko) Chrome/17.0.940.0 Safari/535.8',
    'Mozilla/5.0 (Windows NT 6.0) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.107 Safari/535.1',
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.186 Safari/535.1',
    'Mozilla/5.0 (X11; U; Linux x86_64; en-us) AppleWebKit/528.5+ (KHTML, like Gecko, Safari/528.5+) midori',
    'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_5; fr-fr) AppleWebKit/525.18 (KHTML, like Gecko) Version/3.1.2 Safari/525.20.1',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.12 Safari/535.11' ]

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
    soup = urllib2.urlopen(req, None, urlOpenTimeout).read()
    log.debug('←get_soup(%s, %s, %s): %s' % (url, referer, ua, soup))
    return soup

def get_wat(id, HDFlag, referUrl, sitepage):
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
    # pouet-pouet
    # ts = base36encode(int(time.time())-60)
    referArgs=parse_qs(urlparse(referUrl).query)
    ts=referArgs['ts'][0]
    # pouet-pouet
    timesec = hex(int(ts, 36))[2:]
    while(len(timesec)<8):
        timesec = "0"+timesec
    token = md5.new(
        "9b673b13fa4682ed14c3cfa5af5310274b514c4133e9b3a81e6e3aba009l2564" +
        wat_url + str(id) + timesec).hexdigest()
    # token = md5.new(
    #     "9b673b13fa4682ed14c3cfa5af5310274b514c4133e9b3a81e6e3aba00912564" +
    #     wat_url + str(id) + "" + timesec).hexdigest()
    # id_url1 = (WEBROOTWAT + "/get" + wat_url + str(id) + "?token=" + token +
    # "/" + str(timesec) + "&country=FR&getURL=1")
    # tagada
    # referArgs=parse_qs(urlparse(referUrl).query)
    id_url1 = (WEBROOTWAT + "/get" + wat_url + str(id) +
               "?token=" + token +
               "/" + str(timesec) +
               '&domain=' + referArgs['referer'][0] +
               '&domain2=null' + # referer2?
               '&refererURL=' + urllib2.quote(referArgs['refererURL'][0], safe='') +
               '&revision=' + referArgs['revision'][0] +
               '&synd=0' +      # ?
               '&helios=1' +    # ?
               '&context=' + referArgs['context'][0] +
               '&pub=5' +       # ?
               '&country=FR' +
               '&sitepage=' + sitepage + # referArgs['oasTag'][0] +
               '&nolog=seen' +  # ?
               '&lieu=' + referArgs['referer'][0].split('.')[1] +
               '&playerContext=CONTEXT_' + referArgs['referer'][0].split('.')[1].upper() +
               '&getURL=1' +    # ?
               '&version=LNX%2011,2,202,291' # → automatisation?
               )
    #tagada
    log.debug('←get_wat(%s, %s, %s, %s): %s' % (
            id, HDFlag, referUrl, sitepage, id_url1))
    return id_url1

def swfPlayerHashAndSize(swfPlayerUrl):
    """
    Calcule et renvoie le tuple (hash, taille) du player swf
    ← (swfHash, swfSize)
    """
    global KEY
    try:
        swfPlayer= urllib2.urlopen(swfPlayerUrl, None, urlOpenTimeout).read()
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
        raise ValueError('NoCWS')
    else:
        unzPlayer="FWS" + swfData.read(5) + zlib.decompress(swfData.read())
        unzPlayerSize=len(unzPlayer)
        unzPlayerHash = hmac.new(KEY, unzPlayer, hashlib.sha256).hexdigest()
    log.debug('←computeSwfPlayerHash(%s):(%s, %s)' %(
            swfPlayerUrl, unzPlayerHash, unzPlayerSize))
    return (unzPlayerHash, unzPlayerSize)

def rtmpDownload(rtmpUrl,
                 swfPlayerUrl,
                 swfForceRefresh,
                 swfComputeHashSize,
                 fileName,
                 swfHash=None,
                 swfSize=None):
    """ Appel de rtmpdump avec traitement des options et reprise (récursif)
    """
    log.debug('→rtmpDownload(%s, %s, %s, %s, %s, %s, %s)' % (
            rtmpUrl, swfPlayerUrl, swfForceRefresh, swfComputeHashSize,
            fileName, swfHash, swfSize))
    rtmpCmd = '%s --resume --rtmp "%s" --port 1935 --timeout 10' % (
        rtmpdumpEx, rtmpUrl)    # initialisation de la commande

    if swfComputeHashSize:
        if not swfHash and not swfSize: # pour ne pas recalculer en récursion
            try:
                (swfHash, swfSize)=swfPlayerHashAndSize(swfPlayerUrl)
            except:
                log.warning('Impossible de calculer le hash/size du player swf!')
                log.info('calcul du hash/size par %s' % (rtmpdumpEx))
                return rtmpDownload(rtmpUrl, swfPlayerUrl, swfForceRefresh,
                                    False, fileName)
            if swfForceRefresh:
                log.warning('pas encore codé!')
                # et je ne sais pas si ça le sera... ;)
            rtmpCmd += ' --swfhash %s --swfsize %i' % (swfHash, swfSize)
    else:
        if swfForceRefresh:
            rtmpCmd += ' --swfVfy %s --swfAge 0' % (swfPlayerUrl)
        else:
            rtmpCmd += ' --swfVfy %s' % (swfPlayerUrl)
    rtmpCmd += ' -o "%s"' % (fileName)
    log.info(rtmpCmd)
    rtmpCall = shlex.split(rtmpCmd)
    rtmpProc = subprocess.Popen(rtmpCall,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
    (stdout, stderr) = rtmpProc.communicate()
    if rtmpProc.returncode == 1:   # sortie en erreur →
        log.debug('rtmpdump output: %s' % (stdout))
        if 'corrupt file!' in stdout: # ERROR: Last tag...corrupt file!
            log.warning('Le fichier %s est corrompu!\n\t le téléchargement doit reprendre du début...' % (fileName))
            os.remove(fileName)
            return rtmpDownload(rtmpUrl, swfPlayerUrl, swfForceRefresh,
                                swfComputeHashSize, fileName, swfHash, swfSize)
        else:                      # ERROR: RTMP_ReadPacket...?
            if swfComputeHashSize: # on ré-essaye avec le calcul par rtmpdump
                return rtmpDownload(rtmpUrl, swfPlayerUrl, swfForceRefresh,
                                    False, fileName)
            elif not swfForceRefresh: # on ré-essaye en forçant le recalcul
                return rtmpDownload(rtmpUrl, swfPlayerUrl, True,
                                    False, fileName)
            else:               # rtmpdump computation & refresh KO →
                log.warning ('Veuillez ré-essayer plus tard...')
    elif rtmpProc.returncode == 2:   # téléchargement incomplet →
        log.info('Téléchargement incomplet: nouvel essai dans 3s...')
        time.sleep(3)                # petite temporisation
        if swfComputeHashSize:       # pas la peine de les recalculer
            return rtmpDownload(rtmpUrl, swfPlayerUrl, swfForceRefresh,
                                swfComputeHashSize, fileName, swfHash, swfSize)
        elif swfForceRefresh:   # pas la peine de le refaire
            return rtmpDownload(rtmpUrl, swfPlayerUrl, False,
                                swfComputeHashSize , fileName)
        else:                   # on rappelle avec les mêmes options
            return rtmpDownload(rtmpUrl, swfPlayerUrl, swfForceRefresh,
                                swfComputeHashSize, fileName, swfHash, swfSize)
    else:
        return rtmpProc.returncode # = 0

def downloadWatVideo(videoUrl,
                     swfPlayerUrl,
                     swfForceRefresh,
                     swfComputeHashSize,
                     standardDefinition):
    """ recuperation de vidéos sur TF1/TMC/NT1/HD1 (donc WAT)"""
    log.debug('→downloadWatVideo(%s, %s, %s, %s, %s)' % (
            videoUrl, swfPlayerUrl, swfForceRefresh, swfComputeHashSize, standardDefinition))
    # timeout en secondes
    socket.setdefaulttimeout(90)
    debut_id = ''
    html = urllib2.urlopen(videoUrl, None, urlOpenTimeout).read()
    # log.debug('html=%s' %(html))
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
    #referer = [x.strip() for x in re.findall('url : "(.*?)"', debut_id)][0]

    # tsoin-tsoin
    urlReferer = [x.strip() for x in re.findall('url : "(.*?)"', debut_id)][0]
    class MyHTTPRedirectHandler(urllib2.HTTPRedirectHandler):
        def http_error_302(self, req, fp, code, msg, headers):
            log.debug('redirection(%s, %s, %s)' % ( code, msg, headers))
            return headers['Location']
        http_error_301 = http_error_303 = http_error_307 = http_error_302

    openr=urllib2.build_opener(MyHTTPRedirectHandler)
    urllib2.install_opener(openr)
    openr.addheaders=[('User-Agent', ua)]
    reqst=urllib2.Request(urlReferer)
    reqst.add_header("Referer", videoUrl)
    hiddenRef=openr.open(reqst)
    log.debug('on récupère:  %s' % (hiddenRef))
    referer=WEBROOTWAT +  hiddenRef
    # jsonVideoInfos = get_soup(WEBROOTWAT + '/interface/contentv3/' + id,
    #                           WEBROOTWAT +  hiddenRef, ua)
    # tsoin-tsoin

    jsonVideoInfos = get_soup(WEBROOTWAT+'/interface/contentv3/'+id, referer, ua)
    videoInfos = json.loads(jsonVideoInfos)
    log.debug('videoInfos=%s' % (videoInfos))
    if not standardDefinition:
        try:
            HD = videoInfos["media"]["files"][0]["hasHD"]
        except:
            HD = False
    else:
        HD = False

    NumberOfParts = len(videoInfos["media"]["files"])
    ListOfIds = []
    for iPart in range(NumberOfParts):
        ListOfIds.append(videoInfos["media"]["files"][iPart]["id"])
    log.debug('NumberOfParts=%s' % (NumberOfParts))
    sitepage=urllib2.quote(
        re.search("var sitepage='(.*)';", 
                  str(soup.find('script',
                                attrs={'id' : 'scriptPub'}))).group(1),
        safe='')
    for PartId in ListOfIds:
        id_url1 = get_wat(PartId, HD, referer, sitepage)
        req = urllib2.Request(id_url1)
        req.add_header('User-Agent', ua)
        req.add_header('Referer', referer)
        try:
            log.debug('User-Agent: %s' % (ua))
            log.debug('Referer: %s' % (referer))
            resp = urllib2.urlopen(req, None, urlOpenTimeout)
            data = resp.read()
        except urllib2.HTTPError, error:
            if not standardDefinition:
                log.error('Impossible de récupérer la vidéo en HD. Veuillez ré-essayer avec l\'option --standard-definition')
            else:
                log.error('HTTP error avec User-Agent: %s\tReferer: %s' % (ua, referer))
                
            data = error.read()
        log.debug('data=%s' % (data))
        if data[0:4] == 'http':
            if not checkExternalProgram(curlEx):
                log.warning('Ce script requiert %s' % (curlEx))
            else:
                curlCmd = '%s "%s" -C - -L -g -A "%s" -o "%s.mp4"' % (
                    curlEx, data, ua, no + "-" + str(PartId))
                log.info(curlCmd)
                isDownloaded = False
                while not isDownloaded:
                    curlProc = subprocess.Popen(curlCmd,
                                                stdout=subprocess.PIPE,
                                                shell=True)
                    (stdout, stderr) = curlProc.communicate()
                    if curlProc.returncode == 0:
                        isDownloaded = True
                    else:
                        log.debug('curl output:%s' % (stdout))
                        if 'Cannot resume' in stdout:
                            log.warning('Le fichier obtenu est complet ou corrompu')
                            isDownloaded = True # pour sortir quand même...

        if data[0:4] == 'rtmp':
            # vérification de la présence de rtmpdump v2.4 ou v2.5
            if not (checkExternalProgram(rtmpdumpEx, '-help', 'v2.4') or 
                    checkExternalProgram(rtmpdumpEx, '-help', 'v2.5')): # pas top
                log.warning('Ce script requiert %s v2.4 ou v2.5' % (rtmpdumpEx))
            else:
                if '.hd' in data:
                    rtmpUrl = re.search('rtmpte://(.*)hd', data).group(0)
                if '.h264' in data:
                    rtmpUrl = re.search('rtmpte://(.*)h264', data).group(0)
                # log.debug('rtmpUrl=%s'%(rtmpUrl))
                rtmpUrl = rtmpUrl.replace('rtmpte','rtmpe')
                fName=str(no) + '-' + str(PartId) # nom du fichier sans extension
                fileName=fName+'.mp4'             # nom du fichier avec extension
                if rtmpDownload(rtmpUrl, swfPlayerUrl, swfForceRefresh,
                                swfComputeHashSize, fileName) == 0:
                    log.info('Téléchargement terminé')
                    # ffmpeg est-il disponible?
                    if not checkExternalProgram(ffmpegEx):
                        log.info("L'installation de ffmpeg sur votre système permettrait de corriger automatiquement le conteneur de la vidéo (flash→mp4).")
                    else:
                        log.info('conversion ffmpeg fileName → tmpFileName (pour corriger le conteneur)')
                        tmpFileName = fName+'.tmp.mp4'
                        ffmpegCmd = '%s -i "%s" -acodec copy -vcodec copy "%s"' % (ffmpegEx, fileName, tmpFileName)
                        ffmpegCall = shlex.split(ffmpegCmd)
                        ffmpegProc = subprocess.Popen(ffmpegCall,
                                                      stdout=subprocess.PIPE,
                                                      stderr=subprocess.STDOUT)
                        (stdout, stderr) = ffmpegProc.communicate()
                        if ffmpegProc.returncode != 0:
                            log.error('La conversion ffmpeg s\'est terminée en erreur.\nLe fichier %s est vraisemblablement illisible...' % (fileName))
                            if not standardDefinition:
                                log.error('Veuillez ré-essayer avec l\'option --standard-definition')
                            try:
                                os.remove(tmpFileName) # à effacer si il existe
                            except:
                                pass
                        else:
                            log.debug('remplacement %s → %s' % (
                                    tmpFileName, fileName))
                            os.remove(fileName) # pour éviter les WindowsError
                            os.rename(tmpFileName, fileName)
                        log.info('%s est maintenant disponible!' % (fileName))
                else:
                    log.info('Problème réseau ou algo?')

def main():
    """
    Analyse les arguments et lance le téléchargement
    """
    parser=argparse.ArgumentParser(prog=scriptName,
                                   description='Récuperation de vidéos sur TF1/TMC/NT1/HD1 (donc WAT).',
                                   version='%s v%s' % (scriptName,
                                                       scriptVersion))
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
                           const='%s-%s.log' % (re.sub('\.py', '', scriptName),
                                                strftime("%Y%m%d%H%M%S",
                                                         localtime())),
                           metavar='FILE')
    parser.add_argument('-p', '--swf-player-url',
                        help='url du player swf à utiliser (défaut= %s)' % (defaultSwfPlayerUrl),
                        dest='swfPlayerUrl',
                        default=defaultSwfPlayerUrl,
                        action='store',
                        metavar='URL')
    parser.add_argument('-f', '--swf-force-refresh',
                        help='force la vérification du hash/size du player swf (met éventuellement à jour ~/.swfinfo)',
                        dest='swfForceRefresh',
                        default=False,
                        action='store_true')
    parser.add_argument('-c', '--swf-compute-hash-size',
                        help='calcul du hash/size par le script',
                        dest='swfComputeHashSize',
                        default=False,
                        action='store_true')
    parser.add_argument('-s', '--standard-definition',
                        help='ne recherche pas de version Haute-Définition',
                        dest='standardDefinition',
                        default=False,
                        action='store_true')
    parser.add_argument('url',
                        help='url de la page de la video',
                        metavar='URL',
                        nargs='+')
    args=parser.parse_args()

    if args.verbose:
        logging.basicConfig(format='%(levelname)s:\t%(asctime)s: %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.INFO)
    else:
        if args.log:
            logging.basicConfig(filename=args.log,
                                format='%(levelname)s:\t%(asctime)s: %(message)s',
                                datefmt='%H:%M:%S',
                                level=logging.DEBUG)
        else:
            logging.basicConfig(format='%(message)s',
                                datefmt='%H:%M:%S',
                                level=logging.WARNING)
    if args.url:
        for url in args.url:
            log.info('Traitement de l\'url: %s' % (url))
            downloadWatVideo(url,
                             args.swfPlayerUrl,
                             args.swfForceRefresh,
                             args.swfComputeHashSize,
                             args.standardDefinition)

if __name__ == "__main__":
    main()
