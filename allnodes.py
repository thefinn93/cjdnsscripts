#!/usr/bin/env python

import sys, os
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
