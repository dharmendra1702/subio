import uuid
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
import razorpay
from django.conf import settings
from .models import Category, Review
from decimal import ROUND_HALF_UP, Decimal
import os
from .models import Order, OrderItem, Product, Address
import threading
from .models import ProductVariant

def home(request):
    categories = Category.objects.all()
    cart = request.session.get("cart", {})

    return render(request, "home.html", {
        "categories": categories,
        "cart_count": sum(item["quantity"] for item in cart.values())
    })



def login_page(request):

    if request.method == "POST":

        action = request.POST.get("action")

        # SIGNUP
        if action == "signup":

            username = request.POST["username"]
            email = request.POST["email"]
            password = request.POST["password"]

            if User.objects.filter(username=username).exists():
                return render(request,"login_signup.html",{"error":"Username exists"})

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            login(request, user)
            return redirect("complete_profile")

        # LOGIN
        if action == "login":

            username = request.POST["username"]
            password = request.POST["password"]

            user = authenticate(request, username=username, password=password)

            if user:
                login(request, user)

                # ADMIN → dashboard
                if user.is_staff:
                    return redirect("/dashboard/")

                # NORMAL USER → home
                return redirect("/")
            else:
                return render(request,"login_signup.html",{"error":"Invalid credentials"})

    return render(request,"login_signup.html")


from django.views.decorators.http import require_POST

@require_POST
def logout_view(request):
    logout(request)
    return redirect("/")

from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.views.decorators.http import require_POST
from .models import Category, NewsletterSubscriber, ProductImage

@login_required
def order_success(request, order_id):

    order = Order.objects.prefetch_related(
        "items__product"
    ).get(order_id=order_id, user=request.user)

    return render(request, "order_success.html", {
        "order": order,
        "items": order.items.all(),
        "email_status": order.email_sent
    })

@require_POST
def newsletter_subscribe(request):
    email = request.POST.get("email")

    subscriber, created = NewsletterSubscriber.objects.get_or_create(email=email)

    if created:
        send_custom_email(
            request,
            subscriber,
            "Welcome to Subio Foods 🌿",
            "Thanks for subscribing! You will receive premium offers soon."
        )

        return JsonResponse({
            "status": "success",
            "message": "Subscribed successfully!"
        })

    return JsonResponse({
        "status": "info",
        "message": "Already subscribed!"
    })


def newsletter_unsubscribe(request, token):
    try:
        subscriber = NewsletterSubscriber.objects.get(token=token)
        subscriber.delete()
        return HttpResponse("Unsubscribed Successfully")
    except:
        return HttpResponse("Invalid Link")

from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives


def send_custom_email(request, subscriber, subject, message):
    unsubscribe = request.build_absolute_uri(
        reverse("newsletter_unsubscribe", args=[subscriber.token])
    )

    html = render_to_string("emails/newsletter.html", {
        "email": subscriber.email,
        "message": message,
        "unsubscribe_link": unsubscribe,
    })

    email = EmailMultiAlternatives(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [subscriber.email],
    )

    email.attach_alternative(html, "text/html")

    try:
        success = send_email_with_fallback(
            subject,
            html,
            subscriber.email   # ✅ FIXED
        )
        print("✅ Newsletter email sent")

    except Exception as e:
        print("❌ EMAIL ERROR:", repr(e))

# <===============admin_dashboard================>
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from .models import Product, NewsletterSubscriber
from django.utils import timezone
from datetime import timedelta
from .models import Order

@staff_member_required
def admin_dashboard(request):

    total_users = User.objects.count()
    total_products = Product.objects.count()
    total_subscribers = NewsletterSubscriber.objects.count()

    today = timezone.now().date()

    daily_orders = Order.objects.filter(created_at__date=today).count()

    weekly_orders = Order.objects.filter(
        created_at__gte=today - timedelta(days=7)
    ).count()

    monthly_orders = Order.objects.filter(
        created_at__gte=today - timedelta(days=30)
    ).count()

    recent_orders = Order.objects.select_related("user").order_by("-created_at")[:5]

    context = {
        "total_users": total_users,
        "total_products": total_products,
        "total_subscribers": total_subscribers,
        "daily_orders": daily_orders,
        "weekly_orders": weekly_orders,
        "monthly_orders": monthly_orders,
        "recent_orders": recent_orders,
    }

    return render(request, "admin/admin_dashboard.html", context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from .models import Category, Product

# ================== CATEGORIES ADMIN ==================

@staff_member_required
def categories_admin(request):

    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            Category.objects.create(name=name)

    categories = Category.objects.prefetch_related("products")

    return render(request,"admin/categories_admin.html",{
        "categories":categories
    })


@staff_member_required
def delete_category(request,id):
    Category.objects.filter(id=id).delete()
    return redirect("categories_admin")


@staff_member_required
def inline_add_product(request, cat_id):

    if request.method == "POST":

        Product.objects.create(
            category_id=cat_id,
            name=request.POST["name"],
            image=request.FILES["image"]
        )

    return redirect("categories_admin")


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def products_admin(request):

    category_id = request.GET.get("category")

    categories = Category.objects.all()

    products = Product.objects.prefetch_related("variants", "category").all()

    if category_id:
        products = products.filter(category_id=category_id)

    return render(request, "admin/products_admin.html", {
        "products": products,
        "categories": categories,
        "active_category": category_id
    })

import json
from django.views.decorators.csrf import csrf_exempt

@staff_member_required
def create_category(request):
    import json
    data=json.loads(request.body)
    cat=Category.objects.create(name=data["name"])
    return JsonResponse({"id":cat.id,"name":cat.name})

@staff_member_required
def add_product(request):

    categories = Category.objects.all()

    if request.method == "POST":

        # ✅ GET IMAGE
        image = request.FILES.get("image")

        # 🚨 VALIDATION
        if not image:
            return render(request, "admin/add_product.html", {
                "categories": categories,
                "error": "Main image is required"
            })

        # ✅ CREATE PRODUCT
        product = Product.objects.create(
            category_id=request.POST.get("category"),
            name=request.POST.get("name"),
            description=request.POST.get("description", ""),
            image=image,
            highlights=request.POST.get("highlights", ""),
            shelf_life=request.POST.get("shelf_life", "")
        )

        # ================= VARIANTS =================
        sizes = request.POST.getlist("variant_size[]")
        mrps = request.POST.getlist("variant_mrp[]")
        prices = request.POST.getlist("variant_price[]")

        for i in range(len(sizes)):
            size = sizes[i].strip()
            price = prices[i]

            if size and price:
                ProductVariant.objects.create(
                    product=product,
                    size=size,
                    mrp=mrps[i] or 0,
                    price=price,
                    stock=50
                )

        # ================= GALLERY =================
        from .models import ProductImage

        gallery_files = request.FILES.getlist("gallery")

        for img in gallery_files:
            ProductImage.objects.create(
                product=product,
                image=img
            )

        return redirect("products_admin")

    return render(request, "admin/add_product.html", {
        "categories": categories
    })

@staff_member_required
def edit_product(request, id):

    product = get_object_or_404(Product, id=id)
    categories = Category.objects.all()

    if request.method == "POST":

        # BASIC INFO
        product.category_id = request.POST["category"]
        product.name = request.POST["name"]
        product.description = request.POST.get("description", "")
        product.highlights = request.POST.get("highlights", "")
        product.shelf_life = request.POST.get("shelf_life", "")

        # MAIN IMAGE
        if request.FILES.get("image"):
            product.image = request.FILES["image"]

        product.save()

        # ================= GALLERY =================
        from .models import ProductImage

        gallery_files = request.FILES.getlist("gallery")

        if gallery_files:
            product.images.all().delete()  # optional replace
            for img in gallery_files:
                ProductImage.objects.create(
                    product=product,
                    image=img
                )

        # ================= VARIANTS =================
        product.variants.all().delete()

        sizes = request.POST.getlist("variant_size[]")
        mrps = request.POST.getlist("variant_mrp[]")
        prices = request.POST.getlist("variant_price[]")

        for i in range(len(sizes)):
            size = sizes[i].strip()
            price = prices[i]

            if size and price:
                ProductVariant.objects.create(
                    product=product,
                    size=size,
                    mrp=mrps[i] or 0,
                    price=price,
                    stock=50
                )

        return redirect("products_admin")

    return render(request, "admin/edit_product.html", {
        "product": product,
        "categories": categories
    })

@staff_member_required
def delete_product(request,id):
    Product.objects.filter(id=id).delete()
    return redirect("products_admin")


# <=================== USER PRODUCTS ==================>

def products(request):
    products = Product.objects.prefetch_related("variants", "category")
    categories = Category.objects.all()
    cart = request.session.get("cart", {})

    return render(request, "products.html", {
        "products": products,
        "categories": categories,
        "cart": cart,
        "cart_count": get_cart_count(request),
        "active_category": "all"
    })

def products_by_category(request, slug):
    category = get_object_or_404(Category, slug=slug)

    products = Product.objects.filter(category=category)
    categories = Category.objects.all()
    cart = request.session.get("cart", {})

    return render(request, "products.html", {
        "products": products,
        "categories": categories,
        "cart": cart,
        "cart_count": get_cart_count(request),
        "active_category": category.slug
    })

from django.db.models import Avg, Count

def product_detail(request, id):
    product = get_object_or_404(Product.objects.prefetch_related("variants", "images", "reviews__user"), id=id)
    
    # Check if user has purchased this product
    has_purchased = False
    if request.user.is_authenticated:
        has_purchased = OrderItem.objects.filter(
            order__user=request.user, 
            product=product, 
            order__status="delivered"
        ).exists()

    # Handle Review Submission
    if request.method == "POST" and has_purchased:
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        Review.objects.create(product=product, user=request.user, rating=rating, comment=comment)
        return redirect('product_detail', id=product.id)

    stats = product.reviews.aggregate(avg=Avg('rating'), count=Count('id'))
    
    for v in product.variants.all():
        if v.mrp and v.price:
            v.discount_percent = int(((v.mrp - v.price) / v.mrp) * 100)
        else:
            v.discount_percent = 0

    return render(request, "product_detail.html", {
        "product": product,
        "avg_rating": stats['avg'] or 0,
        "total_reviews": stats['count'] or 0,
        "reviews": product.reviews.all(),
        "has_purchased": has_purchased,
        "cart": request.session.get("cart", {})
    })


import json
from django.http import JsonResponse
from .models import ProductVariant

def update_cart(request):
    if request.method == "POST":
        try:
            if request.content_type and "application/json" in request.content_type:
                data = json.loads(request.body)
            else:
                data = request.POST

            product_id = str(data.get("product_id"))
            variant_id = str(data.get("variant_id"))
            action = data.get("action")

            key = f"{product_id}_{variant_id}"
            cart = request.session.get("cart", {})

            if action == "add":
                variant = ProductVariant.objects.get(id=variant_id)
                product = variant.product

                if key in cart:
                    cart[key]["quantity"] += 1
                else:
                    cart[key] = {
                        "product_id": product_id,
                        "variant_id": variant_id,
                        "name": f"{product.name} ({variant.size})",
                        "price": float(variant.price),
                        "image": product.image.url if product.image else "",
                        "quantity": 1
                    }

            elif action == "increase":
                if key in cart:
                    cart[key]["quantity"] += 1

            elif action == "remove":
                if key in cart:
                    del cart[key]

            elif action == "decrease":
                if key in cart:
                    if cart[key]["quantity"] <= 1:
                        del cart[key]   # 🔥 FORCE REMOVE WHEN 1
                    else:
                        cart[key]["quantity"] -= 1

            request.session["cart"] = cart
            request.session.modified = True

            # ✅ RETURN FULL CART
            items = []
            total = 0

            for k, item in cart.items():
                subtotal = item["price"] * item["quantity"]
                total += subtotal

                items.append({
                    "id": k,
                    "product_id": item["product_id"],
                    "variant_id": item["variant_id"],
                    "name": item["name"],
                    "price": item["price"],
                    "quantity": item["quantity"],
                    "image": item["image"]
                })

            return JsonResponse({
                "items": items,
                "cart_count": sum(i["quantity"] for i in cart.values()),
                "total": total
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


import random

@login_required
def cart_view(request):

    cart = request.session.get("cart", {})

    total = 0

    for item in cart.values():
        price = Decimal(str(item.get("price", 0)))
        quantity = int(item.get("quantity", 0))

        item["subtotal"] = price * quantity
        total += item["subtotal"]

    coupon_discount = request.session.get("coupon_discount", 0)

    recommended = Product.objects.order_by("?")[:4]

    return render(request, "cart.html", {
        "cart": cart,
        "total": total,
        "coupon_discount": coupon_discount,
        "recommended": recommended
    })


def remove_from_cart(request, key):
    cart = request.session.get("cart", {})

    if key in cart:
        del cart[key]

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart")


def cart_json(request):
    cart = request.session.get("cart", {})

    items = []
    total = 0

    for key, item in cart.items():
        subtotal = item["price"] * item["quantity"]
        total += subtotal

        items.append({
            "id": key,
            "product_id": item["product_id"],   # ✅ ADD THIS
            "variant_id": item["variant_id"],   # ✅ ADD THIS
            "name": item["name"],
            "price": item["price"],
            "quantity": item["quantity"],
            "image": item["image"]
        })

    return JsonResponse({
        "items": items,
        "cart_count": sum(i["quantity"] for i in cart.values()),  # ✅ ADD
        "total": total
    })

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import UserProfile, Address, MobileNumber


# ================= PROFILE PAGE =================

@login_required
def profile(request):

    profile, created = UserProfile.objects.get_or_create(user=request.user)

    addresses = Address.objects.filter(user=request.user)
    mobiles = MobileNumber.objects.filter(user=request.user)

    primary_mobile_obj = mobiles.filter(is_primary=True).first()
    primary_mobile = primary_mobile_obj.mobile if primary_mobile_obj else ""

    cart = request.session.get("cart", {})
    cart_count = sum(i["quantity"] for i in cart.values())

    return render(request, "profile.html", {
        "profile": profile,
        "extra_addresses": addresses,
        "extra_mobiles": mobiles,
        "primary_mobile": primary_mobile,
        "cart_count": cart_count,
    })


# ================= UPDATE PROFILE =================

@login_required
def update_profile(request):

    if request.method == "POST":

        user = request.user

        user.first_name = request.POST.get("first_name", "")
        user.last_name = request.POST.get("last_name", "")
        user.email = request.POST.get("email", "")
        username = request.POST.get("username")

        if username and User.objects.exclude(id=user.id).filter(username=username).exists():
            return redirect("profile")

        user.username = username

        user.save()

        profile, created = UserProfile.objects.get_or_create(user=user)

        profile.gender = request.POST.get("gender")
        profile.date_of_birth = request.POST.get("date_of_birth") or None

        profile.save()

    return redirect("profile")


# ================= PROFILE PHOTO =================

@login_required
def update_profile_photo(request):

    if request.method == "POST":

        profile, created = UserProfile.objects.get_or_create(user=request.user)

        if "profile_photo" in request.FILES:
            profile.profile_photo = request.FILES["profile_photo"]
            profile.save()

    return redirect("profile")


# ================= ADD ADDRESS =================

@login_required
def add_extra_address(request):

    if request.method == "POST":

        label = request.POST.get("label")
        address = request.POST.get("address")

        if not address:
            return JsonResponse({"error": "Address required"})

        addr = Address.objects.create(
            user=request.user,
            label=label,
            address=address
        )

        return JsonResponse({
            "id": addr.id,
            "label": addr.label,
            "address": addr.address,
            "is_default": addr.is_default
        })

    return JsonResponse({"error": "Invalid request"})


# ================= DELETE ADDRESS =================

from django.views.decorators.http import require_POST

@login_required
@require_POST
def delete_extra_address(request, id):

    try:
        addr = Address.objects.get(id=id, user=request.user)

        if addr.is_default:
            return JsonResponse({"success": False, "error": "Cannot delete default address"})

        addr.delete()

        return JsonResponse({"success": True})

    except Address.DoesNotExist:
        return JsonResponse({"success": False})


# ================= MAKE DEFAULT ADDRESS =================

from django.views.decorators.http import require_POST

@login_required
@require_POST
def make_default_address(request, id):

    Address.objects.filter(user=request.user).update(is_default=False)

    addr = Address.objects.get(id=id, user=request.user)
    addr.is_default = True
    addr.save()

    return JsonResponse({"success": True})


@login_required
@require_POST
def edit_address(request, id):

    try:
        addr = Address.objects.get(id=id, user=request.user)

        addr.label = request.POST.get("label")
        addr.address = request.POST.get("address")

        addr.save()

        return JsonResponse({"success": True})

    except Address.DoesNotExist:
        return JsonResponse({"success": False})

# ================= ADD MOBILE =================

import re

@login_required
def add_extra_mobile(request):

    if request.method == "POST":

        mobile = request.POST.get("mobile")

        if not re.match(r"^[6-9]\d{9}$", mobile):
            return JsonResponse({"error": "Enter valid 10-digit mobile number"})

        is_first = not MobileNumber.objects.filter(user=request.user).exists()

        mob = MobileNumber.objects.create(
            user=request.user,
            mobile=mobile,
            is_primary=is_first
        )

        return JsonResponse({
            "id": mob.id,
            "mobile": mob.mobile,
            "is_primary": mob.is_primary
        })

    return JsonResponse({"error": "Invalid request"})


# ================= DELETE MOBILE =================

@login_required
@require_POST
def delete_extra_mobile(request, id):

    try:
        mob = MobileNumber.objects.get(id=id, user=request.user)

        if mob.is_primary:
            return JsonResponse({"success": False, "error": "Cannot delete primary mobile"})

        mob.delete()

        return JsonResponse({"success": True})

    except MobileNumber.DoesNotExist:
        return JsonResponse({"success": False})


# ================= MAKE PRIMARY MOBILE =================

@login_required
def make_primary_mobile(request, id):

    MobileNumber.objects.filter(user=request.user).update(is_primary=False)

    mob = MobileNumber.objects.get(id=id, user=request.user)
    mob.is_primary = True
    mob.save()

    return JsonResponse({"success": True})


# ================= PASSWORD VERIFY =================

@login_required
def verify_username_password(request):

    if request.method == "POST":

        password = request.POST.get("password")

        if request.user.check_password(password):
            return JsonResponse({"success": True})

        return JsonResponse({
            "success": False,
            "message": "Incorrect password"
        })

    return JsonResponse({"success": False})


@login_required
def verify_email_password(request):

    if request.method == "POST":

        password = request.POST.get("password")

        if request.user.check_password(password):
            return JsonResponse({"success": True})

        return JsonResponse({
            "success": False,
            "message": "Incorrect password"
        })

    return JsonResponse({"success": False})

from .models import Order

@login_required
def orders(request):

    orders = Order.objects.filter(
        user=request.user
    ).prefetch_related("items__product").order_by("-created_at")

    return render(request,"orders.html",{
        "orders":orders
    })


def get_cart_count(request):
    cart = request.session.get("cart")
    if not cart:
        return 0
    return sum(i["quantity"] for i in cart.values())

@login_required
def complete_profile(request):

    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":

        user = request.user

        # USER MODEL
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.save()

        # PROFILE MODEL
        profile.gender = request.POST.get("gender")
        profile.date_of_birth = request.POST.get("date_of_birth") or None
        profile.save()

        # MOBILE NUMBER
        mobile = request.POST.get("mobile")

        if mobile:
            MobileNumber.objects.get_or_create(
                user=user,
                mobile=mobile,
                defaults={"is_primary": True}
            )

        # ADDRESS
        address = request.POST.get("address")
        label = request.POST.get("label")

        if address:
            Address.objects.create(
                user=user,
                label=label,
                address=address,
                is_default=True
            )

        return redirect("profile")

    return render(request, "complete_profile.html")

from .models import Address, MobileNumber, Product
import random

@login_required
def checkout(request):

    cart = request.session.get("cart", {})

    if not cart:
        return redirect("cart")

    subtotal = sum(
    Decimal(str(item["price"])) * item["quantity"]
    for item in cart.values()
)

    gst = subtotal * Decimal("0.05")
    shipping = Decimal("40.00") if subtotal < Decimal("399") else Decimal("0.00")
    coupon_discount = Decimal(str(request.session.get("coupon_discount", 0)))

    final_total = subtotal + gst + shipping - coupon_discount

    # ✅ force 2 decimal places
    subtotal = subtotal.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
    gst = gst.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
    shipping = shipping.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
    coupon_discount = coupon_discount.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
    final_total = final_total.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)

    # Razorpay order
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    payment = client.order.create({
        "amount": int(final_total * 100),
        "currency": "INR",
        "payment_capture": 1
    })

    addresses = Address.objects.filter(user=request.user)

    # ⭐ Recommended products
    recommended_products = Product.objects.all()[:4]

    return render(request,"checkout.html",{
        "cart":cart,
        "subtotal":subtotal,
        "gst":gst,
        "shipping":shipping,
        "coupon_discount":coupon_discount,
        "final_total":final_total,
        "addresses":addresses,
        "recommended_products":recommended_products,   # ⭐ added
        "razorpay_order_id": payment["id"],
        "razorpay_key": settings.RAZORPAY_KEY_ID
    })

def send_order_email_async(order):
    send_order_email(order)


from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages


@login_required
@transaction.atomic
def place_order(request):

    if request.method != "POST":
        return redirect("cart")

    cart = request.session.get("cart", {})

    if not cart:
        messages.error(request, "Cart empty")
        return redirect("cart")

    address_id = request.POST.get("address_id")

    # ADDRESS
    if address_id:
        addr = Address.objects.get(id=address_id, user=request.user)
    else:
        street = request.POST.get("address")
        city = request.POST.get("city")
        pincode = request.POST.get("pincode")
        state = request.POST.get("state")

        full_address = f"{street}, {city}, {state} - {pincode}"

        addr = Address.objects.create(
            user=request.user,
            label="New Address",
            address=full_address
        )

    address = addr.address

    # TOTAL CALCULATION
    subtotal = sum(
        Decimal(str(item["price"])) * item["quantity"]
        for item in cart.values()
    )

    gst = subtotal * Decimal("0.05")
    shipping = Decimal("40.00") if subtotal < Decimal("399") else Decimal("0.00")
    coupon_discount = Decimal(str(request.session.get("coupon_discount", 0)))

    final_total = subtotal + gst + shipping - coupon_discount

    subtotal = subtotal.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
    gst = gst.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
    shipping = shipping.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
    coupon_discount = coupon_discount.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
    final_total = final_total.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)

    # PAYMENT DETECTION
    razorpay_payment_id = request.POST.get("razorpay_payment_id", "").strip()

    if razorpay_payment_id != "":
        payment_method = "UPI"
        payment_status = "Paid"
    else:
        payment_method = "COD"
        payment_status = "Pending"
        razorpay_payment_id = None

    # CREATE ORDER (ONLY ONCE)
    order = Order.objects.create(
        user=request.user,
        address=address,
        payment_method=payment_method,
        payment_status=payment_status,
        razorpay_payment_id=razorpay_payment_id,
        subtotal=subtotal,
        gst=gst,
        shipping_fee=shipping,
        coupon_discount=coupon_discount,
        total=final_total,
    )

    # ORDER ITEMS (FIXED FOR VARIANT CART)
    order_items = []

    for key, item in cart.items():

        product_id = item["product_id"]

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            continue

        variant = ProductVariant.objects.get(id=item["variant_id"])

        order_items.append(
            OrderItem(
                order=order,
                product=product,
                variant=variant,   # ✅ FIXED
                quantity=item["quantity"],
                price=item["price"]
            )
        )

    OrderItem.objects.bulk_create(order_items)

    print("Order placed successfully:", order.order_id)

    # AFTER ORDER CREATED
    def send_email_background(order_id):
        try:
            order = Order.objects.get(id=order_id)
            send_order_email(order)
        except Exception as e:
            print("❌ Background email failed:", e)


    # CALL THIS
    threading.Thread(
        target=send_email_background,
        args=(order.id,),
        daemon=True   # 🔥 VERY IMPORTANT
    ).start()


    # CLEAR CART
    request.session["cart"] = {}
    request.session["coupon_discount"] = 0
    request.session.modified = True

    return redirect("order_success", order_id=order.order_id)

from django.http import JsonResponse
from django.utils import timezone
from .models import Coupon
from django.views.decorators.http import require_POST

@require_POST
def apply_coupon(request):

    code = request.POST.get("code")

    try:
        coupon = Coupon.objects.get(code__iexact=code, is_active=True)

        today = timezone.now().date()

        if coupon.valid_from <= today <= coupon.valid_to:
            if "coupon_discount" in request.session:
                return JsonResponse({
                    "success": False,
                    "message": "Coupon already applied"
                })

            request.session["coupon_discount"] = coupon.discount_amount

            return JsonResponse({
                "success": True,
                "discount": coupon.discount_amount
            })

        else:
            return JsonResponse({
                "success": False,
                "message": "Coupon expired"
            })

    except Coupon.DoesNotExist:

        return JsonResponse({
            "success": False,
            "message": "Invalid coupon"
        })


from django.conf import settings
import os

def link_callback(uri, rel):

    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))

    elif uri.startswith(settings.STATIC_URL):
        path = os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))

    else:
        path = os.path.join(settings.BASE_DIR, uri)

    return path


import qrcode
import base64
from io import BytesIO
from decimal import Decimal
from num2words import num2words
from django.template.loader import get_template
from django.http import HttpResponse
from django.conf import settings
from xhtml2pdf import pisa
from django.contrib.auth.decorators import login_required
from .models import Order
import os


def image_to_base64(path):
    try:
        with open(path, "rb") as img:
            return base64.b64encode(img.read()).decode()
    except Exception as e:
        print("❌ Image load failed:", e)
        return ""


@login_required
def download_invoice(request, order_id):

    order = Order.objects.prefetch_related("items__product").get(
        order_id=order_id,
        user=request.user
    )

    items = order.items.all()

    subtotal = sum((i.price * i.quantity for i in items), Decimal("0"))
    gst = subtotal * Decimal("0.05")
    shipping = order.shipping_fee or Decimal("0")
    coupon = order.coupon_discount or Decimal("0")

    total = subtotal + gst + shipping - coupon


    subtotal = subtotal.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
    gst = gst.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
    shipping = shipping.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
    coupon = coupon.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
    total = total.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)

    rupees = int(total)
    paise = int(round((total - rupees) * 100))

    if paise > 0:
        amount_words = (
            num2words(rupees, lang="en_IN").title()
            + " Rupees And "
            + num2words(paise, lang="en_IN").title()
            + " Paise Only"
        )
    else:
        amount_words = num2words(rupees, lang="en_IN").title() + " Rupees Only"

    # -------- QR CODE --------

    qr = qrcode.make(f"https://subiofoods.com/order/{order.order_id}")

    buffer = BytesIO()
    qr.save(buffer, format="PNG")

    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    # -------- LOGO + SIGNATURE --------

    logo_file = os.path.join(settings.BASE_DIR, "products/static/images/icons/logo.png")
    signature_file = os.path.join(settings.BASE_DIR, "products/static/images/signature.png")

    logo_base64 = image_to_base64(logo_file)
    signature_base64 = image_to_base64(signature_file)

    # -------- RENDER TEMPLATE --------

    template = get_template("invoice.html")

    html = template.render({
        "order": order,
        "items": items,
        "subtotal": subtotal,
        "gst": gst,
        "shipping": shipping,
        "coupon": coupon,
        "total": total,
        "amount_words": amount_words,
        "qr_code": qr_base64,
        "logo_base64": logo_base64,
        "signature_base64": signature_base64
    })

    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = f'attachment; filename="SUBIO_{order.invoice_number}.pdf"'

    pisa.CreatePDF(html, dest=response)

    return response


def safe_image(path):
    try:
        with open(path, "rb") as img:
            return base64.b64encode(img.read()).decode()
    except Exception as e:
        print("❌ Image load failed:", e)
        return ""

logo_file = os.path.join(settings.BASE_DIR, "products/static/images/icons/logo.png")
signature_file = os.path.join(settings.BASE_DIR, "products/static/images/signature.png")

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from io import BytesIO
from xhtml2pdf import pisa

def send_order_email(order):
    try:
        print("🚀 Sending email to:", order.user.email)

        items = order.items.all()

        subtotal = sum((i.price * i.quantity for i in items), Decimal("0"))
        gst = subtotal * Decimal("0.05")
        shipping = order.shipping_fee or Decimal("0")
        coupon = order.coupon_discount or Decimal("0")
        total = subtotal + gst + shipping - coupon

        subtotal = subtotal.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
        gst = gst.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
        shipping = shipping.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
        coupon = coupon.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
        total = total.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)

        # ✅ AMOUNT IN WORDS
        rupees = int(total)
        paise = int(round((total - rupees) * 100))

        if paise > 0:
            amount_words = (
                num2words(rupees, lang="en_IN").title()
                + " Rupees And "
                + num2words(paise, lang="en_IN").title()
                + " Paise Only"
            )
        else:
            amount_words = num2words(rupees, lang="en_IN").title() + " Rupees Only"

        # -------- QR CODE --------
        qr = qrcode.make(f"https://subiofoods.com/order/{order.order_id}")
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        # -------- IMAGES --------
        def safe_image(path):
            try:
                with open(path, "rb") as img:
                    return base64.b64encode(img.read()).decode()
            except Exception as e:
                print("❌ Image load failed:", e)
                return ""

        logo_file = os.path.join(settings.BASE_DIR, "products/static/images/icons/logo.png")
        signature_file = os.path.join(settings.BASE_DIR, "products/static/images/signature.png")

        logo_base64 = safe_image(logo_file)
        signature_base64 = safe_image(signature_file)

                # -------- GENERATE PDF --------
        template = get_template("invoice.html")

        html_pdf = template.render({
            "order": order,
            "items": items,
            "subtotal": subtotal,
            "gst": gst,
            "shipping": shipping,
            "coupon": coupon,
            "total": total,
            "amount_words": amount_words,
            "qr_code": qr_base64,
            "logo_base64": logo_base64,
            "signature_base64": signature_base64
        })

        if len(items) > 15:
            print("⚠️ Skipping PDF (too many items)")
            pdf_bytes = None
        else:
            pdf_buffer = BytesIO()
            pisa.CreatePDF(html_pdf, dest=pdf_buffer)
            pdf_buffer.seek(0)
            pdf_bytes = pdf_buffer.read()

        # -------- GENERATE PDF --------
        template = get_template("invoice.html")

        html_pdf = template.render({
            "order": order,
            "items": items,
            "subtotal": subtotal,
            "gst": gst,
            "shipping": shipping,
            "coupon": coupon,
            "total": total,
            "amount_words": amount_words,   # ✅ FIX
            "qr_code": qr_base64,           # ✅ FIX
            "logo_base64": logo_base64,     # ✅ FIX
            "signature_base64": signature_base64  # ✅ FIX
        })

        pdf_buffer = BytesIO()
        pisa.CreatePDF(html_pdf, dest=pdf_buffer)
        pdf_buffer.seek(0)

        pdf_bytes = pdf_buffer.read()

        # -------- EMAIL HTML --------
        html_message = render_to_string("emails/order_confirmation.html", {
            "order": order,
            "total": total
        })

        subject = f"Your Subio Order #{order.order_id} Confirmation"

        # -------- SEND EMAIL --------
        success = send_email_with_fallback(
            subject,
            html_message,
            order.user.email,
            pdf_bytes=pdf_bytes,
            filename=f"SUBIO_{order.invoice_number}.pdf"
        )

        if success:
            print("✅ Customer email sent")
        else:
            print("❌ Email sending failed completely")

        # -------- ADMIN EMAIL --------
        admin_email = EmailMessage(
            f"New Order #{order.order_id}",
            f"Order ID: {order.order_id}\n Customer: {order.user.username}\n Email: {order.user.email}\n Total: ₹{total}",
            settings.DEFAULT_FROM_EMAIL,
            [settings.EMAIL_HOST_USER],
        )
        admin_email.send(fail_silently=True)

        print("✅ Admin email sent")

        order.email_sent = success
        order.save(update_fields=["email_sent"])

    except Exception as e:
        print("❌ EMAIL ERROR:", repr(e))
        order.email_sent = False
        order.save(update_fields=["email_sent"])

@login_required
def order_detail(request, order_id):
    order = Order.objects.get(order_id=order_id, user=request.user)
    return render(request, "order_detail.html", {"order": order})

@login_required
def cancel_order(request, order_id):

    order = Order.objects.get(order_id=order_id, user=request.user)

    if order.status in ["pending","processing"]:
        order.status = "cancelled"
        order.save()

    return redirect("order_detail", order_id=order_id)

def track_order(request, order_id):

    order = Order.objects.get(order_id=order_id)

    return render(request,"track_order.html",{"order":order})

from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_orders(request):

    orders = Order.objects.select_related("user").order_by("-created_at")

    return render(request,"admin/orders_admin.html",{
        "orders":orders
    })

@staff_member_required
def admin_order_detail(request, order_id):

    order = Order.objects.prefetch_related("items__product").get(order_id=order_id)

    if request.method == "POST":

        order.status = request.POST.get("status")
        order.courier_name = request.POST.get("courier_name")
        order.tracking_number = request.POST.get("tracking_number")

        order.save()

        return redirect("admin_order_detail",order_id=order_id)

    return render(request,"admin/order_detail_admin.html",{
        "order":order
    })

from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from .models import Order


def dashboard_stats(request):

    today = timezone.now().date()

    daily_orders = Order.objects.filter(created_at__date=today).count()

    weekly_orders = Order.objects.filter(
        created_at__gte=today - timedelta(days=7)
    ).count()

    monthly_orders = Order.objects.filter(
        created_at__gte=today - timedelta(days=30)
    ).count()

    total_revenue = Order.objects.filter(
        status="delivered"
    ).aggregate(total=Sum("total"))["total"] or 0

    today_revenue = Order.objects.filter(
        created_at__date=today,
        status="delivered"
    ).aggregate(total=Sum("total"))["total"] or 0

    recent_orders = list(
        Order.objects.select_related("user")
        .order_by("-created_at")[:6]
        .values(
            "order_id",
            "user__username",
            "total",
            "status",
        )
    )

    return JsonResponse({
        "daily_orders": daily_orders,
        "weekly_orders": weekly_orders,
        "monthly_orders": monthly_orders,
        "total_revenue": total_revenue,
        "today_revenue": today_revenue,
        "recent_orders": recent_orders
    })

from django.core.mail import EmailMessage
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def send_email_with_fallback(subject, html_message, to_email, pdf_bytes=None, filename=None):

    # -------- TRY ZOHO --------
    try:
        email = EmailMessage(
            subject,
            html_message,
            settings.DEFAULT_FROM_EMAIL,
            [to_email],
        )

        email.content_subtype = "html"   # ✅ FIX HTML

        # Attach PDF if exists
        if pdf_bytes and filename:
            email.attach(filename, pdf_bytes, "application/pdf")

        email.send(fail_silently=True)

        print("✅ Sent via Zoho SMTP")
        return True

    except Exception as e:
        print("❌ Zoho failed:", e)

    # -------- FALLBACK SENDGRID --------
    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)

        mail = Mail(
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_emails=to_email,
            subject=subject,
            html_content=html_message,
        )

        # Attach PDF in SendGrid
        if pdf_bytes and filename:
            import base64
            from sendgrid.helpers.mail import Attachment, FileContent, FileName, FileType, Disposition

            encoded = base64.b64encode(pdf_bytes).decode()

            attachment = Attachment(
                FileContent(encoded),
                FileName(filename),
                FileType("application/pdf"),
                Disposition("attachment")
            )

            mail.attachment = attachment

        sg.send(mail)

        print("✅ Sent via SendGrid")
        return True

    except Exception as e:
        print("❌ SendGrid failed:", e)

    return False

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, Review, OrderItem

@login_required
def add_review(request, product_id):
    if request.method == "POST":
        product = get_object_or_404(Product, id=product_id)
        
        # Security check: Ensure they actually bought it (matches your detail view logic)
        has_purchased = OrderItem.objects.filter(
            order__user=request.user, 
            product=product, 
            order__status="delivered"
        ).exists()

        if has_purchased:
            rating = request.POST.get('rating')
            comment = request.POST.get('comment')
            if rating and comment:
                Review.objects.create(
                    product=product, 
                    user=request.user, 
                    rating=rating, 
                    comment=comment
                )
        
        return redirect('product_detail', id=product_id)
    
    return redirect('products')