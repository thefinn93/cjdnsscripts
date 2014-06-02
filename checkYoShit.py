#!/usr/bin/env python2

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
import socket
import hashlib
import json
import threading
import time
import Queue
import random
import string

# SETTINGS N SHIT #
# You shouldn't need to touch these
# But if you know what you're doing you can
clearnetDNShost = "uppit.us"
clearnetDNSresult = "fc3a:956e:4b69:1c1e:5ebc:11a5:3e71:3e7e"
###################

# For fuckers who don't have the libraries installed
BUFFER_SIZE = 69632
KEEPALIVE_INTERVAL_SECONDS = 2

# Proly dont have bencode either
class BTFailure(Exception):
    pass

def decode_int(x, f):
    f += 1
    newf = x.index('e', f)
    n = int(x[f:newf])
    if x[f] == '-':
        if x[f + 1] == '0':
            raise ValueError
    elif x[f] == '0' and newf != f+1:
        raise ValueError
    return (n, newf+1)

def decode_string(x, f):
    colon = x.index(':', f)
    n = int(x[f:colon])
    if x[f] == '0' and colon != f+1:
        raise ValueError
    colon += 1
    return (x[colon:colon+n], colon+n)

def decode_list(x, f):
    r, f = [], f+1
    while x[f] != 'e':
        v, f = decode_func[x[f]](x, f)
        r.append(v)
    return (r, f + 1)

def decode_dict(x, f):
    r, f = {}, f+1
    while x[f] != 'e':
        k, f = decode_string(x, f)
        r[k], f = decode_func[x[f]](x, f)
    return (r, f + 1)

decode_func = {}
decode_func['l'] = decode_list
decode_func['d'] = decode_dict
decode_func['i'] = decode_int
decode_func['0'] = decode_string
decode_func['1'] = decode_string
decode_func['2'] = decode_string
decode_func['3'] = decode_string
decode_func['4'] = decode_string
decode_func['5'] = decode_string
decode_func['6'] = decode_string
decode_func['7'] = decode_string
decode_func['8'] = decode_string
decode_func['9'] = decode_string

def bdecode(x):
    try:
        r, l = decode_func[x[0]](x, 0)
    except (IndexError, KeyError, ValueError):
        raise BTFailure("not a valid bencoded string")
    if l != len(x):
        raise BTFailure("invalid bencoded value (data after valid prefix)")
    return r

from types import StringType, IntType, LongType, DictType, ListType, TupleType


class Bencached(object):

    __slots__ = ['bencoded']

    def __init__(self, s):
        self.bencoded = s

def encode_bencached(x,r):
    r.append(x.bencoded)

def encode_int(x, r):
    r.extend(('i', str(x), 'e'))

def encode_bool(x, r):
    if x:
        encode_int(1, r)
    else:
        encode_int(0, r)

def encode_string(x, r):
    r.extend((str(len(x)), ':', x))

def encode_list(x, r):
    r.append('l')
    for i in x:
        encode_func[type(i)](i, r)
    r.append('e')

def encode_dict(x,r):
    r.append('d')
    ilist = x.items()
    ilist.sort()
    for k, v in ilist:
        r.extend((str(len(k)), ':', k))
        encode_func[type(v)](v, r)
    r.append('e')

encode_func = {}
encode_func[Bencached] = encode_bencached
encode_func[IntType] = encode_int
encode_func[LongType] = encode_int
encode_func[StringType] = encode_string
encode_func[ListType] = encode_list
encode_func[TupleType] = encode_list
encode_func[DictType] = encode_dict

try:
    from types import BooleanType
    encode_func[BooleanType] = encode_bool
except ImportError:
    pass

def bencode(x):
    r = []
    encode_func[type(x)](x, r)
    return ''.join(r)


class Session:
    """Current cjdns admin session"""

    def __init__(self, socket):
        self.socket = socket
        self.queue = Queue.Queue()
        self.messages = {}

    def disconnect(self):
        self.socket.close()

    def getMessage(self, txid):
        # print self, txid
        return _getMessage(self, txid)

    def functions(self):
        print(self._functions)

def _randomString():
    """Random string for message signing"""

    return ''.join(
        random.choice(string.ascii_uppercase + string.digits)
        for x in range(10))


def _callFunc(session, funcName, password, args):
    """Call custom cjdns admin function"""

    txid = _randomString()
    sock = session.socket
    sock.send('d1:q6:cookie4:txid10:' + txid + 'e')
    msg = _getMessage(session, txid)
    cookie = msg['cookie']
    txid = _randomString()
    req = {
        'q': 'auth',
        'aq': funcName,
        'hash': hashlib.sha256(password + cookie).hexdigest(),
        'cookie': cookie,
        'args': args,
        'txid': txid
    }
    reqBenc = bencode(req)
    req['hash'] = hashlib.sha256(reqBenc).hexdigest()
    reqBenc = bencode(req)
    sock.send(reqBenc)
    return _getMessage(session, txid)


def _receiverThread(session):
    """Receiving messages from cjdns admin server"""

    timeOfLastSend = time.time()
    timeOfLastRecv = time.time()
    try:
        while True:
            if (timeOfLastSend + KEEPALIVE_INTERVAL_SECONDS < time.time()):
                if (timeOfLastRecv + 10 < time.time()):
                    raise Exception("ping timeout")
                session.socket.send(
                    'd1:q18:Admin_asyncEnabled4:txid8:keepalive')
                timeOfLastSend = time.time()

            try:
                data = session.socket.recv(BUFFER_SIZE)
            except (socket.timeout):
                continue

            try:
                benc = bdecode(data)
            except (KeyError, ValueError):
                print("error decoding [" + data + "]")
                continue

            if benc['txid'] == 'keepaliv':
                if benc['asyncEnabled'] == 0:
                    raise Exception("lost session")
                timeOfLastRecv = time.time()
            else:
                # print "putting to queue " + str(benc)
                session.queue.put(benc)

    except KeyboardInterrupt:
        print("interrupted")
        import thread
        thread.interrupt_main()


def _getMessage(session, txid):
    """Getting message associated with txid"""

    while True:
        if txid in session.messages:
            msg = session.messages[txid]
            del session.messages[txid]
            return msg
        else:
            # print "getting from queue"
            try:
                # apparently any timeout at all allows the thread to be
                # stopped but none make it unstoppable with ctrl+c
                nextSession = session.queue.get(timeout=100)
            except Queue.Empty:
                continue
            if 'txid' in nextSession:
                session.messages[nextSession['txid']] = nextSession
                # print "adding message [" + str(nextSession) + "]"
            else:
                print "message with no txid: " + str(nextSession)


def _functionFabric(func_name, argList, oargList, password):
    """Function fabric for Session class"""

    def functionHandler(self, *args, **kwargs):
        call_args = {}

        for (key, value) in oargList.items():
            call_args[key] = value

        for i, arg in enumerate(argList):
            if (i < len(args)):
                call_args[arg] = args[i]

        for (key, value) in kwargs.items():
            call_args[key] = value

        return _callFunc(self, func_name, password, call_args)

    functionHandler.__name__ = func_name
    return functionHandler


def connect(ipAddr, port, password):
    """Connect to cjdns admin with this attributes"""

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect((ipAddr, port))
    sock.settimeout(2)

    # Make sure it pongs.
    sock.send('d1:q4:pinge')
    data = sock.recv(BUFFER_SIZE)
    if (data != 'd1:q4:ponge'):
        raise Exception(
            "Looks like " + ipAddr + ":" + str(port) +
            " is to a non-cjdns socket.")

    # Get the functions and make the object
    page = 0
    availableFunctions = {}
    while True:
        sock.send(
            'd1:q24:Admin_availableFunctions4:argsd4:pagei' +
            str(page) + 'eee')
        data = sock.recv(BUFFER_SIZE)
        benc = bdecode(data)
        for func in benc['availableFunctions']:
            availableFunctions[func] = benc['availableFunctions'][func]
        if (not 'more' in benc):
            break
        page = page+1

    funcArgs = {}
    funcOargs = {}

    for (i, func) in availableFunctions.items():
        items = func.items()

        # grab all the required args first
        # append all the optional args
        rargList = [arg for arg,atts in items if atts['required']]
        argList = rargList + [arg for arg,atts in items if not atts['required']]

        # for each optional arg setup a default value with
        # a type which will be ignored by the core.
        oargList = {}
        for (arg,atts) in items:
            if not atts['required']:
                oargList[arg] = (
                    "''" if (func[arg]['type'] == 'Int')
                    else "0")

        setattr(Session, i, _functionFabric(
            i, argList, oargList, password))

        funcArgs[i] = rargList
        funcOargs[i] = oargList

    session = Session(sock)

    kat = threading.Thread(target=_receiverThread, args=[session])
    kat.setDaemon(True)
    kat.start()

    # Check our password.
    ret = _callFunc(session, "ping", password, {})
    if ('error' in ret):
        raise Exception(
            "Connect failed, incorrect admin password?\n" + str(ret))

    session._functions = ""

    funcOargs_c = {}
    for func in funcOargs:
        funcOargs_c[func] = list(
            [key + "=" + str(value)
                for (key, value) in funcOargs[func].items()])

    for func in availableFunctions:
        session._functions += (
            func + "(" + ', '.join(funcArgs[func] + funcOargs_c[func]) + ")\n")

    # print session.functions
    return session


def connectWithAdminInfo(path = None):
    """Connect to cjdns admin with data from user file"""

    if path is None:
        path = os.getenv("HOME") + '/.cjdnsadmin'
    adminInfo = open(path, 'r')
    data = json.load(adminInfo)
    adminInfo.close()
    return connect(data['addr'], data['port'], data['password'])


print "Checking yo shit for cjdns..."
issues = 0

libraries = "Error"
connection = "Error"
importHelp = ""
try:
    import cjdnsadmin
    libraries = "Success"
    cjdns = cjdnsadmin.connectWithAdminInfo()
    connection = "Success"
except ImportError:
    libraries = "Fail!"
    importHelp = "Try putting contrib/python/cjdnsadmin/cjdnsadmin.py in one of these:\n"
    for path in sys.path:
        if path != "":
            importHelp += " * %s\n" % path
    issues += 1
    try:
        cjdns = connectWithAdminInfo()
        connection = "Success"
    except IOError:
        # No ~/.cjdnsadmin
        connection = "Fail (no ~/.cjdnsadmin)"
except AttributeError:
    try:
        from cjdnsadmin import cjdnsadmin
        cjdns = cjdnsadmin.connectWithAdminInfo()
        libraries = "Got to do from cjdnsadmin import cjdnsadmin :("
        connection = "Success"
        issues += 1
    except:
        libraries = "Failed (AttributeError)"
        issues += 1

except UnboundLocalError:
    connection = "Fail!"
    issues += 1
print "Checking for python libraries... %s" % libraries
print "%sTrying to connect to cjdns... %sv" % (importHelp, connection)

dnslookup = socket.getaddrinfo(clearnetDNShost, 80)
dnsAAAA = "Error"
dnsAccurate = "Error"
if len(dnslookup) == 0:
    dnsAAAA = "Fail!"
    dnsAccurate = "Fail! (no results)"
for record in dnslookup:
    if record[0] != 10:
        dnsAAAA = "Fail"
        issues += 1
    elif dnsAAAA != "Fail":
        dnsAAAA = "Success"

    if record[4][0] != clearnetDNSresult:
        dnsAccurate = "Fail! (inaccurate result)"
    else:
        if not "Fail!" in dnsAccurate:
            dnsAccurate = "Success"

print "Checking for ability to lookup AAAA records.... %s" % dnsAAAA
print "Checking for accurate fc::/8 response.... %s" % dnsAccurate

if "cjdns" in dir():
    peers = []
    more = True
    i = 0
    while more:
        peertable = cjdns.InterfaceController_peerStats(i)
        more = "more" in peertable
        i += 1
        peers += peertable['peers']

    totalPeers = {"UNRESPONSIVE": 0, "total": 0, "ESTABLISHED": 0}
    for peer in peers:
        if not peer['state'] in totalPeers:
            totalPeers[peer['state']] = 0
        totalPeers[peer['state']] += 1
        totalPeers['total'] += 1

    unresponsivePeers = "Error"
    if totalPeers["UNRESPONSIVE"] > 0:
        unresponsivePeers = "Fail (%i unresponsive peers):" % totalPeers['UNRESPONSIVE']
        issues += 1
    else:
        unresponsivePeers = "Success"

    connectedPeers = "Error"
    if totalPeers['ESTABLISHED'] == 0:
        connectedPeers = "Fail"
        issues += 1
    else:
        connectedPeers = "Success (%i established connections)" % totalPeers['ESTABLISHED']

    actuallyHasPeers = "Error"
    if totalPeers['total'] == 0:
        actuallyHasPeers = "Fail"
        issues += 1
    else:
        actuallyHasPeers = "Success"
    print "Checking for peers... %s" % actuallyHasPeers
    print "Checking for unresponsive peers... %s" % unresponsivePeers
    for peer in peers:
        if peer['state'] == "UNRESPONSIVE":
            print "  * %s" % peer['publicKey']
    print "Checking for active peers... %s" % connectedPeers
    print "Displaying peer totals for fun:"
    print totalPeers


print """          ***********************READ THIS*****************************
you were probably asked to run this by someone on IRC. Now they're goig to want
the output. DO NOT paste it straight into IRC. Use a pastebin service. Usually
a service like https://ezcrypt.it is recommended. At some point down the line,
this script will be able to diagnose problems, but not now. Enjoy!
"""

exit(issues)
