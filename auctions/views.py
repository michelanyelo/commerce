from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.db.models import Max


from .models import Comment, User, Category, Listing, UserWatchlist, Bid


def get_filtered_listings(category_slug=None):
    active_listings = Listing.objects.filter(is_active=True)

    if category_slug:
        category = Category.objects.get(slug=category_slug)
        active_listings = active_listings.filter(category=category)

    return active_listings


def index(request):
    # ---- start list of all listing categories ----
    all_categories = Category.objects.all()
    category_slug = None
    if request.method == "POST":
        category_slug = request.POST['category']
        if category_slug:
            return HttpResponseRedirect(reverse('category_listings', kwargs={
                'slug': category_slug
            }))
    # ---- end list of all listing categories ----

    active_listings = get_filtered_listings(category_slug)
    return render(request, "auctions/index.html", {
        "actives": active_listings,
        "categories": all_categories
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
        price = float(request.POST["price"])
        category_id = request.POST["category"]
        category = Category.objects.get(pk=category_id)
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
            bid_current=float(price),
            is_active=is_active,
            seller=seller,
            category=category,
        )
        # saving to db
        new_listing.save()
        # redirect to index html
        return HttpResponseRedirect(reverse(index))
# ---- end create listing ----


# ---- start display individual listing ----
def listing_by_id(request, listing_id):
    listing = Listing.objects.get(id=listing_id)
    all_comments = Comment.objects.filter(listing=listing)
    bid = Bid.objects.filter(listing=listing).last()
    user = request.user
    if user.is_authenticated:
        in_watchlist = UserWatchlist.objects.filter(
            user=user, listing=listing).exists()
    else:
        in_watchlist = False
    return render(request, "auctions/listing.html", {
        "listing": listing,
        "watchlist": in_watchlist,
        "comments": all_comments,
        "bid": bid
    })
# ---- end display individual listing ----


# ---- start add/remove watchlist ----
def remove_watchlist(request, listing_id):
    # get the listing object
    listing = Listing.objects.get(pk=listing_id)
    # get the current user
    user = request.user
    # check if there is an entry in the user's watchlist for the listing
    user_watchlist_entry = UserWatchlist.objects.filter(
        user=user, listing=listing).first()
    # if the entry exists, delete it
    if user_watchlist_entry:
        user_watchlist_entry.delete()
    # redirect back to the listing page
    return HttpResponseRedirect(reverse('listing', args=(listing_id,)))


def add_watchlist(request, listing_id):
    # get the listing object
    listing = Listing.objects.get(pk=listing_id)
    # get the current user
    user = request.user
    # if there is no existing entry in the user's watchlist for the listing, create one
    if not UserWatchlist.objects.filter(user=user, listing=listing).exists():
        UserWatchlist.objects.create(user=user, listing=listing)
    # redirect back to the listing page
    return HttpResponseRedirect(reverse('listing', args=(listing_id,)))
# ---- end add/remove watchlist ----


# ---- start display personal watchlist ----
def personal_watchlist(request):
    # get the current user
    user = request.user
    # get all listings in the user's watchlist
    listings = Listing.objects.filter(userwatchlist__user=user)
    # render the watchlist template with the listings
    return render(request, "auctions/watchlist.html", {
        "listings": listings
    })
# ---- end display personal watchlist ----


# ---- start list of all listing categories ----
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
# ---- end list of all listing categories ----


# ---- start add comments ----
def add_comment(request, listing_id):
    user = request.user
    listing = Listing.objects.get(pk=listing_id)
    message = request.POST["comment_content"]
    new_comment = Comment(
        author=user,
        listing=listing,
        message=message
    )
    new_comment.save()
    return HttpResponseRedirect(reverse('listing', args=(listing_id,)))
# ---- end add comments ----


# ---- start add bids ----
def add_bid(request, listing_id):
    if request.method == "POST":
        # retrieve the bid amount from the form
        amount = float(request.POST["bid_amount"])
        # retrieve the bidder (current user)
        bidder = request.user
        # retrieve the listing object based on the listing_id
        listing = Listing.objects.get(pk=listing_id)
        # retrieve all comments associated with the listing
        all_comments = Comment.objects.filter(listing=listing)
        # retrieve the current user
        user = request.user

        # check if the user is authenticated
        if user.is_authenticated:
            # check if the listing is in the user's watchlist
            in_watchlist = UserWatchlist.objects.filter(
                user=user, listing=listing).exists()
        else:
            # if user is not authenticated, set in_watchlist to False
            in_watchlist = False

        # check if the bid amount is greater than the current bid on the listing
        if amount > listing.bid_current:
            # create a new bid object
            bid = Bid(listing=listing, bidder=bidder, amount=amount)
            bid.save()
            # update the current bid amount on the listing
            listing.bid_current = amount
            listing.save()
            # render the listing page with relevant information
            return render(request, 'auctions/listing.html', {
                'listing': listing,
                "watchlist": in_watchlist,
                "comments": all_comments
            })

    # if the method is not POST, redirect back to the listing page
    return HttpResponseRedirect(reverse('listing', args=(listing_id,)))
# ---- end add bids ----


# ---- start close auction ----
def close_auction(request, listing_id):
    # retrieve the listing object based on the listing_id
    listing = Listing.objects.get(pk=listing_id)
    # retrieve all comments associated with the listing
    all_comments = Comment.objects.filter(listing=listing)
    # get the current user
    user = request.user

    # check if the user is authenticated
    if user.is_authenticated:
        # check if the listing is in the user's watchlist
        in_watchlist = UserWatchlist.objects.filter(
            user=user, listing=listing).exists()
    else:
        # if user is not authenticated, set in_watchlist to False
        in_watchlist = False

    # check if the user has placed a bid for the listing
    if Bid.objects.filter(bidder=user, listing=listing).exists():
        # retrieve the last bid for the listing
        bid = Bid.objects.filter(listing=listing).last()
        # check if the bid amount is greater than 0
        if bid.amount > 0:
            # set the listing as inactive
            listing.is_active = False
            listing.save()
            # render the listing page with relevant information
            return render(request, 'auctions/listing.html', {
                'listing': listing,
                "watchlist": in_watchlist,
                "comments": all_comments,
                "bid": bid,
            })
        else:
            # render the listing page with an error message if bid amount is not valid
            return render(request, 'auctions/listing.html', {
                'listing': listing,
                "watchlist": in_watchlist,
                "comments": all_comments,
                "error_message": "Bid amount must be greater than 0.",
            })
    else:
        # render the listing page with an error message if user hasn't placed a bid
        return render(request, 'auctions/listing.html', {
            'listing': listing,
            "watchlist": in_watchlist,
            "comments": all_comments,
            "error_message": "You haven't placed a bid for this listing.",
        })
# ---- end close auction ----


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
