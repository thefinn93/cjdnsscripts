#!/usr/bin/env python

__author__ = "Finn Herzfeld"
__copyright__ = "Copyright 2014, Finn Herzfeld"
__credits__ = ["Finn Herzfeld"]
__license__ = "GPL"
__version__ = "0.5"
__maintainer__ = "Finn Herzfeld"
__email__ = "finn@seattlemesh.net"
__status__ = "Development"

import json
import sys
import os

conf = json.load(open(sys.argv[1]))

existingifaces = []
if "ETHInterface" in conf['interfaces']:
    for interface in conf['interfaces']['ETHInterface']:
        existingifaces.append(interface['bind'])
else:
    conf['interfaces']['ETHInterface'] = []

for dev in os.listdir("/sys/class/net"):
    if dev not in existingifaces:
        # What is a good way to detect physical vs virtual devices? I highly doubt this is way is any good
        if "virtual" not in os.path.realpath("/sys/class/net/%s" % dev):
            print "Adding ETHInterface to %s" % dev
            conf['interfaces']['ETHInterface'].append({"connectTo": {}, "bind": dev, "beacon": 2})
        else:
            print "Ignoring %s because it is a virtual interface" % dev
    else:
        print "ETHInterface already set up for %s" % dev

save = open(sys.argv[1], "w")
save.write(json.dumps(conf, sort_keys=True, indent=4, separators=(',', ': ')))
save.close()
