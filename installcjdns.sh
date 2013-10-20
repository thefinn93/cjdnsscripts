#!/bin/bash

if [ `whoami` != "root" ]; then
    echo "Requires root!"
    exit 1
fi

apt-get install git build-essential cmake

cd /opt
git clone https://github.com/cjdelisle/cjdns
cd cjdns
./do
./cjdroute --genconf | ./cjdroute --cleanconf < /dev/stdin > /etc/cjdroute.conf
cp scripts/cjdns.sh /etc/init.d/cjdns
sed -i 's/ &>> $LOGTO//'  /etc/init.d/cjdns
sed -i 's/ || echo "Failed to update!" && exit 1//' /etc/init.d/cjdns

cat > /etc/default/cjdns <<EOL
CJDPATH=/opt
CONF=/etc/cjdroute.conf
EOL

cat > /opt/updategit.sh <<EOL
#!/bin/bash
TOKEN=
cd \$1
branch=\$(git describe --contains --all HEAD)
if [ "\$(git ls-remote origin -h refs/heads/$branch | cut -c1-40)" != "$(cat .git/refs/heads/$branch)" ];
then
    BASENAME=\$(basename \$1)
    HOSTNAME=\$(hostname)
    git pull
    curl "https://www.thefinn93.com/push/send?token=\$TOKEN&title=Updated%20\$BASENAME%20on%20\$HOSTNAME&message=Updated%20\$BASENAME%20on%20\$HOSTNAME%20to%20\$(cat .git/refs/heads/\$branch)"
    if [ -x "./update" ]; then
        ./update
    fi
fi
EOL
chmod +x /opt/updategit.sh

sudo update-rc.d cjdns defaults

cat > /opt/cjdns/update << EOL
#!/bin/bash
/etc/init.d/cjdns update
EOL

chmod +x /opt/cjdns/update

crontab -l > /tmp/currentcron
echo "0 * * * * /opt/updategit.sh /opt/cjdns" >> /tmp/currentcron
crontab /tmp/currentcron
rm /tmp/currentcron
