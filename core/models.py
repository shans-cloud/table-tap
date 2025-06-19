import uuid
import os
from django.db import models
from django.contrib.auth.models import User


class UserDetail(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    firstname = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    role = models.CharField(
        max_length=10,
        choices=[("OWNER", "Owner"), ("STAFF", "Staff"), ("ADMIN", "Admin")],
    )
    mobileno = models.CharField(max_length=15, blank=True, null=True)
    is_archived = models.BooleanField(default=False)

    def is_complete(self):
        return bool(self.firstname and self.surname and self.mobileno)

    def __str__(self):
        return f"Details for {self.user.username}: {self.firstname} {self.surname} ({self.role})"


class Restaurant(models.Model):
    """Restaurant in the system."""

    owner = models.ForeignKey(
        UserDetail, on_delete=models.SET_NULL, null=True, blank=True
    )
    name = models.CharField(max_length=255)
    address = models.TextField()
    latitude = models.DecimalField(max_digits=22, decimal_places=16)
    longitude = models.DecimalField(max_digits=22, decimal_places=16)
    total_table = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


# Create your models here.
class Menu(models.Model):
    """Menus for restaurants (e.g. Breakfast, Lunch, Dinner)."""

    name = models.CharField(max_length=255)
    description = models.TextField(
        blank=True, default="A variety of dishes for every taste."
    )
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name="menus"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)

    def publish(self):
        self.is_published = True
        self.save()

    def unpublish(self):
        self.is_published = False
        self.save()

    def __str__(self):
        return f"{self.name}"


class Category(models.Model):
    """Categories of menu items (e.g. Main, Desserts)"""

    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} - {self.menu.name}"


class MenuItem(models.Model):
    """Individual menu items."""

    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="items"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.name} (${self.price})"


class Table(models.Model):
    """Physical tables at a restaurant, each with a QR code."""

    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name="tables"
    )
    table_number = models.IntegerField()
    qr_code = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Table {self.table_number} at {self.restaurant.name}"


class Order(models.Model):
    """Customer orders placed from a table."""

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PREPARING", "Preparing"),
        ("SERVED", "Served"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    customer_name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)
    is_complete = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")

    def get_total(self):
        return sum(item.price * item.quantity for item in self.order_items.all())

    def __str__(self):
        return f"Order #{self.id} [{self.get_status_display()}] from Table {self.table.table_number}"


class OrderItem(models.Model):
    """Items in an order with quantity and price snapshot."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_items"
    )
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} × {self.menu_item.name} (Order #{self.order.id})"
