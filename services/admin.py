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

import logging

import web
from google.appengine.api import users
from google.appengine.ext import blobstore
from google.appengine.ext.db import stats

from services.store import _StoreMeta

class Admin(object):

	def POST(self, request):
		return self.__request(request)

	def GET(self, request):
		return self.__request(request)

	def __request(self, request):
		if not users.is_current_user_admin():
			raise web.SeeOther(users.create_login_url(web.ctx.path))
		if not request:
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

	def formatSize(self, size):
		suffixes = ['Bytes', 'KBytes', 'MBytes', 'GBytes']
		for s in suffixes:
			if size < 1024:
				return '%s %s' % (size, s)
			size /= 1024

	def cmdStore(self):
		data = ''
		for meta in _StoreMeta.all():
			name = meta.key().name()
			info = blobstore.BlobInfo.get(meta.blobKey)
			size = self.formatSize(info.size)
			data += '<li><input type="button" value="x" onclick="javascript:delStore(\'%s\');" />%s' % (name, name)
			data += ' <span>(%s, %s, %s)</span></li>\n' % (info.filename, info.content_type, size)
		return data

	def cmdStats(self):
		all = stats.GlobalStat.all().get()
		if not all:
			return ''
		data = '<li>Total storage size: %s</li>\n' % self.formatSize(all.bytes)
		data += '<li>Total entities stored: %s</li>\n' % all.count
		data += '<li>Last statistics update: %s\n' % all.timestamp
		return data
