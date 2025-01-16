# from rest_framework_nested.routers import NestedSimpleRouter
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    TrackViewSet,
    PlaylistViewSet,
    ProfileViewSet,
    CommentViewSet,
    LikeViewSet,
    CategoryViewSet,
)
from rest_framework_nested.routers import NestedSimpleRouter
from django.urls import path
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
urlpatterns = [
    path('tracks/<int:pk>/download/', TrackViewSet.as_view({'get': 'download'}), name='track-download'),
]
urlpatterns = router.urls + tracks_router.urls
