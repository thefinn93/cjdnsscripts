#!/usr/bin/env python

__author__ = "Finn Herzfeld"
__copyright__ = "Copyright 2014, Finn Herzfeld"
__credits__ = ["Finn Herzfeld"]
__license__ = "GPL"
__version__ = "0.5"
__maintainer__ = "Finn Herzfeld"
__email__ = "finn@seattlemesh.net"
__status__ = "Development"

# You may redistribute this program and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

## cjdns credential maker
## Because the go one and the node one are sucky
##
## No offense
import sys, json, os, urllib2, random
from hashlib import sha512
try:
    import cjdnsadmin
except:
    #print "Failed to find cjdnsadmin in the normal search path. Hax in progress..."
    sys.path.append("/opt/cjdns/contrib/python/cjdnsadmin")
    try:
        import cjdnsadmin
        #print "(hax succeeded)"
    except:
        print "Failed to import cjdnsadmin!"
        sys.exit(1)
cjdns = cjdnsadmin.connectWithAdminInfo()

## Stolen from contrib/python/cjdnsadmin/publicToIp6.py ##

# see util/Base32.h
def Base32_decode(input):
    output = bytearray(len(input));
    numForAscii = [
        99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,
        99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,
        99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,
         0, 1, 2, 3, 4, 5, 6, 7, 8, 9,99,99,99,99,99,99,
        99,99,10,11,12,99,13,14,15,99,16,17,18,19,20,99,
        21,22,23,24,25,26,27,28,29,30,31,99,99,99,99,99,
        99,99,10,11,12,99,13,14,15,99,16,17,18,19,20,99,
        21,22,23,24,25,26,27,28,29,30,31,99,99,99,99,99,
    ];

    outputIndex = 0;
    inputIndex = 0;
    nextByte = 0;
    bits = 0;

    while (inputIndex < len(input)):
        o = ord(input[inputIndex]);
        if (o & 0x80): raise ValueError;
        b = numForAscii[o];
        inputIndex += 1;
        if (b > 31): raise ValueError("bad character " + input[inputIndex]);

        nextByte |= (b << bits);
        bits += 5;

        if (bits >= 8):
            output[outputIndex] = nextByte & 0xff;
            outputIndex += 1;
            bits -= 8;
            nextByte >>= 8;

    if (bits >= 5 or nextByte):
        raise ValueError("bits is " + str(bits) + " and nextByte is " + str(nextByte));

    return buffer(output, 0, outputIndex);


def PublicToIp6_convert(pubKey):
    if (pubKey[-2:] != ".k"): raise ValueError("key does not end with .k");
    keyBytes = Base32_decode(pubKey[0:-2]);
    hashOne = sha512(keyBytes).digest();
    hashTwo = sha512(hashOne).hexdigest();
    first16 = hashTwo[0:32];
    out = '';
    for i in range(0,8): out += first16[i*4 : i*4+4] + ":";
    return out[:-1];


## /theft ##


configfile = "/etc/cjdroute.conf"
try:
	config = json.load(open(configfile))
except IOError:
	cjdnsadmin = json.load(open(os.getenv("HOME") + "/.cjdnsadmin"))
	configfile = cjdnsadmin['config']
	config = json.load(open(configfile))
#except all the things

if not "infotohandout" in config:
	print "Welcome to the first run of this crap"
	print "This is the info you'll be handing out to people"
	config['infotohandout'] = {}
	publicip = urllib2.urlopen("http://icanhazip.com").read().replace("\n", "")
	if type(config['interfaces']['UDPInterface']) == type([]):
		publicip = config['interfaces']['UDPInterface'][0]['bind'].replace("0.0.0.0", publicip)
	else:
		publicip = config['interfaces']['UDPInterface']['bind'].replace("0.0.0.0", publicip)
	customip = raw_input("IP:port [%s]" % publicip)
	if customip != "":
		publicip = customip
	config['infotohandout'][publicip] = {}
	done = False
	while not done:
		print "Adding arbitrary key/value pair"
		key = raw_input("Key: ")
		value = raw_input("Value: ")
		add = raw_input("Really add? [Y/n]: ")
		if add == "Y" or add == "y" or add == "":
			config['infotohandout'][publicip][key] = value
		more = raw_input("Add another? [Y/n]: ")
		if more == "n" or more == "N":
			done = True


creds = {}
creds['user'] = raw_input("User: ")
creds['email'] = raw_input("email: ")
creds['pubkey'] = raw_input("Public Key: ")
if creds['pubkey'] == "":
	creds['cjdnsip'] = raw_input("cjdns ip: ")
else:
	creds['cjdnsip'] = PublicToIp6_convert(creds['pubkey'])
creds['location'] = raw_input("Location: ")
creds['clearnetip'] = raw_input("Clearnet IP: ")
creds['password'] = raw_input("Password (leave blank to generate): ")
if creds['password'] == "":
	alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
	for i in range(0,50):	# TODO: Make this number configurable
		creds['password'] += random.choice(alphabet)
	print "Password: %s" % creds['password']

config['authorizedPasswords'].append(creds)

save = open(configfile, "w")
# TODO: This should also be configurable
save.write(json.dumps(config, sort_keys=True, indent=4, separators=(',', ': ')))
save.close()

print "Adding creds to current cjdns instance: "
result = cjdns.AuthorizedPasswords_add(creds['password'], creds['user'])
if "error" in result:
	if result['error'] != 'none':
		print "Failed to add it to the current cjdns instance. Fuck it"
                import code; code.interact(local=locals())
	print result
for ip in config['infotohandout'].keys():
	config['infotohandout'][ip]['password'] = creds['password']
	config['infotohandout'][ip]['publicKey'] = config['publicKey']

print json.dumps(config['infotohandout'], sort_keys=True, indent=4, separators=(',', ': '))
