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
try:
    from cjdnsadmin import connectWithAdminInfo
except ImportError:
    sys.path.append("/opt/cjdns/contrib/python/cjdnsadmin")
    from cjdnsadmin import connectWithAdminInfo
cjdns = connectWithAdminInfo()

i = 0
nodes = []
more = True
while more:
    table = cjdns.NodeStore_dumpTable(i)
    more = "more" in table
    for route in table['routingTable']:
        if not route['ip'] in nodes:
            nodes.append(route['ip'])
    i += 1
print "\n".join(nodes)
