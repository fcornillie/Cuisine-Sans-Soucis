# Author: Frederik Cornillie <frederik.cornillie@gmail.com>
# Created: May 9th, 2011

import logging

from google.appengine.api import users

from models import *

# **********
# HELPER FUNCTIONS
# **********

def login_required(handler_method):
	"""A decorator to require that a user be logged in to access a handler.

	To use it, decorate your get() method like this:

	@login_required
	def get(self):
	user = users.get_current_user(self)
	self.response.out.write('Hello, ' + user.nickname())

	We will redirect to a login page if the user is not logged in. We always
	redirect to the request URI, and Google Accounts only redirects back as a GET
	request, so this should not be used for POSTs.
	"""
	def check_login(self, *args):
		logging.debug("***+++++++++++++++")
		from google.appengine.ext import webapp
		if self.request.method != 'GET':
			raise webapp.Error('The check_login decorator can only be used for GET requests')
		if not self.current_user:
			self.redirect("/auth/facebook/login")
			return
		else:
			handler_method(self, *args)
			return check_login
  
def get_current_user():
	user_query = User.gql("WHERE user = :1", users.get_current_user())
	if user_query.count() > 0:
		user = user_query[0]
	else:
		user = User(user=users.get_current_user())
		user.put()
		
	return user

def append_base_template_values(template_values={}):
	"""
	Appends the values for the base template to the values for the requested view. The appended values are:
	- user: the current user
	- logouturl: the logout url
	
	Requires a dictionary containing the values for the requested view.
	"""
	
	#user = get_current_user()
	#template_values['current_user'] = user
	#template_values['logouturl'] = users.create_logout_url("/")
	#template_values['is_current_user_admin'] = users.is_current_user_admin()
	import datetime
	template_values['today'] = datetime.date.today()
	template_values['google_logout_url'] = users.create_logout_url("/")
	template_values['google_login_url'] = users.create_login_url("/")
	
	return template_values