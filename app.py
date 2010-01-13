#!/usr/bin/env python
# CirruxCache provides dynamic HTTP caching on AppEngine (CDN like)
# Copyright (C) 2009 Samuel Alba <sam.alba@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

"""CirruxCache provides dynamic HTTP caching on AppEngine (CDN like)

http://cirrux.org/cache/
http://code.google.com/p/cirruxcache/
"""

__version__ = 'trunk'
__author__ = [
    'Samuel Alba <sam.alba@gmail.com>'
]
__license__ = 'GNU Public License version 2'

import sys
sys.path.append('contrib')

import logging
import web

from services.cron import Cron
from services.debug import Debug
from lib.cache import *

# URL mapping
urls = (
#		'(/debug/.*)', 'Debug',
		'(/data/.*)', 'Static',
		'/www(/.*)', 'Www',
		'/_cron/(.*)', 'Cron',
		'(/.*)', 'Root'
		)

# POP definition
# You can define and configure your Point Of Presence

class Static(Service):
	origin = 'http://static.mydomain.tld'
	maxTTL = 2592000 # 1 month
	ignoreQueryString = True

class Www(Service):
	origin = 'http://www.mydomain.tld'
	forceTTL = 3600 # 1 hour
	ignoreQueryString = True
	forwardPost = False

# !POP

# Dynamic configuration
# disabled for performance issue
#def initServices(urls):
#	cfg = config.Config()
#	for service, meta in cfg.all():
#		if service[0] != '_':
#			continue
#		globals()[service] = type(service, (Service,), meta)
#		urls = ('(%s/.*)' % meta['mount'], service) + urls
#	return urls

class Root(object):
	def GET(self, request):
		return 'CirruxCache %s / shad ; written by Samuel Alba <sam.alba@gmail.com> / http://shad.cc/' % __version__

if __name__ == '__main__':
#	urls = initServices(urls)
#	debug = ('SERVER_SOFTWARE' in os.environ and os.environ['SERVER_SOFTWARE'] == 'Development/1.0')
#	if debug:
#	from services.debug import Debug
#	urls = ('(/debug/.*)', 'Debug') + urls
#	logging.getLogger().setLevel(logging.DEBUG)
	app = web.application(urls, globals())
	app.cgirun()
