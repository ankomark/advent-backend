

from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    UserViewSet,
    TrackViewSet,
    PlaylistViewSet,
    ProfileViewSet,
    CommentViewSet,
    LikeViewSet,
    CategoryViewSet,
    SignUpView,
    FavoriteTracksView, 
    # ProfileByUserView,
)
from .favorites import toggle_favorite
from .views import FavoriteTracksView
from rest_framework_nested.routers import NestedSimpleRouter
from django.urls import path, include
from rest_framework.routers import DefaultRouter
# Base router
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'tracks', TrackViewSet)
router.register(r'playlists', PlaylistViewSet)
router.register(r'profiles', ProfileViewSet, basename='profiles')
 
router.register(r'comments', CommentViewSet)
router.register(r'likes', LikeViewSet)
router.register(r'categories', CategoryViewSet)

# Nested router for comments under tracks
tracks_router = NestedSimpleRouter(router, r'tracks', lookup='track')
tracks_router.register(r'comments', CommentViewSet, basename='track-comments')

# Additional routes
urlpatterns = [
    path('api/auth/signup/', SignUpView.as_view(), name='signup'),
    path('tracks/<int:pk>/download/', TrackViewSet.as_view({'get': 'download'}), name='track-download'),
    path('api/songs/tracks/<int:track_id>/favorite/', toggle_favorite, name='toggle_favorite'),
    path('favorites/', FavoriteTracksView.as_view(), name='favorite-tracks'),
    #  path('profiles/by_user/<int:user_id>/', ProfileViewSet.as_view({'get': 'by_user'}), name='profile-by-user'),
    path('profiles/by_user/<int:user_id>/', ProfileViewSet.as_view({'get': 'by_user'}), name='profile-by-user'),
    # path('tracks/upload/', TrackViewSet.as_view({'post': 'upload_track'}), name='track-upload'),
    #  path('api/songs/', include((router.urls, 'app_name'), namespace='songs')),
    path('tracks/upload/', TrackViewSet.as_view({'post': 'upload_track'}), name='track-upload'),

]
# Add router URLs
urlpatterns += router.urls + tracks_router.urls
