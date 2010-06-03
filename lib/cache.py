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
import time
import datetime

import web
from google.appengine import runtime
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.api import users

import http
from lib import forward

class Cache(db.Model):
	headers = db.ListProperty(str)
	lastRefresh = db.DateTimeProperty()
	lastModified = db.DateTimeProperty()
	expires = db.DateTimeProperty()
	maxAge = db.IntegerProperty()
	data = db.BlobProperty(default=None)

class CacheExpired(Exception):

	def __init__(self, cacheObject):
		self.__cache = cacheObject

	def __call__(self):
		return self.__cache

class Service(object):

	"""Cache service

	This service implements the content delivering caching mechanism.
	All requests handled by this service produces cache manipulation
	on the Google Datastore (with a Memcache top layer).

	- origin: Set the origin url
	- forceTTL: Does not honor Cache-Control value, replacing cache TTL by this value
	- maxTTL: When the Cache-Control value is honored (forceTTL not set), the cache TTL
	value cannot be greater than this value (otherwise, it is overriden).
	- ignoreQueryString: Tell if the trailing HTTP query string is not taken into account
	to generate the cache object key in Datastore. In other terms, if this value is set
	to True, /url/path/obj.js?v=42 and /url/path/obj.js referer to the same object.
	- forwardPost: If it is True, POST requests will be forwarded, instead of being redirected
	- allowFlushFrom: Specify client IP which are allowed to make DELETE requests to flush
	cache object explicitly.
	"""

	origin = None
	forceTTL = None
	maxTTL = None
	ignoreQueryString = False
	forwardPost = True
	# Set your client IP address to authorize cache entry deletion
	allowFlushFrom = ['127.0.0.1']

	# These headers won't be forwarded
	headerBlacklist = [
			'date',
			'last-modified',
			'via',
			'expires'
			]

	def __init__(self):
		self.name = self.__class__.__name__
		self.cache = type(self.name, (Cache,), {})
		# Register the dynamic object globally
		# if not, pickle cannot find it for serialization
		globals()[self.name] = self.cache

	def GET(self, request):
		if self.ignoreQueryString is False:
			request += web.ctx.query
		try:
			cache = self.readCache(request)
			if cache is None:
				cache = self.writeCache(request)
		except runtime.DeadlineExceededError:
			raise web.SeeOther(self.origin + request, absolute=True)
		except CacheExpired, cache:
			cache = self.writeCache(request, cache())
		if not web.modified(cache.lastModified):
			raise web.HTTPError(status='304 Not Modified')
		web.header('Expires', web.httpdate(cache.expires))
		for h in cache.headers:
			print h
		return cache.data

	def POST(self, request):
		if self.ignoreQueryString is False:
			request += web.ctx.query
		url = self.origin + request
		if self.forwardPost is False:
			raise web.SeeOther(url, absolute=True)
		response = forward.forwardRequest(url, method=web.ctx.method)
		forward.forwardResponse(response)

	def PUT(self, request):
		self.POST(request)

	def DELETE(self, request):
		if not web.ctx.env['REMOTE_ADDR'] in self.allowFlushFrom and not users.is_current_user_admin():
			raise web.Forbidden()
		if request.split('/').pop() == '__ALL__':
			if 'memcache' in web.ctx.query:
				memcache.flush_all()
				return 'memcache flushed.\n'
			# entity selection is limited by 1000 but often timeout
			limit = 800
			batch = []
			for entity in Cache.all(keys_only=True).order('-expires').fetch(limit):
				batch.append(entity)
			n = len(batch)
			if n == 0:
				return 'No entries.\n'
			# batch deletion is limited by 500 but it timeouts above ~200
			step = 200
			if step > n:
				step = n
			for i in range(0, limit, step):
				db.delete(batch[i:i+step])
			return '%s entries flushed\n' % n
		if self.ignoreQueryString is False:
			request += web.ctx.query
		cache = self.cache.get_by_key_name(request)
		if cache:
			cache.delete()
		memcache.delete(request)
		return 'ok\n'

	def memcacheSet(self, *args, **kwargs):
		try:
			if 'key' in kwargs:
				kwargs['key'] = '%s_%s' % (self.name, kwargs['key'])
			if 'time' in kwargs and isinstance(kwargs['time'], datetime.datetime):
				kwargs['time'] = time.mktime(kwargs['time'].timetuple())
			memcache.set(*args, **kwargs)
		except Exception, e:
			logging.warning('memcacheSet(): Error (%s: %s)' % (type(e), e))

	def memcacheGet(self, *args, **kwargs):
		try:
			args = ('%s_%s' % (self.name, args[0]), )
			cache = memcache.get(*args, **kwargs)
			return cache
		except Exception, e:
			logging.warning('memcacheGet(): Error (%s: %s)' % (type(e), e))

	def readCache(self, key):
		logging.debug('readCache')
		cache = self.memcacheGet(key)
		if cache:
			logging.debug('found in memcache')
			return cache
		try:
			logging.debug('fetch from datastore')
			cache = self.cache.get_by_key_name(key)
		except Exception, e:
			logging.warning('datastore fetch error (%s: %s)' % (type(e), e))
		if not cache:
			logging.debug('cache entry not found')
			return
		now = datetime.datetime.utcnow()
		if now >= cache.expires:
			logging.debug('cache entry expired')
			raise CacheExpired(cache)
		self.memcacheSet(key=key, value=cache, time=cache.expires)
		return cache

	def writeCache(self, request, cache = None):
		logging.debug('writeCache')
		url = self.origin + request
		headers = {'User-Agent' : http.userAgent}
		# Bypass google cache
		headers['Cache-Control'] = 'no-cache, max-age=0, must-revalidate'
		if cache:
			headers['If-Modified-Since'] = web.httpdate(cache.lastModified)
		try:
			response = urlfetch.Fetch(url=url, headers=headers)
		except Exception, e:
			if cache:
				return cache
			logging.warning('urlfetch error, redirect to origin. (%s: %s)' % (type(e), e))
			raise web.SeeOther(url, absolute=True)
		if response.status_code == 304:
			logging.debug('304, update cache meta')
			cache.lastRefresh = datetime.datetime.utcnow()
			cache.expires = cache.lastRefresh + datetime.timedelta(seconds=cache.maxAge)
			cache.put()
			self.memcacheSet(key=request, value=cache, time=cache.expires)
			return cache
		elif response.status_code == 404:
			if cache:
				cache.delete()
				memcache.delete(request)
			forward.forwardResponse(response)
		elif cache and response.status_code >= 500:
			logging.warning('500, serving cache copy')
			return cache
		elif response.status_code != 200:
			forward.forwardResponse(response)
		cache = self.cache(key_name=request)
		cache.data = db.Blob(response.content)
		cache.maxAge = self.getMaxAge(response.headers)
		cache.lastRefresh = datetime.datetime.utcnow()
		if not 'last-modified' in response.headers:
			cache.lastModified = cache.lastRefresh
		else:
			cache.lastModified = web.parsehttpdate(response.headers['last-modified'])
		cache.expires = cache.lastRefresh + datetime.timedelta(seconds=cache.maxAge)
		for h in self.headerBlacklist:
			if h in response.headers:
				del response.headers[h]
		cache.headers = []
		for k, v in response.headers.iteritems():
			cache.headers.append('%s: %s' % (k, v))
		if cache.maxAge == 0:
			# no cache
			logging.debug('maxAge null, cache disabled')
			return cache
		self.memcacheSet(key=request, value=cache, time=cache.expires)
		try:
			cache.put()
			logging.debug('new cache entry created')
		except Exception, e:
			logging.warning('cache.put(): Error (%s: %s)' % (type(e), e))
		return cache

	def getMaxAge(self, headers):
		maxAge = 0
		if not self.forceTTL is None:
			maxAge = self.forceTTL
		elif 'cache-control' in headers:
			header = headers['cache-control'].split(',')
			for h in header:
				n = h.find('max-age=')
				if n != -1:
					maxAge = int(h[n + 8:])
					break
		if not self.maxTTL is None and maxAge > self.maxTTL:
			maxAge = self.maxTTL
		return maxAge
