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
import subprocess

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

searchfor = None
if len(sys.argv) > 1:
    searchfor = sys.argv[1]

def publictoip6(pubkey):
    proc = subprocess.Popen(["/opt/cjdns/build/publictoip6", pubkey], stdout=subprocess.PIPE)
    proc.wait()
    return proc.stdout.read().strip()


cjdns = cjdnsadmin.connectWithAdminInfo()

ips = []
i = 0
more = True
while more:
    data = cjdns.NodeStore_dumpTable(i)
    more = "more" in data
    i += 1
    for route in data['routingTable']:
        if not route['ip'] in ips:
            ips.append(route['ip'])

if len(sys.argv) > 1:
    print " ".join(ips[:int(sys.argv[1])])
else:
    print " ".join(ips)
