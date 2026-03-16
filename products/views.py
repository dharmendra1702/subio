import uuid
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
import razorpay
from django.conf import settings
from .models import Category
from decimal import ROUND_HALF_UP, Decimal
import os
from .models import Order, OrderItem, Product, Address

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
        "items": order.items.all()
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

    categories = Category.objects.prefetch_related("products")

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

@login_required
def cart_view(request):

    cart = request.session.get("cart", {})

    total = 0

    for item in cart.values():

        price = Decimal(str(item["price"]))
        quantity = int(item["quantity"])

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

    # ORDER ITEMS
    product_ids = cart.keys()
    products = Product.objects.filter(id__in=product_ids).in_bulk()

    order_items = []

    for pid, item in cart.items():
        product = products.get(int(pid))
        if not product:
            continue

        order_items.append(
            OrderItem(
                order=order,
                product=product,
                quantity=item["quantity"],
                price=item["price"]
            )
        )

    OrderItem.objects.bulk_create(order_items)

    print("Order placed successfully:", order.order_id)
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
    with open(path, "rb") as img:
        return base64.b64encode(img.read()).decode()


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

    amount_words = num2words(total, lang="en_IN").title() + " Rupees Only"

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

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from io import BytesIO
from xhtml2pdf import pisa


def send_order_email(request, order):

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

    amount_words = num2words(total, lang="en_IN").title() + " Rupees Only"

    # -------- QR CODE --------
    qr = qrcode.make(f"https://subiofoods.com/order/{order.order_id}")
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    logo_file = os.path.join(settings.BASE_DIR, "products/static/images/icons/logo.png")
    signature_file = os.path.join(settings.BASE_DIR, "products/static/images/signature.png")

    logo_base64 = image_to_base64(logo_file)
    signature_base64 = image_to_base64(signature_file)

    # -------- GENERATE PDF --------

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

    pdf_buffer = BytesIO()
    pisa.CreatePDF(html, dest=pdf_buffer)

    pdf_buffer.seek(0)

    # -------- CUSTOMER EMAIL --------

    subject = f"Your Subio Order #{order.order_id} Confirmation"

    message = render_to_string("emails/order_confirmation.html", {
        "order": order,
        "total": total
    })

    email = EmailMessage(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [order.user.email],
    )

    email.content_subtype = "html"

    email.attach(
        f"SUBIO_{order.invoice_number}.pdf",
        pdf_buffer.read(),
        "application/pdf"
    )

    email.send()

    # -------- ADMIN EMAIL --------

    admin_subject = f"New Order Received #{order.order_id}"

    admin_message = f"""
    New order received!

    Order ID: {order.order_id}
    Customer: {order.user.username}
    Email: {order.user.email}
    Total: ₹{total}
    """

    admin_email = EmailMessage(
        admin_subject,
        admin_message,
        settings.DEFAULT_FROM_EMAIL,
        [settings.EMAIL_HOST_USER],
    )

    admin_email.send()