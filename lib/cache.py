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
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import urlfetch, urlfetch_errors


# Copy from httplib
httpResponses = {
    100: 'Continue',
    101: 'Switching Protocols',

    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    203: 'Non-Authoritative Information',
    204: 'No Content',
    205: 'Reset Content',
    206: 'Partial Content',

    300: 'Multiple Choices',
    301: 'Moved Permanently',
    302: 'Found',
    303: 'See Other',
    304: 'Not Modified',
    305: 'Use Proxy',
    306: '(Unused)',
    307: 'Temporary Redirect',

    400: 'Bad Request',
    401: 'Unauthorized',
    402: 'Payment Required',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Required',
    408: 'Request Timeout',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length Required',
    412: 'Precondition Failed',
    413: 'Request Entity Too Large',
    414: 'Request-URI Too Long',
    415: 'Unsupported Media Type',
    416: 'Requested Range Not Satisfiable',
    417: 'Expectation Failed',

    500: 'Internal Server Error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported',
}


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

	origin = None
	forceTTL = None
	maxTTL = None
	ignoreQueryString = False
	forwardPost = True

	# These headers won't be forwarded
	headerBlacklist = [
			'date',
			'last-modified',
			'via'
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
		except CacheExpired, cache:
			cache = self.writeCache(request, cache())
		if not web.modified(cache.lastModified):
			raise web.HTTPError(status='304 Not Modified')
		for h in cache.headers:
			print h
		return cache.data

	def POST(self, request):
		if self.ignoreQueryString is False:
			request += web.ctx.query
		url = self.origin + request
		if self.forwardPost is False:
			raise web.SeeOther(request, absolute=True)
		self.forwardRequest(url, method='POST')

	def DELETE(self, request):
		# Set your client IP address to authorize cache entry deletion
		allowedIP = ['127.0.0.1']
		if not web.ctx.env['REMOTE_ADDR'] in allowedIP:
			raise web.Forbidden()
		if request.split('/').pop() == '__ALL__':
			if 'memcache' in  web.ctx.query:
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
		headers = {'User-Agent' : 'CirruxCache 0.1 / shad ;'}
		if cache:
			# Bypass google cache
			headers['Cache-Control'] = 'no-cache, max-age=0'
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
			self.forwardResponse(response)
		elif cache and response.status_code >= 500:
			logging.warning('500, serving cache copy')
			return cache
		elif response.status_code != 200:
			self.forwardResponse(response)
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
			header = headers['cache-control']
			n = header.find('max-age=')
			if n != -1:
				maxAge = int(header[n + 8:])
		if not self.maxTTL is None and maxAge > self.maxTTL:
			maxAge = self.maxTTL
		return maxAge

	def forwardResponse(self, response):
		status = '%s %s' % (response.status_code, httpResponses[response.status_code])
		raise web.HTTPError(status=status, headers=response.headers, data=response.content)

	def forwardRequest(self, url, method='GET'):
		headers = {}
		for key, value in web.ctx.environ.iteritems():
			if not key.startswith('HTTP_'):
				continue
			key = '-'.join([k.capitalize() for k in key[5:].split('_')])
			headers[key] = value
		headers['Host'] = self.origin[7:]
		headers['User-Agent'] = 'CirruxCache 0.1 / shad (http://cirrux.org/cache/) ;'
		response = urlfetch.Fetch(url=url, method=method, headers=headers)
		self.forwardResponse(response)
