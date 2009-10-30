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

import pprint

import web

class Debug(object):

	def GET(self, request):
		pp = pprint.PrettyPrinter(indent=4)
		yield 'Request: %s\n' % request
		yield 'Globals: %s\n' % pp.pformat(globals())
		yield 'web.ctx: %s\n' % pp.pformat(dict(web.ctx))
		headers = {}
		for key, value in web.ctx.environ.iteritems():
			if not key.startswith('HTTP_'):
				continue
			key = '-'.join([k.capitalize() for k in key[5:].split('_')])
			headers[key] = value
		headers['Host'] = origin[7:]
		headers['User-Agent'] = 'CirruxCache 0.1 / shad ;'
		yield 'headers: %s' % pp.pformat(headers)
