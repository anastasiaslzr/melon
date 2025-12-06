from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('create/', views.create, name='create-post'),
    path('profile/<str:username>/', views.profile, name='profile'),  # Added trailing slash for consistency
    path('edit-profile/', views.edit_profile, name='edit-profile'),  # New URL
    path('explore/', views.explore, name='explore'),
    path('post/<int:post_id>/like/', views.like_post, name='like-post'),
    path('post/<int:post_id>/unlike/', views.unlike_post, name='unlike-post'),
    path('post/<int:post_id>/', views.post_detail, name='post'),  # Added trailing slash
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/<str:username>/follow/', views.follow_user, name='follow-user'),
    path('profile/<str:username>/unfollow/', views.unfollow_user, name='unfollow-user'),
    path('search/', views.search, name='search'),
    path('post/<int:post_id>/add_comment/', views.add_comment, name='add-comment'),
    path('notifications/', views.notifications, name='notifications'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)