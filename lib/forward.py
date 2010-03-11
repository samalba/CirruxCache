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

from google.appengine.api import urlfetch, urlfetch_errors

class Service(http.Base):

	"""Forward service

	All requests handled by this service will be forwarded
	to the origin.

	- origin: Set the origin url
	"""

	origin = None

	def __getattribute__(self, attr):
		# "this" points to the child class
		# without calling "__getattribute__"
		this = type(self)
		def _impl(request):
			request += web.ctx.query
			response = forwardRequest(this.origin + request, method=web.ctx.method)
			forwardResponse(response)
		return _impl

def forwardResponse(response):
	status = '%s %s' % (response.status_code, http.httpResponses[response.status_code])
	raise web.HTTPError(status=status, headers=response.headers, data=response.content)

def forwardRequest(url, method='GET'):
	headers = {}
	for key, value in web.ctx.environ.iteritems():
		if not key.startswith('HTTP_'):
			continue
		key = '-'.join([k.capitalize() for k in key[5:].split('_')])
		headers[key] = value
	#headers['Host'] = self.origin[7:]
	headers['User-Agent'] = http.userAgent
	try:
		return urlfetch.Fetch(url=url, method=method, headers=headers)
	except urlfetch_errors.Error:
		# We got an error, redirect to the origin
		# to let client dealing errors with it.
		raise web.SeeOther(url)
