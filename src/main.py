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


FACEBOOK_APP_ID = "238124392903238"
FACEBOOK_APP_SECRET = "11b592fc9c39e6750288eb9902138aac"

import base64
import cgi
import Cookie
import email.utils
import hashlib
import hmac
import logging
import os.path
import time
import urllib
import wsgiref.handlers

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required
#from helpers import login_required
from google.appengine.api import users
from django.utils import simplejson as json
from models import *
import helpers
import datetime

class BaseHandler(webapp.RequestHandler):
	""" The base handler for the production environment on Google """
	
	@property
	def current_user(self):
		"""Returns the logged in user (Facebook first, then Google), or None if unconnected."""
		if not hasattr(self, "_current_user"):
			self._current_user = None
			# Facebook
			user_id = parse_cookie(self.request.cookies.get("fb_user"))
			if user_id:
				self._current_user = User.get_by_key_name(user_id)
			# Google
			else:
				if users.get_current_user() != None:
					user_qry = User.all().filter("user", users.get_current_user())
					if user_qry.count() > 0:
						user = user_qry[0]
					else:
						user = User(user=users.get_current_user())
						user.put()
					self._current_user = user
		return self._current_user

class RootHandler(BaseHandler):
	def get(self):
		if self.current_user == None:
			self.redirect("/recipes")
		else:
			self.redirect("/schedule")

class FBLoginHandler(BaseHandler):
	def get(self):
		verification_code = self.request.get("code")
		args = dict(client_id=FACEBOOK_APP_ID, redirect_uri=self.request.path_url)
		if self.request.get("code"):
			args["client_secret"] = FACEBOOK_APP_SECRET
			args["code"] = self.request.get("code")
			response = cgi.parse_qs(urllib.urlopen(
				"https://graph.facebook.com/oauth/access_token?" +
				urllib.urlencode(args)).read())
			access_token = response["access_token"][-1]

			# Download the user profile and cache a local instance of the
			# basic profile info
			profile = json.load(urllib.urlopen(
				"https://graph.facebook.com/me?" +
				urllib.urlencode(dict(access_token=access_token))))
			user = User(key_name=str(profile["id"]), id=str(profile["id"]),
						name=profile["name"], access_token=access_token,
						profile_url=profile["link"])
			user.put()
			set_cookie(self.response, "fb_user", str(profile["id"]),
					expires=time.time() + 30 * 86400)
			self.redirect("/")
		else:
			self.redirect(
				"https://graph.facebook.com/oauth/authorize?" +
				urllib.urlencode(args))


class FBLogoutHandler(BaseHandler):
	def get(self):
		set_cookie(self.response, "fb_user", "", expires=time.time() - 86400)
		self.redirect("/")


def set_cookie(response, name, value, domain=None, path="/", expires=None):
	"""Generates and signs a cookie for the give name/value"""
	timestamp = str(int(time.time()))
	value = base64.b64encode(value)
	signature = cookie_signature(value, timestamp)
	cookie = Cookie.BaseCookie()
	cookie[name] = "|".join([value, timestamp, signature])
	cookie[name]["path"] = path
	if domain: cookie[name]["domain"] = domain
	if expires:
		cookie[name]["expires"] = email.utils.formatdate(
			expires, localtime=False, usegmt=True)
	response.headers._headers.append(("Set-Cookie", cookie.output()[12:]))


def parse_cookie(value):
	"""Parses and verifies a cookie value from set_cookie"""
	if not value: return None
	parts = value.split("|")
	if len(parts) != 3: return None
	if cookie_signature(parts[0], parts[1]) != parts[2]:
		logging.warning("Invalid cookie signature %r", value)
		return None
	timestamp = int(parts[1])
	if timestamp < time.time() - 30 * 86400:
		logging.warning("Expired cookie %r", value)
		return None
	try:
		return base64.b64decode(parts[0]).strip()
	except:
		return None


def cookie_signature(*parts):
	"""Generates a cookie signature.

	We use the Facebook app secret since it is different for every app (so
	people using this example don't accidentally all use the same secret).
	"""
	hash = hmac.new(FACEBOOK_APP_SECRET, digestmod=hashlib.sha1)
	for part in parts: hash.update(part)
	return hash.hexdigest()
	
class recipe_list(BaseHandler):
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
			'page':'recipes',
			'current_user':self.current_user,
			'foodtypes':FoodType.all(),
			'query':query,
			'recipes':recipes_query,
		}
		
		path = os.path.join(os.path.dirname(__file__), 'templates/recipe_list.html')
		self.response.out.write(template.render(path, helpers.append_base_template_values(template_values)))

class recipe_detail(BaseHandler):
	def get(self):
		if self.request.get('key'):
			recipe = Recipe.get(self.request.get('key'))
		else:
			recipe = None
			
		template_values = {
			'page':'recipes',
			'current_user':self.current_user,
			'recipe':recipe,
		}
		
		path = os.path.join(os.path.dirname(__file__), 'templates/recipe_detail.html')
		self.response.out.write(template.render(path, helpers.append_base_template_values(template_values)))
	
	def post(self):
		user = self.current_user
		if user:
			recipe = Recipe()
			recipe.name = self.request.get("name")
			recipe.teaser = self.request.get("teaser")
			recipe.ingredients = self.request.get("ingredients")
			recipe.method = self.request.get("method")
			recipe.preparation_time = int(self.request.get("preparation_time"))
			recipe.cooking_time = int(self.request.get("cooking_time"))
			recipe.author = self.current_user
			if self.request.get("img"):
				img_data = self.request.get("img")
				recipe.image = db.Blob(img_data)
			recipe.put()
			self.redirect("/")

class recipe_edit(BaseHandler):
	def post(self):
		user = self.current_user
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

class recipe_jsonquery(BaseHandler):
	def post(self):
		user = self.current_user
		if user:
			recipes = []
			for r in Recipe.all():
				if self.request.get("query").lower() in r.name.lower():
					recipes.append({'key':str(r.key()), 'name':r.name})
			result = {'recipes':recipes}
			self.response.out.write(json.dumps(result))

class schedule(BaseHandler):
	def get(self):
		if not self.current_user:
			self.redirect("/auth/facebook/login")
		else:
			format = self.request.get('format').lower()
			schedule = []

			if self.request.get("user"):
				user = User.get(self.request.get("user"))
			else:
				user = self.current_user
			
			if self.request.get('start_date'):
				dateparts = [int(i) for i in self.request.get("start_date").split("-")]
				start_date = datetime.date(dateparts[0], dateparts[1], dateparts[2])
			else:
				start_date = datetime.date.today()
			if self.request.get('nof_days'):
				nof_days = self.request.get('nof_days')
			else:
				from settings import SCHEDULE_DEFAULT_NUMBER_OF_DAYS
				nof_days = SCHEDULE_DEFAULT_NUMBER_OF_DAYS
			if self.request.get('direction')=='back':
				start_date -= datetime.timedelta(nof_days)
			if self.request.get('direction')=='forward':
				start_date += datetime.timedelta(1)
			
			for i in range(nof_days):
				date_next = start_date+datetime.timedelta(i)
				meal_query = Meal.gql("WHERE user = :1 AND date = :2", user, date_next)
				invitations_query = Invitation.gql("WHERE guest = :1 AND date = :2", user, date_next)
				date = {
					'date':date_next,
					'meals':meal_query,
					'invitations':invitations_query,
				}
				schedule.append(date)
				
			if format == 'partial':
				template_values = {
					'page':'schedule',
					'current_user':self.current_user,
					'schedule':schedule,
					'today':datetime.date.today(),
				}
				path = os.path.join(os.path.dirname(__file__), 'templates/schedule_days.html')
				self.response.out.write(template.render(path, helpers.append_base_template_values(template_values)))
			else:
				template_values = {
					'page':'schedule',
					'current_user':self.current_user,
					'user':user,
					'schedule':schedule,
					'today':datetime.date.today(),
				}
				path = os.path.join(os.path.dirname(__file__), 'templates/schedule.html')
				self.response.out.write(template.render(path, helpers.append_base_template_values(template_values)))

class schedule_modify(BaseHandler):
	def post(self):
		user = self.current_user
		if user:
			dateparts = [int(i) for i in self.request.get("date").split("-")]
			date = datetime.datetime(dateparts[0], dateparts[1], dateparts[2])
			if self.request.get("recipe"):
				# querying for existing recipes
				recipe = Recipe.get(self.request.get("recipe"))
			else:
				# check whether current user already has a recipe by that name
				if self.request.get("recipe_name"):
					recipe_query = Recipe.gql("WHERE author = :1 AND name = :2", self.current_user, self.request.get("recipe_name"))
					if recipe_query.count() > 0:
						recipe = recipe_query[0]
					else:
						# quickadding a new recipe
						recipe = Recipe(name=self.request.get("recipe_name"), author=self.current_user, quickadd=True)
						recipe.put()
				else:
					recipe = None
			action = int(self.request.get("action"))
					
			# first check whether recipe is already scheduled for that day
			if recipe:
				meal_query = Meal.gql("WHERE user = :1 AND date = :2 AND recipe = :3", self.current_user, date, recipe)
			else:
				meal_query = None
			
			# adding a meal
			if action==1:
				if meal_query:
					if meal_query.count() > 0:
						result = {'result':'ADD_ERROR'}
					else:
						meal = Meal(date=date, recipe=recipe, user=self.current_user)
						meal.put()
						result = {
							'result':'ADD_OK',
							'recipe':{
								'key':str(recipe.key()),
								'name':recipe.name,
								'type':recipe.type,
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
							}
						}
			
			self.response.out.write(json.dumps(result))

class profile_detail(BaseHandler):
	def get(self):
		
		if self.request.get("user"):
			user = User.get(self.request.get("user"))
		else:
			user = self.current_user
		
		todo = []
		
		meals_to_be_rated = []
		invitation_query = Invitation.all().filter('guest', user).filter('attending', 'yes').filter('food_rating', None)
		for i in invitation_query:
			if i.meal.date < datetime.datetime.today():
				meals_to_be_rated.append(i)
			
		todo.extend(meals_to_be_rated)
		
		import calendar
		import locale
		#locale.setlocale(locale.LC_ALL, 'english_US')
		#  update day names for new locale
		WEEKDAYS = [day for day in calendar.day_name] # list of day name strings
		
		template_values = {
			'page':'profile',
			'current_user':self.current_user,
			'user':user,
			'todo':todo,
			'weekdays':WEEKDAYS,
		}
		
		path = os.path.join(os.path.dirname(__file__), 'templates/profile_detail.html')
		self.response.out.write(template.render(path, helpers.append_base_template_values(template_values)))
		
class profile_modify_preference(BaseHandler):
	def post(self):
		user = self.current_user
		if user:
			ft = FoodType.get(self.request.get("foodtype"))
			#pref_qry = user.preferences.filter("foodtype", ft)
			pref_qry = Preference.gql("WHERE user = :1 AND foodtype = :2", user, ft)
			if pref_qry.count()>0:
				pref = pref_qry[0]
				name = self.request.get("name")
				if name == "like":
					pref.like = self.request.get("value")=="1"
				if name == "allergic":
					pref.allergic = self.request.get("value")=="1"
				if name[0:3] == "day":
					day = int(name[3])
					if self.request.get("value")=="1":
						if not day in pref.weekdays:
							pref.weekdays.append(day)
					else:
						if day in pref.weekdays:
							pref.weekdays.remove(day)
				pref.put()
				self.response.out.write(json.dumps("OK"))
			else:
				self.response.out.write(json.dumps("ERROR"))

class about(BaseHandler):
	def get(self):
		template_values = {
			'current_user':self.current_user,
		}
		path = os.path.join(os.path.dirname(__file__), 'templates/about.html')
		self.response.out.write(template.render(path, helpers.append_base_template_values(template_values)))
	
class get_image(BaseHandler):
	""" Gets the image data for a certain object.
	Requires:
	+ object_key: the key of a certain object
	+ image_property: the name of the Blob property.
	"""
	
	def get(self):
		object = db.Model.get(self.request.get('object_key'))
		image_data = object.image
		self.response.headers['Content-Type'] = 'image/jpeg'
		self.response.out.write(image_data)

class import_content(BaseHandler):
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
		(r'/auth/facebook/login', FBLoginHandler),
		(r'/auth/facebook/logout', FBLogoutHandler),
		('/', RootHandler),
		('/recipes', recipe_list),
		('/recipe', recipe_detail),
		('/recipe/edit', recipe_edit),
		('/recipe/jsonquery', recipe_jsonquery),
		('/schedule', schedule),
		('/schedule/modify', schedule_modify),
		('/profile', profile_detail),
		('/profile/preferences/modify', profile_modify_preference),
		('/about', about),
		('/get_image', get_image),
		('/import_content', import_content),
	], debug=True)
	template.register_template_library('django.contrib.humanize.templatetags.humanize')
	util.run_wsgi_app(application)


if __name__ == '__main__':
	main()

