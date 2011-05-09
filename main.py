#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# Author: Frederik Cornillie <frederik.cornillie@gmail.com>
# Created: May 9th, 2011

import os
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp.util import login_required
from google.appengine.api import users
from models import *

class MainHandler(webapp.RequestHandler):
	def get(self):
		
		template_values = {
			'recipes':Recipe.all(),
		}
		
		path = os.path.join(os.path.dirname(__file__), 'templates/recipe_list.html')
		self.response.out.write(template.render(path, template_values))

class get_recipe(webapp.RequestHandler):
	def get(self):
		recipe = Recipe.get(self.request.get('key'))
		
		template_values = {
			'recipe':recipe,
		}
		
		path = os.path.join(os.path.dirname(__file__), 'templates/recipe_detail.html')
		self.response.out.write(template.render(path, template_values))
	
	def post(self):
		user = users.get_current_user()
		if user:
			# do stuff
			pass
	
def main():
	application = webapp.WSGIApplication([
		('/', MainHandler),
		('/recipe', get_recipe),
	], debug=True)
	util.run_wsgi_app(application)


if __name__ == '__main__':
	main()
