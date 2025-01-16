from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from django.utils.text import slugify
from rest_framework.exceptions import ValidationError
from django.http import FileResponse,Http404



from .models import User, Track, Playlist, Profile, Comment, Like, Category
from .serializers import (
    UserSerializer,
    TrackSerializer,
    PlaylistSerializer,
    ProfileSerializer,
    CommentSerializer,
    LikeSerializer,
    CategorySerializer,
)

class SignUpView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['get'])
    def playlists(self, request, pk=None):
        user = self.get_object()
        playlists = Playlist.objects.filter(user=user)
        serializer = PlaylistSerializer(playlists, many=True)
        return Response(serializer.data)


class TrackViewSet(viewsets.ModelViewSet):
    queryset = Track.objects.all()
    serializer_class = TrackSerializer
    permission_classes = [IsAuthenticated]


    def perform_create(self, serializer):
        title = serializer.validated_data.get('title')
        slug = slugify(title)

        # Check if the slug already exists
        if Track.objects.filter(slug=slug).exists():
            raise serializers.ValidationError({'error': 'A track with this slug already exists.'})

        # Save the serializer with user and slug
        serializer.save(artist=self.request.user, user=self.request.user, slug=slug)

    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        track = self.get_object()
        user = request.user
        # Check if the user has already liked the track
        if Like.objects.filter(user=user, track=track).exists():
          return Response({"error": "You have already liked this track."}, status=400)

        Like.objects.create(user=user, track=track)
    # Return the updated like count
        likes_count = Like.objects.filter(track=track).count()
        return Response({"status": "Track liked", "likes_count": likes_count})



    @action(detail=True, methods=['post'])
    def toggle_like(self, request, pk=None):
     track = self.get_object()
     user = request.user

    # Toggle like
     existing_like = Like.objects.filter(user=user, track=track).first()
     if existing_like:
        existing_like.delete()
        likes_count = Like.objects.filter(track=track).count()
        return Response({"status": "Track unliked", "likes_count": likes_count})

     Like.objects.create(user=user, track=track)
     likes_count = Like.objects.filter(track=track).count()
     return Response({"status": "Track liked", "likes_count": likes_count})
  
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        track = self.get_object()
        if not track.audio_file:
            return Response({'error': 'Audio file not found'}, status=404)
        return FileResponse(open(track.audio_file.path, 'rb'), as_attachment=True, filename=track.audio_file.name)
    @action(detail=True, methods=['post'])
    def favorite(self, request, pk=None):
        track = self.get_object()
        user = request.user

        if not user.is_authenticated:
            return Response({'detail': 'Authentication required'}, status=401)

        if track.favorites.filter(id=user.id).exists():
            track.favorites.remove(user)
            return Response({'message': 'Removed from favorites'})
        else:
            track.favorites.add(user)
            return Response({'message': 'Added to favorites'})
class PlaylistViewSet(viewsets.ModelViewSet):
    queryset = Playlist.objects.all()
    serializer_class = PlaylistSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_update(self, serializer):
        if serializer.instance.user != self.request.user:
            raise PermissionDenied("You can only update your own profile.")
        serializer.save()
    

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        # Use 'track_pk' from the nested route's lookup
        track_id = self.kwargs.get('track_pk')
        if track_id:
            return Comment.objects.filter(track__id=track_id)
        return super().get_queryset()

    def perform_create(self, serializer):
        # Use 'track_pk' from the nested route's lookup
        track_id = self.kwargs.get('track_pk')
        try:
            track = Track.objects.get(id=track_id)
        except Track.DoesNotExist:
            raise ValidationError({"error": "Track not found"})
        serializer.save(user=self.request.user, track=track)


class LikeViewSet(viewsets.ModelViewSet):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
