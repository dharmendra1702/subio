from django.urls import path
from . import views

urlpatterns = [

    # ================= HOME =================
    path("", views.home, name="home"),

    # ================= AUTH =================
    path("login/", views.login_page, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # ================= PROFILE =================
    path("profile/", views.profile, name="profile"),
    path("complete-profile/", views.complete_profile, name="complete_profile"),
    path("update-profile/", views.update_profile, name="update_profile"),
    path("update-photo/", views.update_profile_photo, name="update_profile_photo"),
    path("verify-username-password/", views.verify_username_password, name="verify_username_password"),
    path("verify-email-password/", views.verify_email_password, name="verify_email_password"),

    # ================= ADDRESS =================
    path("add-address/", views.add_extra_address, name="add_extra_address"),
    path("delete-address/<int:id>/", views.delete_extra_address, name="delete_extra_address"),
    path("make-default-address/<int:id>/", views.make_default_address, name="make_default_address"),

    # ================= MOBILE =================
    path("add-mobile/", views.add_extra_mobile, name="add_extra_mobile"),
    path("delete-mobile/<int:id>/", views.delete_extra_mobile, name="delete_extra_mobile"),
    path("make-primary-mobile/<int:id>/", views.make_primary_mobile, name="make_primary_mobile"),

    # ================= PRODUCTS =================
    path("products/", views.products, name="products"),
    path("products/<slug:slug>/", views.products_by_category, name="products_by_category"),
    path("product/<int:id>/", views.product_detail, name="product_detail"),

    # ================= CART =================
    path("cart/", views.cart_view, name="cart"),
    path("remove/<int:product_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("update-cart/", views.update_cart, name="update_cart"),

    path("cart-json/", views.cart_json, name="cart_json"),
    path("checkout/", views.checkout, name="checkout"),
    # ================= ORDERS =================
    path("orders/", views.orders, name="orders"),
    path("place-order/", views.place_order, name="place_order"),
    path("apply-coupon/", views.apply_coupon, name="apply_coupon"),
    path("edit-address/<int:id>/", views.edit_address, name="edit_address"),
    path("delete-extra-address/<int:id>/", views.delete_extra_address),
    path("add-extra-address/", views.add_extra_address),
    path("order-success/<str:order_id>/", views.order_success, name="order_success"),
    path("invoice/<str:order_id>/", views.download_invoice, name="download_invoice"),
    # ================= NEWSLETTER =================
    path("newsletter/", views.newsletter_subscribe, name="newsletter"),
    path("newsletter/unsubscribe/<uuid:token>/", views.newsletter_unsubscribe, name="newsletter_unsubscribe"),

    # ================= ADMIN DASHBOARD =================
    path("dashboard/", views.admin_dashboard, name="admin_dashboard"),

    # ================= ADMIN PRODUCTS =================
    path("products-admin/", views.products_admin, name="products_admin"),
    path("product/add/", views.add_product, name="add_product"),
    path("product/edit/<int:id>/", views.edit_product, name="edit_product"),
    path("product/delete/<int:id>/", views.delete_product, name="delete_product"),

    # ================= ADMIN CATEGORIES =================
    path("categories-admin/", views.categories_admin, name="categories_admin"),
    path("delete-category/<int:id>/", views.delete_category, name="delete_category"),
    path("inline-add-product/<int:cat_id>/", views.inline_add_product, name="inline_add_product"),
    path("create-category/", views.create_category, name="create_category"),
]