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
	
	def friend(self, user_key):
		"""
		Adds a User to the list of friends. Friending is birectional.
		
		Requires the key of the User instance.
		
		Returns True if the User has been added to the list. Returns False if the User was already friended.
		"""
		if user_key != self.key():		# obviously you cannot friend yourself
			try:
				self.friends_list.index(user_key)
				return False
			except ValueError:
				self.friends_list.append(user_key)
				self.put()
				user = User.get(user_key)	# friending is birectional
				user.friends_list.append(self.key())
				user.put()
				return True
	
	def defriend(self, user_key):
		"""
		Removes a User from the list of friends.
		
		Requires the key of the User instance.
		
		Returns True if the User has been removed from the list. Returns False if the User was not in the list.
		"""
		if user_key != self.key():		# obviously you cannot defriend yourself
			try:
				self.friends_list.index(user_key)
				self.friends_list.remove(user_key)
				self.put()
				return True
			except ValueError:
				return False
	
	@property
	def recipe_count(self):
		return self.recipes.filter('quickadd', False).count()

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

class Meal(db.Model):
	""" A Meal represents one instance where a User prepares and devours a Meal. """
	
	date = db.DateTimeProperty()
	recipe = db.ReferenceProperty(Recipe)
	user = db.ReferenceProperty(User)
	rating = db.RatingProperty()
	preparation_time = db.IntegerProperty()
	cooking_time = db.IntegerProperty()
	
	def to_dict(self):
		return dict([(p, unicode(getattr(self, p))) for p in self.properties()])

class Invitation(db.Model):
	""" An Invitation happens when a user is invited as a guest to a meal cooked by another user. """
	
	date = db.DateTimeProperty()		# the meal referent already has a date, however, the date field of Invitation is not redundant. We need a quick way of querying invitations for one day, and since GAE does not support JOIN queries, this is way one to do this.
	meal = db.ReferenceProperty(Meal, collection_name="invitations")
	guest = db.ReferenceProperty(User)
	attending = db.StringProperty(choices=set(["yes", "no", "maybe"]))
	food_rating = db.RatingProperty()