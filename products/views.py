from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from urllib3 import request
import razorpay
from django.conf import settings

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
    email.send()

# <===============admin_dashboard================>
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from .models import Product, NewsletterSubscriber

@staff_member_required
def admin_dashboard(request):

    total_users = User.objects.count()
    total_products = Product.objects.count()
    total_subscribers = NewsletterSubscriber.objects.count()

    context = {
        "total_users": total_users,
        "total_products": total_products,
        "total_subscribers": total_subscribers,
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

    categories = Category.objects.prefetch_related("product_set")

    return render(request,"admin/categories_admin.html",{
        "categories":categories
    })


@staff_member_required
def delete_category(request,id):
    Category.objects.filter(id=id).delete()
    return redirect("categories_admin")


@staff_member_required
def inline_add_product(request,cat_id):

    if request.method == "POST":

        Product.objects.create(
            category_id=cat_id,
            name=request.POST["name"],
            price=request.POST["price"],
            image=request.FILES["image"]
        )

    return redirect("categories_admin")


from django.shortcuts import render, redirect, get_object_or_404
from .models import Product
from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def products_admin(request):

    category_id = request.GET.get("category")

    categories = Category.objects.all()

    products = Product.objects.all()

    if category_id:
        products = products.filter(category_id=category_id)

    return render(request,"admin/products_admin.html",{
        "products":products,
        "categories":categories,
        "active_category":category_id
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

        image = request.FILES.get("image")

        if not image:
            return render(request,"admin/add_product.html",{
                "categories":categories,
                "error":"Please upload image"
            })

        # ✅ SAVE PRODUCT FIRST
        product = Product.objects.create(
            category_id=request.POST["category"],
            name=request.POST["name"],
            description=request.POST.get("description",""),
            price=request.POST["price"],
            stock=request.POST["stock"],
            image=image,

            highlights=request.POST.get("highlights",""),
            brand=request.POST.get("brand",""),
            shelf_life=request.POST.get("shelf_life",""),
            net_weight=request.POST.get("net_weight",""),
            gst_percentage=request.POST.get("gst_percentage",0),

            meta_title=request.POST.get("meta_title",""),
            meta_description=request.POST.get("meta_description","")
        )

        # ✅ SAVE GALLERY IMAGES
        gallery_files = request.FILES.getlist("gallery")

        for img in gallery_files:
            ProductImage.objects.create(product=product, image=img)

        return redirect("products_admin")

    return render(request,"admin/add_product.html",{"categories":categories})

@staff_member_required
def edit_product(request,id):

    product = get_object_or_404(Product,id=id)
    categories = Category.objects.all()

    if request.method == "POST":

        product.category_id = request.POST["category"]
        product.name = request.POST["name"]
        product.description = request.POST.get("description","")
        product.price = request.POST["price"]
        product.stock = request.POST["stock"]

        # EXTRA FIELDS
        product.highlights = request.POST.get("highlights","")
        product.brand = request.POST.get("brand","")
        product.net_weight = request.POST.get("net_weight","")
        product.shelf_life = request.POST.get("shelf_life","")
        product.gst_percentage = request.POST.get("gst_percentage",0)

        product.meta_title = request.POST.get("meta_title","")
        product.meta_description = request.POST.get("meta_description","")

        if request.FILES.get("image"):
            product.image = request.FILES["image"]

        product.save()

        return redirect("products_admin")

    return render(request,"admin/edit_product.html",{
        "product":product,
        "categories":categories
    })


@staff_member_required
def delete_product(request,id):
    Product.objects.filter(id=id).delete()
    return redirect("products_admin")

def inline_add_product(request,cat_id):
    Product.objects.create(
        category_id=cat_id,
        name=request.POST["name"],
        price=request.POST["price"],
        image=request.FILES["image"]
    )
    return redirect("categories_admin")


# <=================== USER PRODUCTS ==================>

def products(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    cart = request.session.get("cart", {})

    return render(request, "products.html", {
        "products": products,
        "categories": categories,
        "cart": cart,
        "cart_count": get_cart_count(request),
        "active_category": "all"   # 👈 important
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

def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    cart = request.session.get("cart", {})

    return render(request, "product_detail.html", {
        "product": product,
        "cart": cart
    })


@require_POST
def update_cart(request):

    product_id = str(request.POST.get("product_id"))
    action = request.POST.get("action")

    product = get_object_or_404(Product, id=product_id)

    cart = request.session.get("cart", {})

    if action == "add":
        cart.setdefault(product_id,{
            "name": product.name,
            "price": float(product.price),
            "image": product.image.url if product.image else "",
            "quantity":0
        })
        cart[product_id]["quantity"] += 1

    elif action == "increase":
        if product_id in cart:
            cart[product_id]["quantity"] += 1

    elif action == "decrease":
        if product_id in cart:
            cart[product_id]["quantity"] -= 1
            if cart[product_id]["quantity"] <= 0:
                del cart[product_id]

    request.session["cart"] = cart
    request.session.modified = True

    return JsonResponse({"status":"ok"})

import random
from .models import Product

@login_required
def cart_view(request):

    cart = request.session.get("cart", {})

    total = sum(item["price"] * item["quantity"] for item in cart.values())

    coupon_discount = request.session.get("coupon_discount", 0)

    products = list(Product.objects.all())
    random.shuffle(products)

    recommended = products[:4]

    return render(request, "cart.html", {
        "cart": cart,
        "total": total,
        "coupon_discount": coupon_discount,
        "recommended": recommended
    })


def remove_from_cart(request, product_id):
    cart = request.session.get("cart", {})

    if str(product_id) in cart:
        del cart[str(product_id)]

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart")


def cart_json(request):

    cart=request.session.get("cart",{})

    items=[]
    total=0

    for key,item in cart.items():

        subtotal=item["price"]*item["quantity"]

        items.append({
            "id":key,
            "name":item["name"],
            "price":item["price"],
            "quantity":item["quantity"],
            "image":item["image"]
        })

        total+=subtotal

    return JsonResponse({
        "items":items,
        "total":total
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

    primary_mobile = mobiles.filter(is_primary=True).first()
    primary_mobile = primary_mobile.mobile if primary_mobile else ""

    return render(request, "profile.html", {
        "profile": profile,
        "extra_addresses": addresses,
        "extra_mobiles": mobiles,
        "primary_mobile": primary_mobile,
        "user": request.user
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
    cart = request.session.get("cart", {})
    return sum(item["quantity"] for item in cart.values())

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

from .models import Address, MobileNumber
@login_required
def checkout(request):

    cart = request.session.get("cart", {})

    subtotal = sum(item["price"] * item["quantity"] for item in cart.values())

    gst = subtotal * 0.05
    shipping = 40 if subtotal < 399 else 0
    coupon_discount = request.session.get("coupon_discount", 0)

    final_total = subtotal + gst + shipping - coupon_discount

    # Razorpay order
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    payment = client.order.create({
        "amount": int(final_total * 100),  # Razorpay takes paise
        "currency": "INR",
        "payment_capture": 1
    })

    addresses = Address.objects.filter(user=request.user)

    return render(request,"checkout.html",{
        "cart":cart,
        "subtotal":subtotal,
        "gst":gst,
        "shipping":shipping,
        "coupon_discount":coupon_discount,
        "final_total":final_total,
        "addresses":addresses,
        "razorpay_order_id": payment["id"],
        "razorpay_key": settings.RAZORPAY_KEY_ID
    })

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Order, OrderItem, Product

@login_required
def place_order(request):

    if request.method == "POST":

        payment = request.POST.get("payment")
        address_id = request.POST.get("address_id")

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

        cart = request.session.get("cart", {})

        if not cart:
            messages.error(request, "Cart empty")
            return redirect("cart")

        subtotal = sum(item["price"] * item["quantity"] for item in cart.values())

        gst = subtotal * 0.05
        shipping = 40 if subtotal < 399 else 0
        coupon_discount = request.session.get("coupon_discount", 0)

        final_total = subtotal + gst + shipping - coupon_discount

        # CREATE ORDER
        order = Order.objects.create(
            user=request.user,
            address=address,
            payment_method=payment,
            total=final_total
        )

        # SAVE ORDER ITEMS
        for key, item in cart.items():

            product = Product.objects.get(id=key)

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item["quantity"],
                price=item["price"]
            )

        # CLEAR CART + COUPON
        request.session["cart"] = {}
        request.session.pop("coupon_discount", None)
        request.session.modified = True

        return redirect("orders")

    return redirect("cart")

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

