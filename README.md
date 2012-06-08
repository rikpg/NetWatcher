=================
Deluge NetWatcher
=================

_NetWatcher_ is a plugin for the [Deluge bittorrent client](http://deluge-torrent.org/) that checks a bunch of ip-addresses to decide if all torrents are to be paused/resumed.


What it does
------------

__Ip Addresses__ is a list of comma separated ip addresses. These addresses are going to be cheked every x minutes.

The rationale is:

- At least one ip address is on-line -> pause all
- All the ip-addresses are off-line -> resume all

Note: the ip-addresses status is checked through ping request.


Building the plugin
-------------------

As explained in the [official doc](http://dev.deluge-torrent.org/wiki/Development/1.3/Plugin#BuildingThePlugin):

    $ python setup.py bdist_egg


Install the plugin
------------------

Deluge Edit > Preferences > Plugins > Click 'Install Plugin' and choose the NetWatcher egg.
