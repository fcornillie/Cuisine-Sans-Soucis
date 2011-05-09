# Author: Frederik Cornillie <frederik.cornillie@gmail.com>
# Created: May 9th, 2011

from google.appengine.api import users

from models import *

# **********
# HELPER FUNCTIONS
# **********

def get_current_user():
	user_query = User.gql("WHERE user = :1", users.get_current_user())
	if user_query.count() > 0:
		user = user_query[0]
		return user
	else:
		return None

def append_base_template_values(template_values):
	"""
	Appends the values for the base template to the values for the requested view. The appended values are:
	- user: the current user
	- logouturl: the logout url
	
	Requires a dictionary containing the values for the requested view.
	"""
	
	user = get_current_user()
	template_values['user'] = user
	template_values['logouturl'] = users.create_logout_url("/")
	template_values['is_current_user_admin'] = users.is_current_user_admin()
	
	return template_values