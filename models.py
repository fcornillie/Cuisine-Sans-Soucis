# Author: Frederik Cornillie <frederik.cornillie@gmail.com>
# Created: May 9th, 2011

from google.appengine.ext import db

class User(db.Model):
	"""
	Our user.
	"""
	
	from datetime import datetime
	
	user = db.UserProperty()
	joined_date = db.DateTimeProperty(auto_now_add=True)
	friends_list = db.ListProperty(db.Key)		# XX ListProperties are limited to 5000 entries
	_is_admin = db.BooleanProperty(default=False)
	avatar = db.BlobProperty()
	
	@property
	def is_admin(self):
		return self._is_admin
		
	@property
	def nickname(self):
		return self.user.nickname()
		
	@property
	def email(self):
		return self.user.email()
		
	def friends(self, keys_only=False):
		"""
		Returns a list containing the friend instances.
		"""
		if self.friends_list:
			if keys_only:
				return self.friends_list
			else:
				return Player.get(self.friends_list)
		else:
			return []
	
	def friend(self, player_key):
		"""
		Adds a Player to the list of friends.
		
		Requires the key of the Player instance.
		
		Returns True if the Player has been added to the list. Returns False if the Player was already friended.
		"""
		if player_key != self.key():		# obviously you cannot friend yourself
			try:
				self.friends_list.index(player_key)
				return False
			except ValueError:
				self.friends_list.append(player_key)
				self.put()
				return True
	
	def defriend(self, player_key):
		"""
		Removes a Player from the list of friends.
		
		Requires the key of the Player instance.
		
		Returns True if the Player has been removed from the list. Returns False if the Player was not in the list.
		"""
		if player_key != self.key():		# obviously you cannot defriend yourself
			try:
				self.friends_list.index(player_key)
				self.friends_list.remove(player_key)
				self.put()
				return True
			except ValueError:
				return False

class Recipe(db.Model):
	type = db.StringProperty(choices=set(["starter", "main", "dessert"]))
	name = db.StringProperty()
	teaser = db.StringProperty()
	ingredients = db.TextProperty()
	method = db.TextProperty()
	preparation_time = db.IntegerProperty()
	cooking_time = db.IntegerProperty()
	ingredients_list = db.ListProperty(db.Key)
	foodtypes = db.ListProperty(db.Key)
	author = db.ReferenceProperty(User, collection_name="recipes")
	picture = db.BlobProperty()
	season = db.StringProperty()
	timestamp = db.DateTimeProperty(auto_now_add=True)

class FoodType(db.Model):
	name = db.CategoryProperty()
	
class Ingredient(db.Model):
	name = db.StringProperty()

class Meal(db.Model):
	""" A Meal represents one instance where a User prepares and devours a Meal. """
	
	timestamp = db.DateTimeProperty(auto_now_add=True)
	recipe = db.ReferenceProperty(Recipe)
	user = db.ReferenceProperty(User)
	rating = db.RatingProperty()
	preparation_time = db.IntegerProperty()
	cooking_time = db.IntegerProperty()