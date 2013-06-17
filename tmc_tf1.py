#!/usr/bin/python
# -*- coding:utf-8 -*-
# TF1 TMC NT1 HD1 version 0.8 par k3c, telecharge lien en rtmpdump en HD, pas curl
import subprocess, optparse, re, sys, shlex
import socket
from urllib2 import urlopen
import time, md5, random, urllib2, json
import bs4 as BeautifulSoup
listeUserAgents = [ 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_5; fr-fr) AppleWebKit/525.18 (KHTML, like Gecko) Version/3.1.2 Safari/525.20.1',
                                                'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.186 Safari/535.1',
                                                'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.27 Safari/525.',
                                                'Mozilla/5.0 (X11; U; Linux x86_64; en-us) AppleWebKit/528.5+ (KHTML, like Gecko, Safari/528.5+) midori',
                                                'Mozilla/5.0 (Windows NT 6.0) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.107 Safari/535.1',
                                                'Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en-us) AppleWebKit/312.1 (KHTML, like Gecko) Safari/312',
                                                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.12 Safari/535.11',
                                                'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.8 (KHTML, like Gecko) Chrome/17.0.940.0 Safari/535.8' ]

WEBROOTWAT          = "http://www.wat.tv"
wat_url      = "/web/"
jsonVideosInfos    = ""
def get_soup(url, referer):
    """ on récupère la soupe """
    ua = random.choice(listeUserAgents)
    req  = urllib2.Request(url)
    req.add_header('User-Agent', ua)
    req.add_header('Referer', referer)
    soup = urllib2.urlopen(req).read()
    return soup

def get_wat(id):
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
    ts = base36encode(int(time.time()))
    timesec = hex(int(ts, 36))[2:]
    while(len(timesec)<8):
        timesec = "0"+timesec
    token = md5.new("9b673b13fa4682ed14c3cfa5af5310274b514c4133e9b3a81e6e3aba00912564/web/"+str(id)+""+timesec).hexdigest()
    id_url1 = WEBROOTWAT+"/get"+wat_url+str(id)+"?token="+token+"/"+str(timesec)+"&country=FR&getURL=1"
    return id_url1

def main():
    """ recuperation de vidéos sur TF1/TMC/NT1/HD1 (donc WAT)"""
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
    html = urlopen(sys.argv[1]).read()
    nom = sys.argv[1].split('/')[-1:][0]
    no = nom.split('.')[-2:][0]
    soup = BeautifulSoup.BeautifulSoup(html)
    if 'tmc.tv' in str(soup) or 'tf1.fr' in str(soup):
        debut_id = str(soup.find('div', attrs={'class' : 'unique' }))
    if 'nt1.tv' in str(soup) or 'hd1.tv' in str(soup):
        debut_id = str(soup.find('section', attrs={'class' : 'player-unique' }))
    id = [x.strip() for x in re.findall("mediaId :([^,]*)", debut_id)][0]
    referer = [x.strip() for x in re.findall('url : "(.*?)"', debut_id)][0]
    id_url1 = get_wat(id)
    req  = urllib2.Request(id_url1)
    req.add_header('User-Agent', random.choice(listeUserAgents))
    req.add_header('Referer', referer)
    data = urllib2.urlopen(req).read()
    ua = random.choice(listeUserAgents)
    jsonVideoInfos = get_soup(WEBROOTWAT+'/interface/contentv3/'+id, referer)
    videoInfos     = json.loads(jsonVideoInfos)
    try :
        HD = videoInfos["media"]["files"][0]["hasHD"]
        data = data.replace('H264-384x288','HD-1280x720').replace('.h264','.hd')
        data0 = re.search('rtmpte://(.*)hd', data).group(0)
        wat_url = "/webhd/"
    except :
        wat_url = "/web/"  
        data0 = re.search('rtmpte://(.*)h264', data).group(0)  
    if data[0:4] == 'http':
        ua = random.choice(listeUserAgents)
        arguments = 'curl "%s" -C - -L -g -A "%s" -o "%s.mp4"' % (data, ua, no)
        print arguments
        p = subprocess.Popen(arguments, stdout=subprocess.PIPE, shell=True).communicate()[0]
    if data[0:4] == 'rtmp':
        host = re.search('rtmpte://(.*)/ondemand', data).group(1)
        host = host.replace('rtmpte', 'rtmpe')

        data0 = data0.replace('rtmpte','rtmpe')
        # cmds = 'rtmpdump -r "%s" -c 443 -m 10 -w b23434cbed89c9eaf520373c4c6f26e1f7326896dee4b1719e8d9acda0c19e99 -x 343427 -o "%s.mp4" " --resume"' % (data0, str(no)) # needs a new swf hash ?
        cmds='rtmpdump -r "%s" -c 1935  -o "%s.mp4" -e' % (data0, str(no))
        f = open(str(no), 'w')
        f.write(cmds)
        f.close()
        arguments = shlex.split( cmds )
        print arguments
        cpt = 0 
        while True:
            p = subprocess.Popen( arguments,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                print "stdout: " + stdout
                print "stderr: " + stderr
                print "Erreur : le sous-process s\'est terminé avec (le code d\'erreur est " + str(p.returncode) + ")"
#                status = False
                if cpt > 5:
                    break
                cpt += 1
                time.sleep(3) 
            else:
                break
if __name__ == "__main__":
    main()
