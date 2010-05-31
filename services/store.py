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


class _StoreMeta(db.Model):
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
		request = web.ctx.path
		data = web.data()
		s = data.find('blob-key=') + 10
		meta = _StoreMeta.get_by_key_name(request)
		if meta:
			# Delete the existing blob
			blobstore.delete(meta.blobKey)
		meta = _StoreMeta(key_name=request)
		meta.blobKey = data[s: data.find('"', s)]
		logging.warning('BlobKey = %s' % meta.blobKey)
		meta.put()
		# This redirection is empty and useless,
		# required from the appengine SDK...
		raise web.HTTPError(status='302 Found')

	def serve(self, request):
		meta = _StoreMeta.get_by_key_name(request)
		if not meta:
			raise web.NotFound()
		print 'X-AppEngine-BlobKey: %s' % meta.blobKey

	def cmdNew(self, request):
		url = blobstore.create_upload_url(request).split('/')[3:]
		url = '/' + '/'.join(url)
		return '%s' % url
