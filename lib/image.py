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
from google.appengine.api import images
from google.appengine.ext import db

from lib import cache

class _StoreMeta(db.Model):
	blobKey = db.StringProperty()

class Service(cache.Service):

	def __init__(self):
		self.ignoreQueryString = False
		self.stripForwardedQueryString = True
		cache.Service.__init__(self)

	def GET(self, request):
		args = self.parseArguments()
		if self.origin == 'store://':
			meta = _StoreMeta.get_by_key_name(request)
			if not meta:
				raise web.NotFound()
			if not args:
				web.header('X-AppEngine-BlobKey', meta.blobKey)
				return
			img = images.Image(blob_key=meta.blobKey)
			web.header('Content-Type', 'image/jpeg')
			return self.transform(img, args)

		def transformCache(cache):
			img = images.Image(image_data=cache)
			return self.transform(img, args)

		if not args:
			return cache.Service.GET(self, request)
		return cache.Service.GET(self, request, _beforeWriteCache=transformCache)

	def parseArguments(self):
		args = web.input(_method='get')
		filter = ['width', 'height', 'rotate', 'horizontal_flip',\
				'vertical_flip', 'crop', 'enhance']
		l = list(args)
		l.sort()
		# Rewrite query string sorted to keep the same cache key
		query = []
		for k in l:
			if not k in filter:
				continue
			v = args[k]
			if not v:
				query.append(k)
			else:
				query.append('%s=%s' % (k, v))
		if not query:
			web.ctx.query = u''
		else:
			web.ctx.query = '?' + '&'.join(query)
		return args

	def transform(self, img, args):
		try:
			width = 0
			height = 0
			if 'width' in args:
				width = int(args['width'])
			if 'height' in args:
				height = int(args['height'])
			if width > 0 or height > 0:
				img.resize(width=width, height=height)
			if 'rotate' in args:
				img.rotate(int(args['rotate']))
			if 'horizontal_flip' in args:
				img.horizontal_flip()
			if 'vertical_flip' in args:
				img.vertical_flip()
			if 'crop' in args:
				crop = [float(x) for x in args['crop'].split('-')]
				img.crop(crop[0], crop[1], crop[2], crop[3])
			if 'enhance' in args:
				img.im_feeling_lucky()
			return img.execute_transforms(output_encoding=images.JPEG)
		except Exception:
			raise web.badrequest()
