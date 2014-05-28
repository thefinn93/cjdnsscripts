#!/usr/bin/env python2

import os
import sys

print "Checking yo shit for cjdns..."
issues = 0

libraries = "Error"
connection = "Error"
try:
    import cjdnsadmin
    libraries = "Success"
    cjdns = cjdnsadmin.connectWithAdminInfo()
    connection = "Success"
except ImportError:
    libraries = "Fail!"
    issues += 1
except UnboundLocalError:
    connection = "Fail!"
    issues += 1
print "Checking for python libraries... %s" % libraries
print "Trying to connect to cjdns... %s" % connection

exit(issues)
