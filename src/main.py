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
from django.utils import simplejson as json
from models import *
import helpers

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
			
		# XXX: need a coherent way of checking whether a recipe is not just quickadded through the schedule
		recipes_query = Recipe.all().filter("quickadd", False)
		
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
		self.response.out.write(template.render(path, helpers.append_base_template_values(template_values)))

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
		self.response.out.write(template.render(path, helpers.append_base_template_values(template_values)))
	
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
			recipe.author = helpers.get_current_user()
			if self.request.get("img"):
				img_data = self.request.get("img")
				recipe.image = db.Blob(img_data)
			recipe.put()
			self.redirect("/")

class recipe_edit(webapp.RequestHandler):
	def post(self):
		user = users.get_current_user()
		if user:
			recipe = Recipe.get(self.request.get("key"))
			property = self.request.get("id")
			newvalue = self.request.get("value")
			from google.appengine.ext.db import IntegerProperty
			if isinstance(recipe.fields()[property], IntegerProperty):
				recipe.__setattr__(property, int(newvalue))
			else:
				recipe.__setattr__(property, unicode(newvalue))
			recipe.put()
			self.response.out.write(newvalue)
			
class recipe_jsonquery(webapp.RequestHandler):
	def post(self):
		user = users.get_current_user()
		if user:
			recipes = []
			for r in Recipe.all():
				if self.request.get("query").lower() in r.name.lower():
					recipes.append({'key':str(r.key()), 'name':r.name})
			result = {'recipes':recipes}
			self.response.out.write(json.dumps(result))

class schedule(webapp.RequestHandler):
	@login_required
	def get(self):
		import datetime
		
		schedule = []
		if self.request.get('future_days'):
			future_days = self.request.get('future_days')
		else:
			from settings import DEFAULT_FUTURE_DAYS
			future_days = DEFAULT_FUTURE_DAYS		
		for i in range(0, future_days):
			date = {
				'date':datetime.date.today()+datetime.timedelta(i),
				'meals':Meal.gql("WHERE user = :1 AND date = :2", helpers.get_current_user(), datetime.date.today()+datetime.timedelta(i)),
			}
			schedule.append(date)

		template_values = {
			'schedule':schedule,
		}
		
		path = os.path.join(os.path.dirname(__file__), 'templates/schedule.html')
		self.response.out.write(template.render(path, helpers.append_base_template_values(template_values)))

class schedule_modify(webapp.RequestHandler):
	def post(self):
		user = users.get_current_user()
		if user:
			import datetime
			dateparts = [int(i) for i in self.request.get("date").split("_")]
			date = datetime.datetime(dateparts[0], dateparts[1], dateparts[2])
			if self.request.get("recipe"):
				# querying for existing recipes
				recipe = Recipe.get(self.request.get("recipe"))
			else:
				# check whether current user already has a recipe by that name
				if self.request.get("recipe_name"):
					recipe_query = Recipe.gql("WHERE author = :1 AND name = :2", helpers.get_current_user(), self.request.get("recipe_name"))
					if recipe_query.count() > 0:
						recipe = recipe_query[0]
					else:
						# quickadding a new recipe
						recipe = Recipe(name=self.request.get("recipe_name"), author=helpers.get_current_user(), quickadd=True)
						recipe.put()
				else:
					recipe = None
			action = int(self.request.get("action"))
					
			# first check whether recipe is already scheduled for that day
			if recipe:
				meal_query = Meal.gql("WHERE user = :1 AND date = :2 AND recipe = :3", helpers.get_current_user(), date, recipe)
			else:
				meal_query = None
			
			# adding a meal
			if action==1:
				if meal_query:
					if meal_query.count() > 0:
						result = {'result':'ADD_ERROR'}
					else:
						meal = Meal(date=date, recipe=recipe, user=helpers.get_current_user())
						meal.put()
						result = {
							'result':'ADD_OK',
							'recipe':{
								'key':str(recipe.key()),
								'name':recipe.name,
							}
						}
			# removing a meal
			elif action==2:
				if meal_query:
					if meal_query.count() == 0:
						result = {'result':'REMOVE_ERROR'}
					else:
						meal = meal_query[0]
						meal.delete()
						result = {
							'result':'REMOVE_OK',
							'recipe':{
								'key':str(recipe.key()),
								'name':recipe.name,
							}
						}

			
			self.response.out.write(json.dumps(result))

class profile_detail(webapp.RequestHandler):
	@login_required
	def get(self):
		
		if self.request.get("user"):
			user = User.get(self.request.get("user"))
		else:
			user = helpers.get_current_user()
			
		template_values = {
			'user':user,
		}
		
		path = os.path.join(os.path.dirname(__file__), 'templates/profile_detail.html')
		self.response.out.write(template.render(path, helpers.append_base_template_values(template_values)))
	
class get_image(webapp.RequestHandler):
	""" Gets the image data for a certain object.
	Requires:
	+ object_key: the key of a certain object
	+ image_property: the name of the Blob property.
	"""

	@login_required
	def get(self):
		object = db.Model.get(self.request.get('object_key'))
		image_data = object.image
		self.response.headers['Content-Type'] = 'image/jpeg'
		self.response.out.write(image_data)

class import_content(webapp.RequestHandler):
	@login_required
	def get(self):
		from content import recipes
		for r in recipes:
			recipe = Recipe(author=helpers.get_current_user())
			recipe.name = r['name']
			recipe.teaser = r['teaser']
			recipe.type = r['type']
			recipe.preparation_time = r['preparation_time']
			recipe.cooking_time = r['cooking_time']
			from google.appengine.api import urlfetch
			recipe.image = db.Blob(urlfetch.Fetch(r['image']).content)
			recipe.publish = r['publish']
			recipe.ingredients = r['ingredients']
			recipe.method = r['method']
			for f in r['foodtypes']:
				if FoodType.all().filter('name', f).count() == 1:
					ft = FoodType.all().filter('name', f)[0]
				else:
					ft = FoodType(name=f)
					ft.put()
				recipe.foodtypes_list.append(ft.key())
			recipe.put()
		self.response.out.write("OK")
			
def main():
	application = webapp.WSGIApplication([
		('/', schedule),
		('/recipes', recipe_list),
		('/recipe', recipe_detail),
		('/recipe/edit', recipe_edit),
		('/recipe/jsonquery', recipe_jsonquery),
		('/schedule', schedule),
		('/schedule/modify', schedule_modify),
		('/profile', profile_detail),
		('/get_image', get_image),
		('/import_content', import_content),
	], debug=True)
	template.register_template_library('django.contrib.humanize.templatetags.humanize')
	util.run_wsgi_app(application)


if __name__ == '__main__':
	main()

