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
from helpers import *

class MainHandler(webapp.RequestHandler):
	@login_required
	def get(self):
		
		template_values = {
			'recipes':Recipe.all(),
		}
		
		path = os.path.join(os.path.dirname(__file__), 'templates/recipe_list.html')
		self.response.out.write(template.render(path, append_base_template_values(template_values)))

class recipe_detail(webapp.RequestHandler):
	@login_required
	def get(self):
		if self.request.get('key'):
			recipe = Recipe.get(self.request.get('key'))
		else:
			recipe = None
			
		template_values = {
			'recipe':recipe,
		}
		
		path = os.path.join(os.path.dirname(__file__), 'templates/recipe_detail.html')
		self.response.out.write(template.render(path, append_base_template_values(template_values)))
	
	def post(self):
		user = users.get_current_user()
		if user:
			recipe = Recipe()
			recipe.name = self.request.get("name")
			recipe.ingredients = self.request.get("ingredients")
			recipe.method = self.request.get("method")
			recipe.preparation_time = int(self.request.get("preparation_time"))
			recipe.cooking_time = int(self.request.get("cooking_time"))
			recipe.author = get_current_user()
			recipe.put()
			self.redirect("/")
			
def main():
	application = webapp.WSGIApplication([
		('/', MainHandler),
		('/recipe', recipe_detail),
	], debug=True)
	util.run_wsgi_app(application)


if __name__ == '__main__':
	main()

