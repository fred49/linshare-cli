linsharecli
============

Description
-----------

This package contains the [LinShare](http://linshare.org "Open Source secure
files sharing application") command line interface.

This module contains two scripts :

* linsharecli : the user cli.

  You can use this script to upload, download or delete documents stored in
  LinShare. 

* linshareadmcli : the admin cli.

  This script let you configure LinShare server through the command line.
  Domains, ldap connections, functionnalities, and more can be displayed or
  updated through this tool.

Installation
------------

You can install this module using : ``pip install linsharecli``.


QuickStart :
------------

``$ linsharecli.py --user myuser --host https://my.server.com/linshare -P password documents list``

If you want to use a configuration file to preset the server, your login or some
addditional parameters, you can generate the default configuration file like
this :

``$ argtoolboxtool generate  linsharecli``

or for the admin script:

``$ argtoolboxtool generate  linshareadmcli``


The configuration file, by default ~/.linshare-cli.cfg will  contains a section
called "server" :

 [server]

 # Attribute (str) : HOST

 ;host=



Each lines which begins with "#" or ";" are comments.
"str" is the type of data we are expecting, str for string, bool for boolean (true, false) or int for integer.
Every optional attributes, like host, are prefixed by ";".
Mandatory attributes are not prefixed.


