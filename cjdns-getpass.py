#!/usr/bin/env python

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

peers = {}
i = 0
more = True
while more:
    data = cjdns.InterfaceController_peerStats(i)
    more = "more" in data
    i += 1
    for peer in data['peers']:
        peers[peer['publicKey']] = None
        if "user" in peer:
            peers[peer['publicKey']] = peer['user']
        if peer['publicKey'] == searchfor:
            more = False

if searchfor is None:
    for pubkey in peers:
        print "%s\t%s\t%s" % (pubkey, publictoip6(pubkey), peers[pubkey])
else:
    if searchfor in peers:
        print "%s\t%s\t%s" % (searchfor, publictoip6(searchfor), peers[searchfor])
    else:
        print "Failed to find %s" % searchfor
        sys.exit(1)
        

