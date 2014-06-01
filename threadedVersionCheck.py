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
import Queue
import threading

try:
    from cjdnsadmin import connectWithAdminInfo
except ImportError:
    sys.path.append("/opt/cjdns/contrib/python/cjdnsadmin")
    from cjdnsadmin import connectWithAdminInfo
cjdns = connectWithAdminInfo()

debug = False
if "-v" in sys.argv:
    debug = True

class VersionCheckThread(threading.Thread):
    """Threaded cjdns version checker"""

    def __init__(self, queue, versions, timeout, threadNumber):
        threading.Thread.__init__(self)
        self.queue = queue
        self.versions = versions
        self.timeout = timeout
        self.threadNumber = threadNumber

    def run(self):
        while True:
            node = self.queue.get()
            if debug:
                print "[Thread #%i] Preparing to version check %s" % (self.threadNumber, node)
            if self.timeout is not None:
                ping = cjdns.RouterModule_pingNode(node, self.timeout)
            else:
                ping = cjdns.RouterModule_pingNode(node)
            if 'version' in ping or 'protocol' in ping:
                if 'version' in ping:
                    if debug:
                        print "[Thread #%i] %s has version %s" % (self.threadNumber, node, ping['version'])
                    if not ping['version'] in self.versions['cjdns']:
                        self.versions['cjdns'][ping['version']] = 0
                    self.versions['cjdns'][ping['version']] += 1
                if 'protocol' in ping:
                    if debug:
                        print "[Thread #%i] %s is using protocol #%s" % (self.threadNumber, node, ping['protocol'])
                    if not ping['protocol'] in self.versions['protocol']:
                        self.versions['protocol'][ping['protocol']] = 0
                    self.versions['protocol'][ping['protocol']] += 1
            elif 'result' in ping:
                if debug:
                    print "[Thread #%i] %s did not ping: %s" % (self.threadNumber, node, ping['result'])
                if not ping['result'] in self.versions['error']:
                    self.versions['error'][ping['result']] = 0;
                self.versions['error'][ping['result']] += 1
            elif 'error' in ping:
                if debug:
                    print "[Thread #%i] %s did not ping (error): %s" % (self.threadNumber, node, ping['error'])
                if not ping['error'] in self.versions:
                    self.versions['error'][ping['error']] = 0
                self.versions['error'][ping['error']] += 1
            self.queue.task_done()

def getVersions(timeout=None, threads=5):
    versions = {"cjdns": {}, "protocol": {}, "error": {}}
    q = Queue.Queue()
    if timeout is not None:
        print "Setting timeout to %i milliseconds" % timeout
    print "Starting %i threads" % threads
    for i in range(threads):
        t = VersionCheckThread(q, versions, timeout, i)
        t.daemon = True
        t.start()

    more = True
    i = 0
    nodes = []
    while more:
        table = cjdns.NodeStore_dumpTable(i)
        more = "more" in table
        more = False # Testing purposes only, delete to do it all
        if 'routingTable' in table:
            for route in table['routingTable']:
                if not route['ip'] in nodes:
                    nodes.append(route['ip'])
                    q.put(route['ip'])
        else:
            if debug:
                print "No routing table. Wat: %s" % json.dumps(table)
        i += 1

    return versions

if __name__ == "__main__":
    data = {}
    startTime = time.time()
    data["versions"] =  getVersions(5000, 3)
    data["collectedAt"] = time.time()
    data["runtime"] = time.time() - startTime

    file = None
    if len(sys.argv) > 2 and "-v" in sys.argv:
        file = sys.argv[1]
    elif len(sys.argv) > 1 and not "-v" in sys.argv:
        file = sys.argv[1]

    if file is not None:
        a = open(file, "w")
        a.write(json.dumps(data))
        a.close()
    else:
        print json.dumps(data, indent=4, separators=(',', ': '))
