from itertools import product

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse

def home(request):
    return render(request, "home.html")


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

            login(request, user)  # auto login after signup
            return redirect("/")

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

@login_required(login_url="/login/")
def cart(request):
    return render(request, "cart.html")


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

# <===================user products==================>
def products(request):
    products = Product.objects.all()
    categories = Category.objects.all()

    return render(request, "products.html", {
        "products": products,
        "categories": categories
    })


def product_detail(request,id):
    product=get_object_or_404(Product,id=id)
    return render(request,"product_detail.html",{"product":product})

