from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import User

from django import forms
from .models import Listing, Bid, Comment
from django.contrib.auth.decorators import login_required

# Forms 
class AuctionForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ["title", "description", "starting_bid", "image_url", "category"]

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ["amount"]

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]





# views

def index(request):
    return render(request, "auctions/index.html", {
        "auctions": Listing.objects.filter(active=True)
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("auctions:index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("auctions:index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("auctions:index"))
    else:
        return render(request, "auctions/register.html")

@login_required
def create_view(request):
    if request.method == "POST":
        Auction = AuctionForm(request.POST)
        if Auction.is_valid():
            new_auction = Auction.save(commit=False)
            new_auction.owner = request.user
            new_auction.active = True
            new_auction.save()
            return HttpResponseRedirect(reverse("auctions:detail", kwargs={"id": new_auction.pk}))
     
    return render( request,"auctions/createAuction.html",{
        "AuctionForm":AuctionForm()
    })

@login_required
def detail_view(request, id):
    try:
        auction = Listing.objects.get(pk=id)
    except Listing.DoesNotExist:
        return HttpResponse("Auction not found.", status=404)
    
    if request.method == "POST":
        if 'amount' in request.POST:
            bid_form = BidForm(request.POST)
            if bid_form.is_valid():
                bid = bid_form.save(commit=False)
                bid.user = request.user
                bid.listing = auction
                if bid.amount > auction.starting_bid:
                    bid.save()
                    auction.starting_bid = bid.amount
                    auction.save()
                else:
                    return render(request, "auctions/auctionDetails.html", {
                        "auction": auction,
                        "comments": auction.comments.all(),
                        "BidForm": bid_form,
                        "CommentForm": CommentForm(),
                        "message": "Bid must be higher than the current bid."
                    })

        if 'content' in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.user = request.user
                comment.listing = auction
                comment.save()
    
    return render(request, "auctions/auctionDetails.html", {
        "auction": auction,
        "comments": auction.comments.all(),
        "BidForm": BidForm(),
        "CommentForm": CommentForm()
    })