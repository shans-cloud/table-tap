import qrcode
from io import BytesIO
from django.core.files import File
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages 
from django.db.models import Q, Sum, F
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.response import Response
from core.models import (
    UserDetail, 
    Restaurant, 
    Order, 
    Menu, 
    Category, 
    MenuItem,
    Table,
    Order,
    OrderItem,
)
from .forms import UserDetailFullForm
from .serializers import (
    UserDetailSerializer,
    RestaurantSerializer, 
    MenuSerializer, 
    CategorySerializer, 
    MenuItemSerializer, 
    TableSerializer, 
    OrderSerializer, 
    OrderItemSerializer,
)

def landing_page(request):
    return render(request, "landing.html")

def about(request):
    return render(request, "about.html")

def home(request):
    # If the user is not authenticated then show the landing
    if not request.user.is_authenticated:
        return render(request, "landing.html")

    # Authenticated user
    user_details, created = UserDetail.objects.get_or_create(
        user=request.user,
        defaults={
            "firstname": request.user.first_name or "NoFirstName",
            "surname": request.user.last_name or "NoSurname",
            "mobileno": "0400000000",  # Default mobile number
        }
    )

    restaurants = Restaurant.objects.filter(owner=user_details)

    context = {
        "user_details": user_details,
        "username": user_details.user.username,
        "name": f"{user_details.firstname} {user_details.surname}",
        "mobileno": user_details.mobileno,
        "restaurants": restaurants,
    }
    return render(request, "home.html", context)

@login_required
def restaurant_dashboard(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    total_menus = Menu.objects.filter(restaurant=restaurant).count()
    total_orders = Order.objects.filter(table__restaurant=restaurant).count()

    context = {
        "restaurant": restaurant,
        "total_menus": total_menus,
        "total_orders": total_orders,
    }
    return render(request, "restaurant.html", context)

@login_required
def menu_list(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    menus = Menu.objects.filter(restaurant=restaurant)
    context = {
        "restaurant": restaurant,
        "menus": menus
    }
    return render(request, "menu_list.html", context)

@login_required
def menu_detail(request, restaurant_id, menu_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    menu = get_object_or_404(Menu, id=menu_id, restaurant=restaurant)
    categories = Category.objects.filter(menu=menu)
    return render(request, "menu_detail.html", {
        "restaurant": restaurant, 
        "menu": menu,
        "categories": categories,
    })

# A class-based view to manage and display a paginated list of subscribers
@method_decorator(user_passes_test(lambda u: u.is_staff), name='dispatch')
class ManageSubscribersView(ListView):
    model = UserDetail  # This view operates on the UserDetail model
    template_name = "manage_subscribers.html"  # Template to render the list
    context_object_name = "users"  # Context variable name for the list in the template
    paginate_by = 5  # Number of users to display per page

    # Custom queryset to enable search functionality
    def get_queryset(self):
        
        # Use select_related to optimize DB queries by joining related User table
        queryset = super().get_queryset().select_related("user") \
            .filter(is_archived=False, user__is_active=True)   

        # Get the search term from the query parameters (?search=...)
        search_query = self.request.GET.get("search", "")

        # If there's a search query, filter the queryset
        if search_query:
            queryset = queryset.filter(
                Q(user__username__icontains=search_query) |  # Match username
                Q(firstname__icontains=search_query) |       # Match first name
                Q(surname__icontains=search_query)           # Match surname
            )

        return queryset  # Return the final filtered or unfiltered queryset


# A class-based view for creating a new subscriber entry
@method_decorator(user_passes_test(lambda u: u.is_staff), name='dispatch')
class SubscriberCreateView(CreateView):
    model = UserDetail  # The model that will be created in this form view
    form_class = UserDetailFullForm  # Custom form that likely includes both User and UserDetail fields
    template_name = "subscriber_form.html"  # Template used to render the form

    # After successful form submission, redirect to the 'manage' view (e.g., ManageSubscribersView)
    success_url = reverse_lazy("manage")

# A class-based view  for updating an existing subscriber
@method_decorator(user_passes_test(lambda u: u.is_staff), name='dispatch')
class SubscriberUpdateView(UpdateView):
    model = UserDetail  # The model instance to update
    form_class = UserDetailFullForm  # The form used to edit subscriber details
    template_name = "subscriber_form.html"  # Reuses the create form template

    # After successful update, redirect to the 'manage' view (list of subscribers)
    success_url = reverse_lazy("manage")

    # Pre-populate initial data for fields from the related User model
    def get_initial(self):
        initial = super().get_initial()
        user = self.object.user  # Get the related User instance
        initial['username'] = user.username  # Populate the username field
        initial['email'] = user.email  # Populate the email field
        return initial

    # Save changes to both UserDetail and the related User object
    def form_valid(self, form):
        # Get the related User object from the current UserDetail
        user = self.object.user
        # Update fields from the submitted form
        user.username = form.cleaned_data['username']
        user.email = form.cleaned_data['email']

        # If a new password is provided, update it securely
        if form.cleaned_data['password']:
            user.set_password(form.cleaned_data['password'])

        user.save()  # Save changes to the User model
        return super().form_valid(form)  # Continue saving UserDetail via the form

# A class-based view for archiving a subscriber (UserDetail and its associated User)
@method_decorator(user_passes_test(lambda u: u.is_staff), name='dispatch')
class SubscriberArchiveView(View):
    success_url = reverse_lazy("manage")  # Redirect after archiving

    def post(self, request, *args, **kwargs):
        user_detail = get_object_or_404(UserDetail, pk=kwargs["pk"])
        user = user_detail.user

        # Archive both models
        user_detail.is_archived = True
        user_detail.save()

        user.is_active = False
        user.save()

        messages.success(request, f"User '{user.username}' archived.")
        return redirect(self.success_url)

class UserDetailViewSet(viewsets.ModelViewSet):
    queryset = UserDetail.objects.all()
    serializer_class = UserDetailSerializer

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        if user_id:
            return self.queryset.filter(user_id=user_id)
        return self.queryset

class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer

    def get_queryset(self):
        owner_id = self.request.query_params.get('owner_id')
        if owner_id:
            return self.queryset.filter(owner_id=owner_id)
        return self.queryset

class MenuViewSet(viewsets.ModelViewSet):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer

    def get_queryset(self):
        restaurant_id = self.request.query_params.get('restaurant_id')
        if restaurant_id:
            return self.queryset.filter(restaurant_id=restaurant_id)
        return self.queryset

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_queryset(self):
        menu_id = self.request.query_params.get('menu_id')
        if menu_id:
            return self.queryset.filter(menu_id=menu_id)
        return self.queryset

class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_queryset(self):
        category_id = self.request.query_params.get('category_id')
        if category_id:
            return self.queryset.filter(category_id=category_id)
        return self.queryset

class TableViewSet(viewsets.ModelViewSet):
    queryset = Table.objects.all()
    serializer_class = TableSerializer

    def get_queryset(self):
        restaurant_id = self.request.query_params.get('restaurant_id')
        if restaurant_id:
            return self.queryset.filter(restaurant_id=restaurant_id)
        return self.queryset

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        table_id = self.request.query_params.get('table_id')
        if table_id:
            return self.queryset.filter(table_id=table_id)
        return self.queryset

class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer

    def get_queryset(self):
        order_id = self.request.query_params.get('order_id')
        if order_id:
            return self.queryset.filter(order_id=order_id)
        return self.queryset

    def create(self, request, *args, **kwargs):
        order_id = request.data.get("order")
        menu_item_id = request.data.get("menu_item")
        price = float(request.data.get("price", 0))

        # Check if the item already exists in the order
        existing_item = OrderItem.objects.filter(order_id=order_id, menu_item_id=menu_item_id).first()

        if existing_item:
            existing_item.quantity += 1
            existing_item.price = existing_item.quantity * price
            existing_item.save()

            serializer = self.get_serializer(existing_item, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Otherwise create a new one
        return super().create(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        new_qty = int(request.data.get("quantity", instance.quantity))

        if new_qty <= 0:
            instance.delete()
            return Response({"deleted": True}, status=status.HTTP_204_NO_CONTENT)

        instance.quantity = new_qty
        instance.price = instance.menu_item.price * new_qty
        instance.save()

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

@login_required
def initialise_tables(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    restaurant.tables.all().delete()
    for i in range(1, restaurant.total_table + 1):
        Table.objects.create(restaurant=restaurant, table_number=i)
    return redirect("table_list", restaurant_id=restaurant.id)

@login_required
def table_list(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    tables = restaurant.tables.all()
    should_show_init_button = tables.count() != restaurant.total_table

    return render(request, "table_list.html", {
        "restaurant": restaurant, 
        "tables": tables, 
        "show_init_button": should_show_init_button,
    })

# Helper function to generate qr code - Created with the help of ChatGPT
def generate_qr_code(url):
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=5,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill="black", back_color="white").resize((150, 150))

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

def qr_code_view(request, restaurant_id, table_id):
    url = request.build_absolute_uri(f"/tabletap/qr/restaurant/{restaurant_id}/table/{table_id}")
    qr_image = generate_qr_code(url)
    return HttpResponse(qr_image.getvalue(), content_type="image/png")

def table_qr_redirect_view(request, restaurant_id, table_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    table = get_object_or_404(Table, id=table_id, restaurant=restaurant)

    # Find existing pending order
    order = Order.objects.filter(
        table=table,
        is_complete=False,
        status="PENDING",
    ).first()

    # If no order exists, create one
    if not order:
        order = Order.objects.create(
            table=table,
            is_complete=False,
            status="PENDING"
        )

    menus = Menu.objects.filter(restaurant=restaurant, is_published=True           )

    return render(request, "customer_menu.html", {
        "restaurant": restaurant,
        "menus": menus,
        "table": table,
        "order": order,
    })

def customer_menu_detail_view(request, restaurant_id, menu_id, table_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    table = get_object_or_404(Table, id=table_id, restaurant=restaurant)
    menu = get_object_or_404(Menu, id=menu_id, restaurant=restaurant)
    categories = Category.objects.filter(menu=menu)
    order = Order.objects.filter(table=table, is_complete=False, status='PENDING').first()

    return render(request, "customer_menu_detail.html", {
        "restaurant": restaurant,
        "menu": menu,
        "table": table,
        "categories": categories,
        "order": order,
    })

def customer_cart(request, restaurant_id, table_id, order_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    table = get_object_or_404(Table, id=table_id, restaurant=restaurant)
    order = get_object_or_404(Order, id=order_id, table=table)

    order_items = order.order_items.select_related('menu_item').all()
    total = sum(item.price * item.quantity for item in order_items)

    return render(request, "customer_cart.html", {
        "restaurant": restaurant,
        "table": table,
        "order": order,
        "order_items": order_items,
        "total": total,
    })

@login_required
def orders_view(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)

    # logged in user has to own the restaurant
    if restaurant.owner != request.user.userdetail:
        return HttpResponse("Unauthorized", status=403)

    orders = Order.objects.filter(table__restaurant=restaurant).prefetch_related("order_items__menu_item")

    return render(request, "orders.html", {
        "restaurant": restaurant,
        "orders": orders,
    })