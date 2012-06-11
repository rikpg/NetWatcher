=================
Deluge NetWatcher
=================

_NetWatcher_ is a plugin for the [Deluge bittorrent client](http://deluge-torrent.org/) that checks a bunch of ip-addresses to decide if all torrents are to be paused/resumed.


What it does
------------

The __Ip Addresses__ setting is a list of comma separated ip addresses. These addresses are going to be cheked every X minutes.

The rationale is:

- At least one ip address is on-line -> pause all
- All the ip-addresses are off-line -> resume all

Note: the ip-addresses status is checked through ping request.


Install the plugin
------------------

There are various ways to do it.

1. Build the egg and copy it in the deluge _plugins_ directory:

        $ python setup.py bdist_egg
        $ cp dist/*.egg ~/.config/deluge/plugins

2. Or if you are a developer, since it is inconvenient to have to install it in the way described above, you could use the setuptools develop command:

        $ python setup.py develop -mxd ~/.config/deluge/plugins
