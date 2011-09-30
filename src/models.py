# Author: Frederik Cornillie <frederik.cornillie@gmail.com>
# Created: May 9th, 2011

from google.appengine.ext import db

class User(db.Model):
	"""
	Our user.
	"""
	
	# fb user here
	id = db.StringProperty()		# required=True
	created = db.DateTimeProperty(auto_now_add=True)
	updated = db.DateTimeProperty(auto_now=True)
	name = db.StringProperty() 	#required=True
	profile_url = db.StringProperty()	# required=True
	access_token = db.StringProperty()	# required=True
	
	# old code below
	user = db.UserProperty()
	_is_admin = db.BooleanProperty(default=False)
	
	@property
	def is_admin(self):
		return self._is_admin
		
	@property
	def nickname(self):
		return self.user.nickname()
		
	@property
	def email(self):
		return self.user.email()
	
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
	user = db.ReferenceProperty(User, collection_name="meals")
	rating = db.RatingProperty()
	preparation_time = db.IntegerProperty()
	cooking_time = db.IntegerProperty()
	
	@property
	def guests(self):
		return [i.guest for i in self.invitations]
	
	def to_dict(self):
		return dict([(p, unicode(getattr(self, p))) for p in self.properties()])

class Invitation(db.Model):
	""" An Invitation happens when a user is invited as a guest to a meal cooked by another user. """
	
	date = db.DateTimeProperty()		# the meal referent already has a date, however, the date field of Invitation is not redundant. We need a quick way of querying invitations for one day, and since GAE does not support JOIN queries, this is way one to do this.
	meal = db.ReferenceProperty(Meal, collection_name="invitations")
	guest = db.ReferenceProperty(User)
	attending = db.StringProperty(choices=set(["yes", "no", "maybe"]))
	food_rating = db.RatingProperty()