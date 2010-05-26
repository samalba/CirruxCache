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

from google.appengine.api import users
import web

class Admin(object):

	def POST(self, request):
		return self.__request(request)

	def GET(self, request):
		return self.__request(request)

	def __request(self, request):
		if not users.is_current_user_admin():
			raise web.SeeOther(users.create_login_url(web.ctx.path))
		if not request:
			#return web.template.render('static/templates').admin()
			try:
				f = file('static/admin.html')
				return f.read()
			finally:
				f.close()
		func = 'cmd' + request.capitalize()
		if hasattr(self, func):
			attr = getattr(self, func)
			if callable(attr):
				return attr()
		raise web.NotFound()

	def cmdFlush(self):
		cache = lib.cache.Service()
		input = web.data().split('\n')
		n = 0
		for ln in input:
			ln = ln.strip()
			if not ln:
				continue
			n += 1
		return '%s object%s flushed' % (n, (n > 1 and 's' or ''))
