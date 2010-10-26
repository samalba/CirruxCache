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

"""CirruxCache configuration file
"""

from lib import cache, redirect, forward, image
urls = {}


# EDIT BELOW

urls['default'] = (
		#'(/debug/.*)', 'Debug',
		'(/data/.*)', 'config.Static',
		'/www(/.*)', 'config.Www'
		)

# POP definition
# You can define and configure your Point Of Presence

class Static(cache.Service):
	origin = 'http://static.mydomain.tld'
	maxTTL = 2592000 # 1 month
	ignoreQueryString = True

class Www(cache.Service):
	origin = 'http://www.mydomain.tld'
	allowFlushFrom = ['127.0.0.1']
	forceTTL = 3600 # 1 hour
	ignoreQueryString = True
	forwardPost = False
