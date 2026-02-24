from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_page, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("cart/", views.cart, name="cart"),
    path("newsletter/", views.newsletter_subscribe, name="newsletter"),
    path("newsletter/unsubscribe/<uuid:token>/", views.newsletter_unsubscribe, name="newsletter_unsubscribe"),
    path("dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("products-admin/", views.products_admin, name="products_admin"),
    path("product/add/", views.add_product, name="add_product"),
    path("product/edit/<int:id>/", views.edit_product, name="edit_product"),
    path("product/delete/<int:id>/", views.delete_product, name="delete_product"),
    path("product/<int:id>/",views.product_detail,name="product_detail"),
    path("products/", views.products, name="products"),
    path("categories-admin/", views.categories_admin, name="categories_admin"),
    path("delete-category/<int:id>/", views.delete_category, name="delete_category"),
    path("inline-add-product/<int:cat_id>/", views.inline_add_product, name="inline_add_product"),
    path("create-category/",views.create_category,name="create_category"),
]
