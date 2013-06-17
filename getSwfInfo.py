#!/usr/bin/python
#-*- coding:utf-8 -*-

urlWatPlayerv40="http://www.wat.tv/images/v40/PlayerWat.swf" # fourni par JUL1EN094
urlWatPlayerv30="http://www.wat.tv/images/v30/PlayerWat.swf"
urlWatPlayerLite="http://www.wat.tv/images/v70/PlayerLite.swf" # trouvé sur le www.wat.t
urlWatPlayer=urlWatPlayerv30
validHash='0818931e9bfa764b9c33e42de6d06f924ac7fc244d0d4941019b9cdfe8706705'
validSize=352043

# from urllib2 import urlopen
import base64
import urllib2                  # → pas que urlopen (exceptions, etc.)
import hashlib                  # → sha256sum
import zlib
import StringIO

def main():
    """
    Essais → swf size & hash
    """
    try:
        swfPlayer= urllib2.urlopen(urlWatPlayer).read()
    except urllib2.URLError:
        print "Pb avec l'url"
    except urllib2.HTTPError:
        print "Pb http"

    swfPlayerSize=len(swfPlayer)
    swfPlayerHash=hashlib.sha224(swfPlayer).hexdigest()
    if(type(swfPlayer) is str):
        swfData=StringIO.StringIO(swfPlayer)
    swfData.seek(0, 0)
    magic=swfData.read(3)
    if(magic != "CWS"):
        print "Pas de CWS..."
    else:
        unzPlayer="CWS" + swfData.read(5) + zlib.decompress(swfData.read())
        unzPlayerSize=len(unzPlayer)
        sha256Player=hashlib.sha256(unzPlayer)
        unzPlayerHash=sha256Player.hexdigest()
        # b64PlayerHash=base64.b64encode(unzPlayerHash.decode('hex'))
        b64PlayerHash=base64.urlsafe_b64encode(sha256Player.hexdigest().decode('hex'))

    print 'url: %s\n' %(urlWatPlayer)
    print '*-*- Compressed -*-*\nsize: %i\nhash: %s\nhlen:%i\n' % (swfPlayerSize, swfPlayerHash, len(swfPlayerHash))
    print '*-*- Uncompressed -*-*\nsize: %i\nhash: %s\nhlen:%i\n' % (unzPlayerSize, unzPlayerHash, len(unzPlayerHash))
    print '*-*- b64Encoded -*-*\nhash: %s\nhlen:%i\n' % (b64PlayerHash, len(b64PlayerHash))
    print '*-*- Valid -*-*\nsize: %i\nhash: %s\nhlen:%i\n' % (validSize, validHash, len(validHash))

if __name__ == "__main__":
    main()
