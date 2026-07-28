from django.urls import path

from . import views

app_name = "store"

urlpatterns = [
    path("", views.home, name="home"),
    path("medicines/", views.medicine_list, name="medicine_list"),
    path("medicine/<slug:slug>/", views.medicine_detail, name="medicine_detail"),

    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<int:medicine_id>/", views.cart_add, name="cart_add"),
    path("cart/update/<int:medicine_id>/", views.cart_update, name="cart_update"),
    path("cart/remove/<int:medicine_id>/", views.cart_remove, name="cart_remove"),

    path("checkout/", views.checkout, name="checkout"),
    path("orders/", views.order_history, name="order_history"),
    path("orders/<str:order_number>/", views.order_detail, name="order_detail"),
    path("orders/<str:order_number>/cancel/", views.order_cancel, name="order_cancel"),

    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),

    path("dashboard/", views.dashboard_home, name="dashboard_home"),
    path("dashboard/medicines/", views.dashboard_medicines, name="dashboard_medicines"),
    path("dashboard/medicines/add/", views.dashboard_medicine_form, name="dashboard_medicine_add"),
    path("dashboard/medicines/<int:pk>/edit/", views.dashboard_medicine_form, name="dashboard_medicine_edit"),
    path("dashboard/medicines/<int:pk>/delete/", views.dashboard_medicine_delete, name="dashboard_medicine_delete"),
    path("dashboard/categories/", views.dashboard_categories, name="dashboard_categories"),
    path("dashboard/orders/", views.dashboard_orders, name="dashboard_orders"),
    path("dashboard/orders/<str:order_number>/status/", views.dashboard_order_update_status, name="dashboard_order_update_status"),
    path("dashboard/messages/", views.dashboard_messages, name="dashboard_messages"),
]
