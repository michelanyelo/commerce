from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import User, Category, Listing


def index(request):
    # ---- start active listing page ----
    # get all categories
    all_categories = Category.objects.all()

    # get active listings
    active_listing = Listing.objects.filter(is_active=True)

    # render the index.html template with active listings and all categories
    return render(request, "auctions/index.html", {
        "actives": active_listing,
        "categories": all_categories
    })
    # ---- end active listing page ----


# ---- start categories listing ----

def category_listings(request, category_slug):
    # get the category object based on the provided slug
    category = Category.objects.get(slug=category_slug)

    # get active listings for the specific category
    active_listings = Listing.objects.filter(category=category, is_active=True)

    # render the category_listings.html template with active listings and the selected category
    return render(request, "auctions/category_listings.html", {
        "category": category,
        "actives": active_listings
    })

# ---- end categories listing ----


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
