# cjdns scripts
This is my collection of scripts for [cjdns](https://github.com/cjdelisle/cjdns).
Some of them have obvious uses, others don't. *Most require `~/.cjdnsadmin`
and the cjdns python libraries to be installed*. I'll try to give a quick
breakdown:

* `addeth.py` scans for all non-virtual ethernet adapters and adds them to the
ETHInterface's config section. Note that at this time having more than one
ETHInterface doesn't seem to actually work (only the first one is used).

* `addpass.py` is my script to easily add authorized passwords to my nodes.
It assumes that the `cjdroute.conf` file is at `/etc/cjdroute.conf` and is valid
JSON, and it assumes there is a `.cjdnsadmin` file in your home directory. The
path to the conf file can be changed on line 88.

* `allnodes.py` prints out every unique IP in the routing table, one per line.
 This is handy for piping to nmap or similar.

* `cjdns-getpass.py` is basically `peerStats` from cjdns's `contrib/python`
folder, but I made it before `peerStats` existed. Basically useless now.

* `installcjdns.sh` was my all-in-one installer script for my own nodes to get
cjdns up and running. May or may not actually work, and I think it relies on
remote content on my server, so maybe don't use it.

* `peercron.py` is/was used by the HIA (Hyperboria Intelligence Agency) to
periodically record information about our peers in order to detect changes.

* `pingall.sh` reads a file called `hosts.txt` and ssh's into all of the hosts
listed in it and pings the IP specified, returning the time it took to ping.
I use this to determine the best node to peer someone with.

* `resolveips.py` appears to do some kind of rDNS-style resolution from a list
of nodes.

* `routingtable.py` appears to print out bits or all of the routing table.

* `threadedVersionCheck.py` is eventually going to be a threaded version of
`peercron.py`
