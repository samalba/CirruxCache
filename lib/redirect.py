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

import web
import http

class Service(http.Base):

	"""Redirect service

	All requests handled by this service will be redirected
	to the origin.

	- origin: Set the origin url
	- code: Set the redirection code (default: 301)
	"""

	origin = None
	code = 301

	def __getattribute__(self, attr):
		# "this" points to the child class
		# without calling "__getattribute__"
		this = type(self)
		def _impl(request):
			request += web.ctx.query
			web.header('Location', this.origin + request)
			status = '%s %s' % (this.code, http.httpResponses[this.code])
			raise web.HTTPError(status=status)
		return _impl
