#!/usr/bin/env python
# -*- coding:utf-8 -*-
# TV5MondePlus version 0.1 par JUL1EN094 pour mon poto k3c

import urllib, urllib2, sys, re
import xml.etree.ElementTree
import subprocess

class TV5MondePlus(object):
    def __init__(self, url):
        self.url           = url
        self.contentID     = self.get_contentID()
        self.smilUrl       = self.get_smilUrl()
        self.videoUrl      = self.get_videoUrl()
    
    def get_contentID(self):
        try :
            print 'look for the contentID'
            soup = self.getFile(self.url)
            html = soup.decode('utf-8')
            contentID = re.findall("""contentID:'(.*)'""",html)[0]
            print '    ContentID : ' + contentID
            return contentID
        except Exception, e:
            print 'error : not possible to get the contentID'
            print e
            return False
        
    
    def get_httpEnd(self,smilFile) :
        #get best bitrate 
        video_src_s = re.findall("""<video src="(.*)" system-bitrate="(.*)"/>""", smilFile)
        bestBitrate = 0
        httpEnd     = False
        for video_src in video_src_s :
            bitrate = video_src[1]
            if bitrate > bestBitrate :
                bestBitrate = bitrate
                httpEnd     = video_src[0]
        return httpEnd
              
    
    def get_smilUrl(self) :
        try :
            print 'look for the smilUrl'
            root     =  xml.etree.ElementTree.fromstring(self.getFile(self.contentID))
            video    = root.find('video')
            info     = video.find('info')
            videoUrl = info.find('videoUrl')
            smilUrl  = videoUrl.text
            print '    smilUrl : '+smilUrl
            return smilUrl
        except Exception, e:
            print 'error : not possible to get the smilURL'
            print e
            return False
    
    def get_videoUrl(self) :
        try :
            global videoUrl
            print 'look for the videoUrl'
            smilFile = self.getFile(self.smilUrl)
            httpBase = re.findall("""<meta name="httpBase" content="(.*)" />""", smilFile)[0]
            httpEnd  = self.get_httpEnd(smilFile)
            videoUrl = httpBase+httpEnd
            print '    videoUrl : '+videoUrl
            return videoUrl
        except Exception, e:
            print 'error : not possible to get the videoUrl'
            print e
            return False        
    
    def getFile(self, url):
        request = urllib2.Request(url)
        request.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:17.0) Gecko/20100101 Firefox/17.0')
        response = urllib2.urlopen(request,timeout = 10)
        return response.read()

def main():
    x = TV5MondePlus(sys.argv[1]) 

if __name__ == "__main__":
    main()
    tit = sys.argv[1].split('/')[-1]+'.mp4'
    print 'titre',tit
    args = ["/usr/bin/msdl","-c","--no-proxy", videoUrl , "-o", tit]
    print args
    app = subprocess.Popen(args=args, stdout=open('somefile', 'w'))
    app.wait()
