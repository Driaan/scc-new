scc-new
scc-1.26.73
scc-srv-1.19.44

# SCC (SysConfCollect)

The source code for SCC (SysConfCollect) on both server and client environments.

## Compilation & Installation

To manually compile (tested on debian) execute the following scripts:

```shell script
# as non-root user:

git clone https://github.com/driaan/scc-new
chmod -R +x scc-new/ # otherwise permission errors after packaging

# scc
cd scc
./debian-gen-scc
sudo dpkg -i scc_1.26.73-1_all.deb

# scc-srv
sudo apt install scc-srv
cd scc
./debian-gen-scc-srv
sudo dpkg -i scc-srv_1.19.44-1_all.deb
/opt/scc-srv/bin/scc-srv-set
/opt/scc-srv/bin/scc-setup --activate # to start apache2 server
```

# Rsync Setup

1. create file ```/var/opt/scc-srv/conf/scc-hosts```

    ```shell script
    scc-srv 123qwe
    tros01-gra2 123qwe
    tros01-rbx7 123qwe
    tros01-sbg3 123qwe
    tros02-gra2 123qwe
    trosdata01-rbx7 123qwe
    trosdata02-rbx8 123qwe
    ```
2. 



# Usage

### Updating scc

```shell script
/opt/scc-srv/bin/scc-update -f
```

### Adding a new realm

```shell script
/opt/scc-srv/bin/scc-realm -a $REALM_NAME
```

### Deleting a realm

```shell script
/opt/scc-srv/bin/scc-realm -d $REALM_NAME
```

### Adding hosts to realm

```shell script
scc-realm --add --quick --list $HOST_1 $REALM_NAME # do not call scc-update, manually call /opt/scc-srv/bin/scc-update -f
scc-realm --add --list $HOST_1,$HOST_2 $REALM_NAME
```

### Renaming a realm

```shell script
/opt/scc-srv/bin/scc-update -r $OLD_REALM_NAME $NEW_REALM_NAME
```

### Archiving hosts

```shell script
/opt/scc-srv/bin/scc-realm --archive /<dir>/archive --list $HOST_1,$HOST_2 --delete All
```

# Security

## Adding user:password to realm via .htpasswd

You can generate a password hash using https://hostingcanada.org/htpasswd-generator/

```shell script
# user1:123qwe
# user2:123qwe

sudo tee -a /var/opt/scc-srv/data/www/.htpasswd > /dev/null <<EOT
user1:{SHA}Bf50YcYHwzIpdy1AJQVgEBan0Oo=
user2:{SHA}Bf50YcYHwzIpdy1AJQVgEBan0Oo=
EOT
```

## Adding folder protection via .htaccess

```shell script
sudo tee -a /var/opt/scc-srv/data/www/$REALM_NAME/.htaccess > /dev/null <<EOT
AuthName "Access Control"
AuthType Basic
AuthUserFile /var/opt/scc-srv/data/www/.htpasswd
AuthGroupFile /var/opt/scc-srv/data/www/.htgroups
Require group admin
Require group $REALM_GROUP
EOT
```

Note: allowing users without needing groups: "Require valid-user"

## Adding group protection via .htgroups

Activating apache2 authz_groupfile

```shell script
a2enmod authz_groupfile
systemctl restart apache2
```

### Groups File:

```shell script
# /var/opt/scc-srv/data/www/.htgroups

$GROUP_NAME: $GROUP_USER_1 $GROUP_USER_2 $GROUP_USER_3

example:
admin: user1 user2
paythem: user_1 user_2
```
