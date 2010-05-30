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
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import db


class _Store(db.Model):
	blobKey = db.StringProperty()

class Store(object):

	def GET(self, request):
		req = web.ctx.path.split('/')
		cmd = 'cmd' + req.pop().capitalize()
		if hasattr(self, cmd):
			attr = getattr(self, cmd)
			if callable(attr):
				return attr('/'.join(req))
		return self.serve(web.ctx.path)

	def POST(self, request):
		data = web.data()
		s = data.find('blob-key=') + 10
		bkey = data[s: data.find('"', s)]
		logging.warning('--%s--' % web.data())
		logging.warning('--%s--' % bkey)
		raise web.SeeOther(request)

	def serve(self, request):
		logging.warning('--%s--' % blobstore.BlobInfo.get(request.split('/').pop()))
		return 'OK'

	def cmdNew(self, request):
		url = blobstore.create_upload_url(request).split('/')[3:]
		url = '/' + '/'.join(url)
		return '%s' % url
