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
import re
import textwrap
import urllib

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
			return 'No stats available.'
		data = '<li>Total storage size: %s</li>\n' % self.formatSize(all.bytes)
		data += '<li>Total entities stored: %s</li>\n' % all.count
		data += '<li>Last statistics update: %s\n' % all.timestamp
		return data

	def cmdConfigvars(self):
		if not web.ctx.env["QUERY_STRING"] in ['cache', 'redirect', 'forward']:
			raise web.BadRequest()
		from lib import cache, redirect, forward
		try:
			service = '%s.Service' % web.ctx.env["QUERY_STRING"]
			d = eval("dir(%s)" % service);
			vars = [x for x in d if not x[0] == '_' and not callable(getattr(eval(service), x))]
			# Force browser cache
			web.header("Cache-Control", "public, max-age=3600");
			web.header("Age", "0");
			return str(vars)
		except Exception:
			raise web.BadRequest()

	def cmdConfighelp(self):
		service = web.ctx.env["QUERY_STRING"].split('_')
		if len(service) != 2:
			raise web.BadRequest()
		var = service[1]
		service = service[0]
		if not service in ['cache', 'redirect', 'forward']:
			raise web.BadRequest()
		from lib import cache, redirect, forward
		data = eval('%s.Service.__doc__' % service)
		e = re.search('- %s: ([^-]+)' % var, data, re.MULTILINE)
		# Force browser cache
		web.header("Cache-Control", "public, max-age=3600");
		web.header("Age", "0");
		if not e:
			return 'No help available'
		doc = textwrap.wrap(e.group(1).strip(), 50)
		return '<br />'.join(doc)

	def cmdConfigsave(self):

		def formatType(var):
			var = var.strip('\'"')
			if var.lower() in ['true', 'false']:
				return var.capitalize()
			if var.find(',') >= 0:
				return '[%s]' % ', '.join(['\'%s\'' % v.strip() for v in var.split(',')])
			if var.find('://') >= 0:
				return '\'%s\'' % var
			return var

		data = urllib.unquote(web.input(_method='post')['configFile'])
		data = eval(data)
		services = data[0]
		urls = data[1]
		ret = 'urls[\'default\'] = (\n'
		for i in range(0, len(urls), 2):
			ret += "\t\t'%s', 'config.%s',\n" % (urls[i], urls[i + 1])
		ret += '\t\t)\n\n'
		for i in range(0, len(services), 3):
			ret += 'class %s(%s.Service):\n' % (services[i], services[i + 1])
			var = services[i + 2]
			for j in range(0, len(var), 2):
				ret += '\t%s = %s\n' % (var[j], formatType(var[j + 1]))
			ret += '\n'
		f = file('config.py')
		ret = f.read(939) + ret
		f.close()
		web.header('Content-Type', 'text/x-python')
		web.header('Content-Disposition', 'attachment; filename=config.py')
		return ret

	def cmdConfigload(self):

		def formatType(var):
			# strip comments
			n = var.find('#')
			if n >= 0:
				var = var[:n]
			return var.strip('\'"[] ')

		data = web.input()['configFile']
		ret = '[[\n'
		e = re.search('urls\[.default.\][^\(]+\(', data)
		end = data.find(')\n', e.end())
		urls = data[e.end():end]
		urls = eval('[%s]' % urls)
		for cls in re.finditer('class\s+(\w+)\((\w+)[^\)]+\):[\r\n]+', data):
			ret += '"%s", "%s",\n[\n' % (cls.group(1), cls.group(2))
			tmp = data[cls.end():]
			for var in re.finditer('([\S]+)\s*=\s*([^\r\n]+)[\r\n]?', tmp):
				ret += '"%s", "%s",\n' % (var.group(1), formatType(var.group(2)))
				if re.match('^[\r\n]+', tmp[var.end():]):
					# We are at the end of the class
					break
			ret += '],\n'
		ret += '],\n%s]' % str(urls).replace('config.', '')
		return ret
