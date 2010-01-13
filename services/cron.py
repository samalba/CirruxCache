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
import datetime
import web

from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.ext.db import stats

import lib.cache

class Cron(object):

	def GET(self, request):
		if not 'HTTP_X_APPENGINE_CRON' in web.ctx.environ:
			return ''
		request = request.lower()
		if not hasattr(self, request):
			return ''
		attr = getattr(self, request)
		if callable(attr):
			attr()
		return ''

	def expired(self):
		"""clear old cache entries"""
		# Allow an offset of 1 hour to flush cache entries.
		now = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
		# entity selection is limited by 1000 but often timeout
		limit = 800
		batch = []
		# Browse all Datastore kinds to find expired entities
		for kind in stats.KindStat.all():
			if kind.kind_name.startswith('__'):
				continue
			cache = type(str(kind.kind_name), (lib.cache.Cache,), {})
			for obj in cache.all(keys_only=True) \
					.filter('expires <=', now) \
					.order('expires').fetch(limit):
						batch.append(obj)
		n = len(batch)
		if n == 0:
			logging.info('cron: no expired entities.')
			return
		# batch deletion is limited by 500 but it timeouts above ~200
		step = 200
		if step > n:
			step = n
		for i in range(0, limit, step):
			db.delete(batch[i:i+step])
		logging.info('cron: %s expired entities flushed.' % n)
