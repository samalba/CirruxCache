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

import sys, os
root = os.path.dirname(os.environ['PATH_TRANSLATED'])
sys.path.append(os.path.join(root, 'lib'))
sys.path.append(os.path.join(root, 'contrib'))

import logging
import web

import config
from services.cron import Cron
from services.admin import Admin
from services.store import Store
from services.debug import Debug


class Root(object):

	def GET(self, request):
		web.header('Content-Type', 'text/plain')
		content = 'CirruxCache (%s) / http://code.google.com/p/cirruxcache/\n' % __version__
		if request:
			raise web.HTTPError(status='404 Not Found', data=content)
		return content

class VhostMapper(object):

	def __iter__(self):
		base = (
				'/_admin/(.*)', 'Admin',
				'/_store/(.*)', 'Store',
				'/_cron/(.*)', 'Cron'
				)
		url = ()
		urls = config.urls
		if 'HTTP_HOST' in web.ctx.environ:
			vhost = web.ctx.environ['HTTP_HOST']
			if vhost in urls:
				url = urls[vhost]
			elif 'default' in urls:
				url = urls['default']
		return iter(base + url + ('/(.*)', 'Root'))

if __name__ == '__main__':
#	logging.getLogger().setLevel(logging.DEBUG)
	app = web.application(VhostMapper(), globals())
	app.cgirun()
