from django.contrib import admin
from .models import UserDetail, Restaurant, Menu, Category, MenuItem, Table, Order, OrderItem

@admin.register(UserDetail)
class UserDetailAdmin(admin.ModelAdmin):
    list_display = ('user', 'firstname', 'surname', 'role', 'mobileno')
    search_fields = ('user__username', 'firstname', 'surname')
    list_filter = ('role',)
    
@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'total_table', 'created_at')
    search_fields = ('name', 'address')
    list_filter = ('owner',)

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'is_published', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('restaurant', 'is_published')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'menu')
    search_fields = ('name',)
    list_filter = ('menu',)

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price')
    search_fields = ('name', 'description')
    list_filter = ('category',)

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('table_number', 'restaurant', 'is_active')
    search_fields = ('table_number', 'qr_code')
    list_filter = ('restaurant', 'is_active')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'table', 'status', 'is_complete', 'created_at')
    search_fields = ('customer_name', 'phone_number')
    list_filter = ('status', 'is_complete', 'table')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'menu_item', 'quantity', 'price')
    search_fields = ('menu_item__name',)
    list_filter = ('menu_item',)