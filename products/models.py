from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from django.db.models import Avg
import uuid



# ================= CATEGORY =================

class Category(models.Model):

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)

    created = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):

        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ================= PRODUCT =================
class Product(models.Model):
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name="products"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="products/")

    # PRODUCT DETAILS
    highlights = models.TextField(blank=True)
    shelf_life = models.CharField(max_length=100, blank=True)

    # SEO fields removed here

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["category"]),
            # models.Index(fields=["price"]), <-- REMOVED index
        ]

    @property
    def average_rating(self):
        avg_data = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return float(avg_data) if avg_data is not None else 0.0
    
    @property
    def review_count(self):
        """Returns the total number of reviews for this product"""
        return self.reviews.count()
    
    def __str__(self):
        return self.name


# ================= PRODUCT GALLERY =================

class ProductImage(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images"
    )

    image = models.ImageField(upload_to="products/gallery/")

    def __str__(self):
        return f"{self.product.name} image"


# ================= NEWSLETTER =================

class NewsletterSubscriber(models.Model):

    email = models.EmailField(unique=True)

    subscribed_at = models.DateTimeField(auto_now_add=True)

    token = models.UUIDField(default=uuid.uuid4, editable=False)

    class Meta:
        ordering = ["-subscribed_at"]

    def __str__(self):
        return self.email


# ================= USER PROFILE =================

class UserProfile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    profile_photo = models.ImageField(upload_to="profile/", blank=True, null=True)

    gender = models.CharField(max_length=10, blank=True)

    date_of_birth = models.DateField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


# ================= ADDRESS =================

class Address(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="addresses"
    )

    label = models.CharField(max_length=50)

    address = models.TextField()

    is_default = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.label} - {self.user.username}"


# ================= MOBILE NUMBER =================

class MobileNumber(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="mobiles"
    )

    mobile = models.CharField(max_length=10)

    is_primary = models.BooleanField(default=False)

    is_verified = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "mobile")

    def __str__(self):
        return self.mobile


# ================= COUPON =================

class Coupon(models.Model):

    code = models.CharField(max_length=20, unique=True)

    discount_amount = models.FloatField()

    is_active = models.BooleanField(default=True)

    valid_from = models.DateField()

    valid_to = models.DateField()

    class Meta:
        ordering = ["-valid_from"]

    def __str__(self):
        return self.code


# ================= ORDER =================

class Order(models.Model):

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    )

    order_id = models.CharField(max_length=20, unique=True, blank=True)

    # ⭐ NEW
    invoice_number = models.CharField(max_length=30, blank=True, null=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")

    address = models.TextField()

    payment_method = models.CharField(max_length=20)
    payment_status = models.CharField(max_length=20, default="Pending")

    # ⭐ NEW FINANCIAL FIELDS
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    gst = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    coupon_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    total = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    created_at = models.DateTimeField(auto_now_add=True)

    email_sent = models.BooleanField(default=False)
    
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    def save(self, *args, **kwargs):

        # Order ID
        if not self.order_id:
            self.order_id = "SUBIO-" + uuid.uuid4().hex[:8].upper()

        # Invoice number
        if not self.invoice_number:
            self.invoice_number = "INV-" + uuid.uuid4().hex[:10].upper()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_id


# ================= ORDER ITEMS =================

class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    # ✅ ADD THIS
    variant = models.ForeignKey(
        "ProductVariant",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    quantity = models.PositiveIntegerField()

    price = models.DecimalField(max_digits=10, decimal_places=2)
    

class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        related_name="variants",
        on_delete=models.CASCADE
    )

    size = models.CharField(max_length=50)   # 500g, 1kg
    mrp = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)

    @property
    def discount_percentage(self):
        if self.mrp and self.price and self.mrp > self.price:
            discount = ((self.mrp - self.price) / self.mrp) * 100
            return int(discount)
        return 0
    
    def __str__(self):
        return f"{self.product.name} - {self.size}"

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.FloatField()  # Changed from Integer to Float
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}★)"