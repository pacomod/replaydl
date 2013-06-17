#!/usr/bin/python
#-*- coding:utf-8 -*-

# generic
import argparse
from time import localtime, strftime
import logging

# specific
import base64
import urllib2                  # → pas que urlopen (exceptions, etc.)
import hashlib                  # → sha256sum
import zlib
import StringIO

# script globvars
scriptName='getSwfInfo'
scriptVersion='1.0'
versionString='%s v%s' % (scriptName, scriptVersion)

# default/valid values
validHash='0818931e9bfa764b9c33e42de6d06f924ac7fc244d0d4941019b9cdfe8706705'
validSize=352043

# global logger
log=logging.getLogger(__name__)

def computeSwfPlayerHash(swfPlayerUrl):
    """
    Essais → swf size & hash
    """
    try:
        swfPlayer= urllib2.urlopen(swfPlayerUrl).read()
    except ValueError:
        log.error('Url invalide: %s' %(swfPlayerUrl))
        return
    except urllib2.URLError:
        log.error("Pb avec l'url")
        return
    except urllib2.HTTPError:
        log.error("Pb http")
        return

    swfPlayerSize=len(swfPlayer)
    swfPlayerHash=hashlib.sha224(swfPlayer).hexdigest()
    if type(swfPlayer) is str:
        swfData=StringIO.StringIO(swfPlayer)
    swfData.seek(0, 0)
    magic=swfData.read(3)
    if magic != "CWS":
        log.error("Pas de CWS...")
    else:
        unzPlayer="CWS" + swfData.read(5) + zlib.decompress(swfData.read())
        unzPlayerSize=len(unzPlayer)
        sha256Player=hashlib.sha256(unzPlayer)
        unzPlayerHash=sha256Player.hexdigest()
        # b64PlayerHash=base64.b64encode(unzPlayerHash.decode('hex'))
        b64PlayerHash=base64.urlsafe_b64encode(sha256Player.hexdigest().decode('hex'))

    log.info('url: %s\n' %(swfPlayerUrl))
    log.debug('*-*- Compressed -*-*\n\tsize: %i\n\thash: %s\n\thlen: %i\n' % (
            swfPlayerSize, swfPlayerHash, len(swfPlayerHash)))
    log.info('*-*- Uncompressed -*-*\n\tsize: %i\n\thash: %s\n\thlen: %i\n' % (
            unzPlayerSize, unzPlayerHash, len(unzPlayerHash)))
    log.debug('*-*- b64Encoded -*-*\n\thash: %s\n\thlen: %i\n' % (
            b64PlayerHash, len(b64PlayerHash)))


def main():
    """
    compute/display/log size & hash of swf player
    """
    parser=argparse.ArgumentParser(prog=scriptName,
                                     description='compute swf player hash.',
                                     version=versionString)
    parser.add_argument('-d', '--default',
                        help='show default value',
                        dest='displayValidHash',
                        action='store_true',
                        default=False)
    parser.add_argument('-u', '--url',
                        help='url of swf player',
                        dest='swfPlayerUrl',
                        action='store',
                        metavar='URL')
    verbOrLog=parser.add_mutually_exclusive_group()
    verbOrLog.add_argument('-V', '--verbose',
                           help="display information messages",
                           dest='verbose',
                           action='store_true',
                           default=False)
    verbOrLog.add_argument('-l', '--log',
                           help="log information messages",
                           dest='log',
                           action='store_const',
                           const='%s-%s.log' % (scriptName,
                                                strftime("%Y%m%d%H%M%S",
                                                         localtime())),
                           metavar='FILE')
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
            logging.info(args.log)
        else:
            logging.basicConfig(format='%(message)s',
                                datefmt='%H:%M:%S',
                                level=logging.INFO)

    if args.swfPlayerUrl:
        log.debug('swfPlayerUrl: %s' % (args.swfPlayerUrl))
        computeSwfPlayerHash(args.swfPlayerUrl)

    if args.displayValidHash:
        log.info('*-*- Valid hash -*-*\n\tsize: %x\n\thash: %s\n\thlen: %i\n' % (
                validSize, validHash, len(validHash)))
        
if __name__ == "__main__":
    main()
