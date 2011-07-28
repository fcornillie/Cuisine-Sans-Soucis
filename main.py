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

import logging

class recipe_list(webapp.RequestHandler):
	@login_required
	def get(self):
		query = {}
		foodtype = None
		user = None
		
		if self.request.get('foodtype'):
			foodtype = FoodType.get(self.request.get('foodtype'))
			query['foodtype'] = foodtype
		if self.request.get('user'):
			user = User.get(self.request.get('user'))
			query['user'] = user
			
		recipes_query = Recipe.all()
		
		if foodtype:
			recipes_query = recipes_query.filter('foodtypes_list', foodtype)
		if user:
			recipes_query = recipes_query.filter('author', user)
		
		recipes_query = recipes_query.fetch(50)
		
		template_values = {
			'foodtypes':FoodType.all(),
			'query':query,
			'recipes':recipes_query,
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
			recipe.teaser = self.request.get("teaser")
			recipe.ingredients = self.request.get("ingredients")
			recipe.method = self.request.get("method")
			recipe.preparation_time = int(self.request.get("preparation_time"))
			recipe.cooking_time = int(self.request.get("cooking_time"))
			recipe.author = get_current_user()
			if self.request.get("img"):
				img_data = self.request.get("img")
				recipe.image = db.Blob(img_data)
			recipe.put()
			self.redirect("/")

class get_image(webapp.RequestHandler):
	""" Gets the image data for a certain object.
	Requires:
	+ object_key: the key of a certain object
	+ image_property: the name of the Blob property.
	"""

	def get(self):
		from google.appengine.ext import db
		object = db.Model.get(self.request.get('object_key'))
		# image_data = object._properties[self.request.get('image_property')]
		image_data = object.image
		self.response.headers['Content-Type'] = 'image/jpeg'
		self.response.out.write(image_data)
			
def main():
	application = webapp.WSGIApplication([
		('/', recipe_list),
		('/recipes', recipe_list),
		('/recipe', recipe_detail),
		('/get_image', get_image),
	], debug=True)
	util.run_wsgi_app(application)


if __name__ == '__main__':
	main()

