from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CustomUserCreationForm, PostForm, CommentForm, ProfileEditForm
from .models import UserProfile, Post, Follow, Like, Notification

from django.db.models import Prefetch  # Add this import if not present
from django.db.models import Exists, OuterRef, Count, Value, BooleanField, Q

from myapp.models import Follow, Like


# Create your views here.
def home(request):
    posts_qs = Post.objects.all().prefetch_related('comments', 'comments__author').annotate(
        like_count=Count('likes')
    ).order_by('-created_at')

    if request.user.is_authenticated:
        user_likes_subquery = Like.objects.filter(
            post=OuterRef('pk'),
            user=request.user
        )
        posts_qs = posts_qs.annotate(
            user_liked=Exists(user_likes_subquery)
        )
    else:
        posts_qs = posts_qs.annotate(
            user_liked=Value(False, output_field=BooleanField())
        )

    return render(request, 'index.html', {  # Changed from 'home.html' to 'index.html'
        'posts': posts_qs,
        'comment_form': CommentForm()
    })


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('home')  # Redirect to your home view (update 'home' to your URL name)
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            
            # Store phone number in session for now (or create a profile model)
            request.session['user_phone'] = form.cleaned_data.get('phone_number')
            
            messages.success(request, f'Account created for {username}! Welcome to Melon!')
            # Automatically log in the user after registration
            login(request, user)
            return redirect('home')  # Redirect to your home view
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)

        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('home')
    else:
        form = PostForm()
    return render(request, 'create.html', {'form': form})

def profile(request, username):
    user = get_object_or_404(User, username=username)
    
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Get user's posts
    posts = Post.objects.filter(author=user).order_by('-created_at')
    
    # Get follower/following counts
    follower_count = user.followers.count()
    following_count = user.following.count()
    
    # Check if current user is following this profile user
    is_following = False
    if request.user.is_authenticated and request.user != user:
        is_following = request.user.following.filter(following=user).exists()

    return render(request, 'profile.html', {
        'profile_user': user,
        'profile': profile,
        'posts': posts,
        'follower_count': follower_count,
        'following_count': following_count,
        'is_following': is_following,
        'is_own_profile': request.user == user,
    })

@login_required
def edit_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile', username=request.user.username)
    else:
        form = ProfileEditForm(instance=profile, user=request.user)
    
    return render(request, 'edit_profile.html', {'form': form})

def explore(request):
    # 1. Annotate 'like_count' (Make sure to use this exact name!)
    posts_qs = Post.objects.annotate(
        like_count=Count('likes')
    ).order_by('-like_count') # Sort by most likes (Popularity)

    # 2. Annotate 'user_liked' (Just like in the home view)
    if request.user.is_authenticated:
        user_likes_subquery = Like.objects.filter(
            post=OuterRef('pk'),
            user=request.user
        )
        posts_qs = posts_qs.annotate(
            user_liked=Exists(user_likes_subquery)
        )
    else:
        # Fallback for anonymous users
        posts_qs = posts_qs.annotate(
            user_liked=Value(False, output_field=BooleanField())
        )

    return render(request, 'explore.html', {'posts': posts_qs})


def follow_user(request, username):
    target = User.objects.get(username=username)
    follow, created = Follow.objects.get_or_create(follower=request.user, following=target)

    if created:
        # Create Notification
        Notification.objects.create(
            sender=request.user,
            receiver=target,
            notification_type='follow'
        )

    return redirect('profile', username=username)

def unfollow_user(request, username):
    target = User.objects.get(username=username)
    # CHANGE 'followed' TO 'following'
    follow = Follow.objects.get(follower=request.user, following=target)
    follow.delete()

    return redirect('profile', username=username)


def like_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)

    if created and post.author != request.user:  # Don't notify if liking own post
        # Create Notification
        Notification.objects.create(
            sender=request.user,
            receiver=post.author,
            notification_type='like',
            post=post
        )

    return redirect(request.META.get('HTTP_REFERER', 'home'))

def unlike_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    Like.objects.filter(user=request.user, post=post).delete()
    return redirect(request.META.get('HTTP_REFERER', 'home'))

def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()

    # FIX 1: Change 'Post' to 'POST' (must be all caps)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('post', post_id=post_id)
    else:
        form = CommentForm()

    # FIX 2: Move the dictionary INSIDE the parenthesis
    return render(request, 'post.html', {
        'post': post,
        'comments': comments,
        'form': form,
    })

def logout_view(request):
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, f"Goodbye, {username}! You have been logged out successfully.")
    else:
        messages.info(request, "You were not logged in.")
    
    return redirect('login')  # Redirect to login page after logout

def search(request):
    query = request.GET.get('q')
    user_results = []
    post_results = []

    if query:
        # Search Users by username or full name
        user_results = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
        # Search Posts by content
        post_results = Post.objects.filter(content__icontains=query)

    return render(request, 'search_results.html', {
        'query': query,
        'users': user_results,
        'posts': post_results
    })

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
    return redirect('home')


@login_required
def notifications(request):
    # Get alerts for the current user, newest first
    alerts = Notification.objects.filter(receiver=request.user).order_by('-created_at')
    # Mark them as read (optional logic)
    alerts.update(is_read=True)

    return render(request, 'notifications.html', {'alerts': alerts})
