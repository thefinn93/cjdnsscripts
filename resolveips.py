#!/usr/bin/env python

__author__ = "Finn Herzfeld"
__copyright__ = "Copyright 2014, Finn Herzfeld"
__credits__ = ["Finn Herzfeld"]
__license__ = "GPL"
__version__ = "0.5"
__maintainer__ = "Finn Herzfeld"
__email__ = "finn@seattlemesh.net"
__status__ = "Development"

import subprocess
import sys
import json
try:
    import cjdnsadmin
except:
    print "Failed to find cjdnsadmin in the normal search path. Hax in progress..."
    sys.path.append("/opt/cjdns/contrib/python/cjdnsadmin")
    try:
        import cjdnsadmin
    except:
        print "Failed to import cjdnsadmin!"
        sys.exit(1)

def publictoip6(pubkey):
    proc = subprocess.Popen(["/opt/cjdns/build/publictoip6", pubkey], stdout=subprocess.PIPE)
    proc.wait()
    return proc.stdout.read().strip()

def rdns(ip):
    # http://[fc5d:baa5:61fc:6ffd:9554:67f0:e290:7535]/nodes/list.json
    nodelist = json.load(open("list.json"))
    out = None
    for node in nodelist['nodes']:
        if node['ip'] == ip:
            out = node
            break
    return out
try:
    keys = open(sys.argv[1]).read().split("\n")
    for key in keys:
        if key == "":
            print key
        elif key[0] == "#":
            print key
        else:
            ip = publictoip6(key)
            dns = rdns(ip)
            if dns is not None:
                print "%s\t%s\t%s" % (key, ip, dns['name'])
            else:
                print "%s\t%s\t-" % (key, ip)

except IOError:
    ip = publictoip6(sys.argv[1])
    dns = rdns(ip)
    if dns is not None:
        print "%s\t%s\t%s" % (sys.argv[1], ip, dns['name'])
    else:
        print "%s\ts\t-" % (sys.argv[1], ip)
