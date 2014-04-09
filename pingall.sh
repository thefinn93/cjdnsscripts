#!/bin/bash
while read host; do
    echo -e "$host ... \c"
    ssh -n $host "fping -e $@" | cut -d'(' -f 2 | sed 's/)//'
done < hosts.txt
