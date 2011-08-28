# Author: Frederik Cornillie <frederik.cornillie@gmail.com>
# Created: May 9th, 2011

from google.appengine.ext import db

class User(db.Model):
	"""
	Our user.
	"""
		
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
				return User.get(self.friends_list)
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
	foodtypes_list = db.ListProperty(db.Key)
	author = db.ReferenceProperty(User, collection_name="recipes")
	image = db.BlobProperty()
	season = db.StringProperty()
	publish = db.StringProperty(choices=set(["no", "friends", "public"]))
	quickadd = db.BooleanProperty(default=False)
	timestamp = db.DateTimeProperty(auto_now_add=True)
	
	@property
	def foodtypes(self):
		return FoodType.get(self.foodtypes_list)
	
	@property
	def total_time(self):
		return self.preparation_time + self.cooking_time
	
	@property
	def rating(self):
		return "***"
	
	def to_dict(self):
		return dict([(p, unicode(getattr(self, p))) for p in self.properties()])		

class FoodType(db.Model):
	name = db.CategoryProperty()
	
class Ingredient(db.Model):
	name = db.StringProperty()

class MealGuest(db.Model):
	""" A GuestMeal represents a guest who is invited to a meal. """
	
	user = db.ReferenceProperty(User)
	status = db.StringProperty(choices=set(["yes", "no", "maybe"]))
	food_rating = db.RatingProperty()
	
class Meal(db.Model):
	""" A Meal represents one instance where a User prepares and devours a Meal. """
	
	date = db.DateTimeProperty()
	recipe = db.ReferenceProperty(Recipe)
	user = db.ReferenceProperty(User)
	rating = db.RatingProperty()
	guests = db.ReferenceProperty(MealGuest)
	preparation_time = db.IntegerProperty()
	cooking_time = db.IntegerProperty()
	
	def to_dict(self):
		return dict([(p, unicode(getattr(self, p))) for p in self.properties()])