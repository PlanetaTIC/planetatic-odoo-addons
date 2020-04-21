#!/bin/bash

# $1: Fedicom Port
# $2: odoo's URL
# $3: database name
# $4: Odoo's username
# $5: Odoo's password

echo $#
if [ $# -ne "5" ]
    then
        echo "First parameter Fedicom server port, second parameter odoo's URL, third dbname, forth Odoo username, fifth Odoo password"
else
    echo 'Port: ' $1
    echo 'Odoo URL: ' $2
    echo 'Odoo DB name: ' $3
    echo 'Odoo username: ' $4
    echo 'Odoo password: ' $5
    pkill -9 -f fedicom_service.py
    python fedicom_service.py $1 $2 $3 $4 $5
fi
