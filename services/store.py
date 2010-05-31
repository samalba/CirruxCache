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
from google.appengine.api import users


class _StoreMeta(db.Model):
	blobKey = db.StringProperty()

class Store(object):

	# This IP list is authorized to upload and remove files
	allowFrom = ['127.0.0.1']

	def GET(self, request):
		req = web.ctx.path.split('/')
		cmd = 'cmd' + req.pop().capitalize()
		if hasattr(self, cmd):
			attr = getattr(self, cmd)
			if callable(attr):
				return attr('/'.join(req))
		return self.serve(web.ctx.path)

	def DELETE(self, request):
		return self.cmdDelete(request)

	def POST(self, request):
		request = web.ctx.path
		data = web.data()
		s = data.find('blob-key=')
		if s < 0:
			raise web.BadRequest()
		s += 10
		e = data.find('"', s)
		if e < 0:
			raise web.BadRequest()
		data = data[s:e]
		if not data:
			raise web.BadRequest()
		if not blobstore.BlobInfo.get(data):
			# The blobKey does not exist
			raise web.NotFound()
		meta = _StoreMeta.get_by_key_name(request)
		if meta:
			# Delete the existing blob
			blobstore.delete(meta.blobKey)
		meta = _StoreMeta(key_name=request)
		meta.blobKey = data
		logging.warning('BlobKey: %s' % meta.blobKey)
		meta.put()
		# This redirection is empty and useless,
		# required from the appengine SDK...
		raise web.HTTPError(status='302 Found')

	def serve(self, request):
		meta = _StoreMeta.get_by_key_name(request)
		if not meta:
			raise web.NotFound()
		print 'X-AppEngine-BlobKey: %s' % meta.blobKey

	def checkAuth(self):
		if not web.ctx.env['REMOTE_ADDR'] in self.allowFrom and not users.is_current_user_admin():
			raise web.Forbidden()

	def cmdNew(self, request):
		self.checkAuth()
		url = blobstore.create_upload_url(request).split('/')[3:]
		url = '/' + '/'.join(url)
		return '%s' % url

	def cmdDelete(self, request):
		self.checkAuth()
		meta = _StoreMeta.get_by_key_name(request)
		if not meta:
			raise web.NotFound()
		meta.delete()
		blobstore.delete(meta.blobKey)
		return 'OK'
