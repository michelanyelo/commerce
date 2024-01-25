from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse

from .models import User, Category, Listing


def get_filtered_listings(category_slug=None):
    active_listings = Listing.objects.filter(is_active=True)

    if category_slug:
        category = Category.objects.get(slug=category_slug)
        active_listings = active_listings.filter(category=category)

    return active_listings


def index(request):
    all_categories = Category.objects.all()
    category_slug = None

    if request.method == "POST":
        category_slug = request.POST['category']
        if category_slug:
            return redirect('category_listings', slug=category_slug)

    active_listings = get_filtered_listings(category_slug)

    return render(request, "auctions/index.html", {
        "actives": active_listings,
        "categories": all_categories
    })


def category_listings(request, slug=None):
    active_listings = get_filtered_listings(slug)

    if slug:
        category = Category.objects.get(slug=slug)
    else:
        category = None

    return render(request, "auctions/category_listings.html", {
        "actives": active_listings,
        "category": category
    })


# ---- start create listing ----

def create_listing(request):
    if request.method == "GET":
        allCategories = Category.objects.all()
        return render(request, "auctions/create.html", {"categories": allCategories})
    # if method is post
    else:
        title = request.POST["title"]
        description = request.POST["description"]
        image_url = request.POST["image_url"]
        price = request.POST["price"]
        category = request.POST["category"]
        categoryData = Category.objects.get(name=category)
        active = request.POST["active"]
        # convert 'active' to boolean
        if active == "on":
            is_active = True
        else:
            is_active = False
        seller = request.user
        # creating new listing
        new_listing = Listing(
            title=title,
            description=description,
            image_url=image_url,
            bid_start=float(price),
            is_active=is_active,
            seller=seller,
            category=categoryData,
        )
        # saving to db
        new_listing.save()
        # redirect to index html
        return HttpResponseRedirect(reverse(index))


# ---- end create listing ----

# ---- start individual listing ----

def listing_by_id(request, listing_id):
    listing = Listing.objects.get(id=listing_id)
    return render(request, "auctions/listing.html", {
        "listing": listing
    })

# ---- end individual listing ----


def login_view(request):
    if request.method == "POST":
        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(
                request,
                "auctions/login.html",
                {"message": "Invalid username and/or password."},
            )
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(
                request, "auctions/register.html", {
                    "message": "Passwords must match."}
            )

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(
                request,
                "auctions/register.html",
                {"message": "Username already taken."},
            )
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
