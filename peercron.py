#!/usr/bin/env python

__author__ = "Finn Herzfeld"
__copyright__ = "Copyright 2014, Finn Herzfeld"
__credits__ = ["Finn Herzfeld"]
__license__ = "GPL"
__version__ = "0.5"
__maintainer__ = "Finn Herzfeld"
__email__ = "finn@seattlemesh.net"
__status__ = "Development"

import sys
import os
import json
import time
import urllib2
from hashlib import sha1
from urllib import urlencode
import subprocess

def notify(message):
    title = "Peer cron on %s" % open("/etc/hostname").read().strip()
    for token in ["cgiFjIzrmWBkMjOHg4ZN"]:
        params = {"token": token, "title": title, "message": message}
        url = "https://www.thefinn93.com/push/send?" + urlencode(params)
        urllib2.urlopen(url)
    print message

try:
    import cjdnsadmin
except ImportError:
    sys.path.append("/opt/cjdns/contrib/python/cjdnsadmin")
    try:
        import cjdnsadmin
    except ImportError:
        notify("Failed to import cjdnsadmin!")
        sys.exit(1)

cjdns = cjdnsadmin.connectWithAdminInfo()

if not os.path.isfile("/tmp/stoppeercron"):
    try:
        data = json.load(open(sys.argv[1]))
    except IOError:
        data = {}
    except ValueError:
        print "Teh JSONz are fux0r'd"
        open("/tmp/stoppeercron", "a").close()
        sys.exit(1)
else:
    sys.exit(0)


if not "version" in data:
    data['version'] = ""

version = sha1(open(sys.argv[0]).read()).hexdigest()
if version != data['version']:
    notify("Updated to version %s" % version)
    data['version'] = version

def dbg(msg, level="DEBUG"):
    #levels = ["DEBUG", "INFO", "WARN", "ERROR"]
    if os.getenv("LOGLEVEL") != "":
        if os.getenv("LOGLEVEL") == level:
            print "%s: %s" % (level, msg)

def publictoip6(pubkey):
    proc = subprocess.Popen(["/opt/cjdns/build/publictoip6", pubkey], stdout=subprocess.PIPE)
    proc.wait()
    return proc.stdout.read().strip()

i = 0
more = True
while more:
    peertable = cjdns.InterfaceController_peerStats(i)
    more = "more" in peertable
    i += 1
    for peer in peertable['peers']:
        pubkey = peer['publicKey']
        dbg("Checking peer %s" % pubkey)
        if not pubkey in data:
            dbg("%s is new" % pubkey)
            data[pubkey] = peer.copy()
        data[pubkey]['lastseen'] = time.time()
        if "user" in data[pubkey]:
            if type(data[pubkey]['user']) != dict:
                user = data[pubkey]['user']
                data[pubkey]['user'] = {}
                data[pubkey]['user'][user] = time.time()
        else:
            data[pubkey]['user'] = {}
        if "user" in peer:
            dbg("%s is using %s's peering password" % (pubkey, peer['user']))
            if not peer['user'] in data[pubkey]['user']:
                data[pubkey]['user'][peer['user']] = time.time()
                notify("ALERT: %s starting using %s's peering password" % (pubkey, peer['user']))
        if not "version" in data[pubkey]:
            data[pubkey]['version'] = {}
        ping = cjdns.RouterModule_pingNode(publictoip6(pubkey))
        if "version" in ping:
            if not ping['version'] in data[pubkey]['version']:
                data[pubkey]['version'][ping['version']] = time.time()

save = open(sys.argv[1], "w")
save.write(json.dumps(data,  sort_keys=True, indent=4, separators=(',', ': ')))
save.close()
