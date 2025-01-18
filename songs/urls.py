from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter
from django.urls import path
from .views import (
    UserViewSet,
    TrackViewSet,
    PlaylistViewSet,
    ProfileViewSet,
    CommentViewSet,
    LikeViewSet,
    CategoryViewSet,
)
from .favorites import toggle_favorite  # Import from the new module
from .views import FavoriteTracksView # Import from the new module

# Base router
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'tracks', TrackViewSet)
router.register(r'playlists', PlaylistViewSet)
router.register(r'profiles', ProfileViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'likes', LikeViewSet)
router.register(r'categories', CategoryViewSet)

# Nested router for comments under tracks
tracks_router = NestedSimpleRouter(router, r'tracks', lookup='track')
tracks_router.register(r'comments', CommentViewSet, basename='track-comments')

# Additional routes
urlpatterns = [
    path('tracks/<int:pk>/download/', TrackViewSet.as_view({'get': 'download'}), name='track-download'),
    path('api/songs/tracks/<int:track_id>/favorite/', toggle_favorite, name='toggle_favorite'),
    path('favorites/', FavoriteTracksView.as_view(), name='favorite-tracks'),  # Simplified route
]

urlpatterns += router.urls + tracks_router.urls
