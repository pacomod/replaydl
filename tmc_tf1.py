# -*- coding:utf-8 -*-
# TF1 TMC NT1 HD1 version 0.5 par k3c, correction de 11gjm
import subprocess, optparse, re, sys, shlex
import socket
from urllib2 import urlopen
import time, md5, random, urllib2
import bs4 as BeautifulSoup
listeUserAgents = [ 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_5; fr-fr) AppleWebKit/525.18 (KHTML, like Gecko) Version/3.1.2 Safari/525.20.1',
                                                'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.186 Safari/535.1',
                                                'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.27 Safari/525.',
                                                'Mozilla/5.0 (X11; U; Linux x86_64; en-us) AppleWebKit/528.5+ (KHTML, like Gecko, Safari/528.5+) midori',
                                                'Mozilla/5.0 (Windows NT 6.0) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.107 Safari/535.1',
                                                'Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en-us) AppleWebKit/312.1 (KHTML, like Gecko) Safari/312',
                                                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.12 Safari/535.11',
                                                'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.8 (KHTML, like Gecko) Chrome/17.0.940.0 Safari/535.8' ]

def get_wat(id):
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
    id_url1 = "http://www.wat.tv/get/web/"+str(id)+"?token="+token+"/"+timesec+"&getURL=1&country=FR"
    return id_url1

def main():
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
    id_url1 = get_wat('9064731')
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', random.choice(listeUserAgents))]
    data = opener.open(id_url1).read()
    opener.close()
    if data[0:4] == 'http':
        ua = random.choice(listeUserAgents)
        arguments = 'curl "%s" -L -g -A "%s" -o "%s.mp4"' % (data, ua, no)
        print arguments
        process = subprocess.Popen(arguments, stdout=subprocess.PIPE, shell=True).communicate()[0]
    if data[0:4] == 'rtmp':
        host = re.search('rtmpte://(.*)/ondemand', data).group(1)
        host = host.replace('rtmpte', 'rtmpe')
        data0 = re.search('rtmpte://(.*)h264', data).group(0)
        cmds = 'rtmpdump -r "%s" -c 1935 -m 10 -w ebb7a6fbdc9021db95e2bd537d73fabb9717508f085bea50bde75f7a8e27698c -x 343642 -o "%s.mp4" " --resume"' % (data0, str(no)
)
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
                print "Erreur : le sous-process s\'est terminé avec (le code d\'erreur est " + str(p.returncode) + ")"
#                status = False
                if cpt > 5:
                    break
                cpt += 1
                time.sleep(3) 
            else:
#                status = True
                break
if __name__ == "__main__":
    main()
