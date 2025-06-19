from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import (
    ManageSubscribersView,
    SubscriberCreateView,
    SubscriberUpdateView,
    SubscriberArchiveView,
    UserDetailViewSet,
    RestaurantViewSet,
    MenuViewSet,
    CategoryViewSet,
    MenuItemViewSet,
    TableViewSet, 
    OrderViewSet,
    OrderItemViewSet,
)

router = DefaultRouter()
router.register(r'user-details', UserDetailViewSet)
router.register(r'restaurants', RestaurantViewSet)
router.register(r'menus', MenuViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'menu-items', MenuItemViewSet)
router.register(r'tables', TableViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'order-items', OrderItemViewSet)

urlpatterns = [
    # Landing
    path("", views.home, name="index"),
    path("api/", include(router.urls)), 
    path("home/", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("manage/", views.ManageSubscribersView.as_view(), name="manage"),
    path("manage/add/", SubscriberCreateView.as_view(), name="subscriber_add"),
    path("manage/edit/<int:pk>/", SubscriberUpdateView.as_view(), name="subscriber_edit"),
    path("manage/archive/<int:pk>/", SubscriberArchiveView.as_view(), name="subscriber_archive"),

    # Restaurant
    path("restaurant/<int:restaurant_id>/", views.restaurant_dashboard, name="restaurant_dashboard"),
    # Menu
    path("restaurant/<int:restaurant_id>/menu/", views.menu_list, name="menu_list"),
    path("restaurant/<int:restaurant_id>/menu/<int:menu_id>/", views.menu_detail, name="menu_detail"),
    path("restaurant/<int:restaurant_id>/tables/init/", views.initialise_tables, name="initialise_tables"),
    path("restaurant/<int:restaurant_id>/tables/", views.table_list, name="table_list"),
    path("generate-qr/<int:restaurant_id>/<int:table_id>/", views.qr_code_view, name="generate_qr"),
    path("qr/restaurant/<int:restaurant_id>/table/<int:table_id>/", views.table_qr_redirect_view, name="table_qr_redirect"),
    path("qr/restaurant/<int:restaurant_id>/table/<int:table_id>/menu/<int:menu_id>/", views.customer_menu_detail_view, name="customer_menu_detail"),
    path("qr/restaurant/<int:restaurant_id>/table/<int:table_id>/order/<int:order_id>/", views.customer_cart, name="customer_cart"),
    path("restaurant/<int:restaurant_id>/orders/", views.orders_view, name="orders"),
]