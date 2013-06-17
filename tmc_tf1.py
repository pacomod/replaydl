#!/usr/bin/python
#-*- coding:utf-8 -*-
# TF1 TMC NT1 HD1 V0.9.4 par k3c, bibichouchou et pacome: rtmpdump -W, vérif programme externes, algo conversion 

import subprocess, optparse, re, sys, shlex
import socket
from urllib2 import urlopen
import time, md5, random, urllib2, json
import bs4 as BeautifulSoup
import os                       # → os.remove
from urlparse import urlparse

listeUserAgents = [ 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_5; fr-fr) AppleWebKit/525.18 (KHTML, like Gecko) Version/3.1.2 Safari/525.20.1',
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
ua=random.choice(listeUserAgents)
# swf players
swfWatPlayerLite="www.wat.tv/images/v40/PlayerWat.swf" # fourni par JUL1EN094
swfWatPlayerWat="www.wat.tv/images/v70/PlayerLite.swf" # trouvé sur le www.wat.tv
# programmes externes utilisés
ffmpegEx='ffmpeg'
rtmpdumpEx='rtmpdump'

def checkExternalProgram(prog, optArg='', expectedValue=''):
    """ Permet de vérifier la présence des programmes externes requis """
    args=shlex.split('%s %s' % (prog, optArg))
    try:
        process=subprocess.Popen(args,stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = process.communicate()
        if expectedValue == '':
            return True
        else:
            if expectedValue in stdout: # à améliorer pour versions > ...
                return True
            else:
                return False
    except OSError:
        print 'Le programme %s n\'est pas présent sur votre système' % (prog)
        return False

def get_soup(url, referer, ua):
    """ on récupère la soupe """
    req  = urllib2.Request(url)
    req.add_header('User-Agent', ua)
    req.add_header('Referer', referer)
    soup = urllib2.urlopen(req).read()
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
    return id_url1

def main():
    """ recuperation de vidéos sur TF1/TMC/NT1/HD1 (donc WAT)"""
    # vérification de la présence de rtmpdump v2.4 ou v2.5
    if not checkExternalProgram(rtmpdumpEx, '-help', 'v2.4'):
        if not checkExternalProgram(rtmpdumpEx, '-help', 'v2.5'): # pas top...
            print 'Ce script requiert %s v2.4 ou v2.5' % (rtmpdumpEx)
            return
    # timeout en secondes
    socket.setdefaulttimeout(90)
    usage   = "usage: python tmc_tf1.py     [options] <url de l'emission>"
    parser  = optparse.OptionParser( usage = usage )
    parser.add_option( "--nocolor",         action = 'store_true', default = False, help = 'desactive la couleur dans le terminal' )
    parser.add_option( "-v", "--verbose",   action = "store_true", default = False, help = 'affiche les informations de debugage' )
    ( options, args ) = parser.parse_args()
    if( len( args ) > 2 or args[ 0 ] == "" ):
        parser.print_help()
        parser.exit( 1 )
    debut_id = ''
    html = urllib2.urlopen(sys.argv[1]).read()
    nom = sys.argv[1].split('/')[-1:][0]
    no = nom.split('.')[-2:][0]
    soup = BeautifulSoup.BeautifulSoup(html)
    site = urlparse(sys.argv[1]).netloc
    if 'tmc.tv' in site or 'tf1.fr' in site:
        debut_id = str(soup.find('div', attrs={'class' : 'unique' }))
    if 'nt1.tv' in site or 'hd1.tv' in site:
        debut_id = str(soup.find('section', attrs={'class' : 'player-unique' }))
    id = [x.strip() for x in re.findall("mediaId :([^,]*)", debut_id)][0]
    referer = [x.strip() for x in re.findall('url : "(.*?)"', debut_id)][0]
    jsonVideoInfos = get_soup(WEBROOTWAT+'/interface/contentv3/'+id, referer, ua)
    videoInfos     = json.loads(jsonVideoInfos)

    try:
        HD = videoInfos["media"]["files"][0]["hasHD"]
    except:
        HD = False

    NumberOfParts = len(videoInfos["media"]["files"])
    ListOfIds = []
    for iPart in range(NumberOfParts):
        ListOfIds.append(videoInfos["media"]["files"][iPart]["id"])

    for PartId in ListOfIds:
        id_url1 = get_wat(PartId, HD)
        req  = urllib2.Request(id_url1)
        req.add_header('User-Agent', ua)
        req.add_header('Referer', referer)
        data = urllib2.urlopen(req).read()
        # print data
        # print type(data)
        if data[0:4] == 'http':
            arguments = 'curl "%s" -C - -L -g -A "%s" -o "%s.mp4"' % (data, ua, no + "-" + str(PartId))
            print arguments
            process = subprocess.Popen(arguments, stdout=subprocess.PIPE, shell=True).communicate()[0]
        if data[0:4] == 'rtmp':
            if '.hd' in data:
                data0 = re.search('rtmpte://(.*)hd', data).group(0)
            if '.h264' in data:
                data0 = re.search('rtmpte://(.*)h264', data).group(0)
            data0 = data0.replace('rtmpte','rtmpe')
            fName=str(no) + "-" + str(PartId) # nom du fichier final sans extension
            fileName=fName+".mp4"             # nom du fichier final avec extension
            # ffmpeg est-il disponible?
            if not checkExternalProgram(ffmpegEx):
                print "L'installation de ffmpeg sur votre système permettrait de corriger automatiquement le conteneur de la vidéo (flash→mp4)."
                tmpFileName=fileName
                ffmpegAvailable=False
            else:
                tmpFileName=fName+".tmp.mp4"
                ffmpegAvailable=True
            rtmpCmd = '%s -e -r "%s" -c 443 -m 10 -W %s -o "%s"' % (rtmpdumpEx, data0, swfWatPlayerLite, tmpFileName)
            print rtmpCmd
            arguments = shlex.split( rtmpCmd )
            # print arguments
            cpt = 0 
            while True:
                p = subprocess.Popen(arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = p.communicate()
                if p.returncode != 0:
                    print "Erreur : le sous-process s\'est terminé avec (le code d\'erreur est " + str(p.returncode) + ")"
                    if cpt > 5:
                        break
                    cpt += 1
                    time.sleep(3) 
                else:
                    if ffmpegAvailable:
                        # conversion ffmpeg tmpFileName → fileName (pour corriger le conteneur)
                        ffmpegCmd='ffmpeg -i "%s" -acodec copy -vcodec copy "%s"' % (tmpFileName, fileName)
                        arguments=shlex.split(ffmpegCmd)
                        p=subprocess.Popen(arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        stdout, stderr = p.communicate()
                        if p.returncode != 0:
                            print 'Erreur: la conversion ffmpeg s\'est terminée avec le code d\'erreur %i.\nLe fichier %s est néanmois disponible' % (p.returncode, tmpFileName)
                        else:
                            # suppression du fichier temporaire
                            os.remove(tmpFileName)
                    break

if __name__ == "__main__":
    main()
