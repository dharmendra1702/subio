from django.db import models
import uuid
from cloudinary.models import CloudinaryField

from django.db import models

from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    image = models.ImageField(upload_to="products/")

    # NEW FIELDS
    highlights = models.TextField(blank=True)
    brand = models.CharField(max_length=100, blank=True)
    shelf_life = models.CharField(max_length=100, blank=True)
    net_weight = models.CharField(max_length=100, blank=True)
    gst_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)

    created = models.DateTimeField(auto_now_add=True)

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/gallery/")

class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    token = models.UUIDField(default=uuid.uuid4, editable=False)

    def __str__(self):
        return self.email


from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_photo = models.ImageField(upload_to="profile/", blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class Address(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    label = models.CharField(max_length=50)

    address = models.TextField()

    is_default = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.label


class MobileNumber(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    mobile = models.CharField(max_length=10)

    is_primary = models.BooleanField(default=False)

    is_verified = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.mobile