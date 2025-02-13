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
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes

from django.contrib.auth.decorators import login_required
from rest_framework import status
from .models import User,SocialPost,PostSave,PostComment, PostLike, Track, Playlist, Profile, Comment, Like, Category
from .serializers import (
    UserSerializer,
    TrackSerializer,
    PlaylistSerializer,
    ProfileSerializer,
    CommentSerializer,
    LikeSerializer,
    CategorySerializer,
    SocialPostSerializer, 
    PostLikeSerializer,
    PostCommentSerializer,
    PostSaveSerializer,
)
import logging
logger = logging.getLogger(__name__)
class SignUpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print("Request data received:", request.data)  # Debug log

        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        
        print("Serializer errors:", serializer.errors)  # Debug log
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
        base_slug = slug
        counter = 1
        while Track.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        serializer.save(artist=self.request.user, slug=slug)

    @action(detail=False, methods=['post'], url_path='upload')
    def upload_track(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(artist=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




    
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
    def favorites(self, request):
   
        user = request.user
        if not user.is_authenticated:
            return Response({'detail': 'Authentication required'}, status=401)

        favorite_tracks = user.favorite_tracks.all()
        serializer = self.get_serializer(favorite_tracks, many=True)
        return Response(serializer.data)
    @action(detail=True, methods=['post'], url_path='toggle-favorite')
    def toggle_favorite(self, request, pk=None):
        track = self.get_object()
        user = request.user

        existing_like = Like.objects.filter(user=user, track=track).first()
        if existing_like:
            existing_like.delete()
            return Response({"status": "Track unfavorited"}, status=status.HTTP_200_OK)
        
        Like.objects.create(user=user, track=track)
        return Response({"status": "Track favorited"}, status=status.HTTP_200_OK)


    @action(detail=False, methods=['get'], url_path='favorites')
    def get_favorites(self, request):
        user = request.user
        favorites = Track.objects.filter(likes__user=user)
        serializer = TrackSerializer(favorites, many=True, context={"request": request})
        return Response(serializer.data)

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

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def check_or_redirect(self, request):
        user = request.user
        if hasattr(user, 'profile'):
            return Response({'profile_exists': True}, status=status.HTTP_200_OK)
        return Response({'profile_exists': False, 'message': 'Redirect to create profile'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def create_profile(self, request):
        if hasattr(request.user, 'profile'):
            return Response({'detail': 'Profile already exists for this user.'}, status=status.HTTP_400_BAD_REQUEST)

        # Pass the request to the serializer context
        serializer = ProfileSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            print("Serializer data is valid:", serializer.validated_data)  # Debug log
            serializer.save()  # Save will now correctly handle user
            print("Profile created successfully")  # Debug log
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        print("Serializer errors:", serializer.errors)  # Debug log
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def has_profile(self, request):
        profile_exists = hasattr(self.request.user, 'profile')
        return Response({'profile_exists': profile_exists})
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Retrieve the profile of the authenticated user."""
        try:
            profile = request.user.profile  # Assuming 'profile' is a one-to-one field related to the user
            serializer = self.get_serializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response({'detail': 'Profile does not exist for this user.'}, status=status.HTTP_404_NOT_FOUND)


    @action(detail=False, methods=['get'], url_path='by_user/(?P<user_id>[^/.]+)')
    def by_user(self, request, user_id=None):
        """Retrieve a profile by user ID."""
        try:
            user = User.objects.get(id=user_id)
            profile = user.profile
            serializer = self.get_serializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Profile.DoesNotExist:
            return Response({'detail': 'Profile not found for this user.'}, status=status.HTTP_404_NOT_FOUND)
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


class FavoriteTracksView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure authentication is enforced

    def get(self, request):
        user = request.user
        favorite_tracks = Track.objects.filter(likes__user=user)  # Query for the user's favorites
        serializer = TrackSerializer(favorite_tracks, many=True, context={"request": request})
        return Response(serializer.data, status=200)

class SocialPostViewSet(viewsets.ModelViewSet):
    queryset = SocialPost.objects.all()
    serializer_class = SocialPostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        try:
            media_file = self.request.FILES.get('media_file')
            content_type = self.request.data.get('content_type')
            caption = self.request.data.get('caption')

            if not all([media_file, content_type, caption]):
                missing = [field for field in ['media_file', 'content_type', 'caption'] if not self.request.data.get(field)]
                raise ValidationError({ "missing_fields": missing })

            # Verify file signature
            allowed_types = {
                'image': ['image/jpeg', 'image/png'],
                'video': ['video/mp4']
            }
            
            if content_type not in allowed_types:
                raise ValidationError({"content_type": "Invalid content type. Must be image/video"})
            
            if media_file.content_type not in allowed_types[content_type]:
                raise ValidationError({"media_file": f"Invalid {content_type} format. Allowed: {', '.join(allowed_types[content_type])}"})

            serializer.save(user=self.request.user)
            
        except Exception as e:
            logger.error(f"Create post error: {str(e)}")
            raise
     

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        post = self.get_object()
        user = request.user
        
        # Check if like exists
        like_exists = PostLike.objects.filter(post=post, user=user).exists()
        
        if like_exists:
            # Unlike the post
            PostLike.objects.filter(post=post, user=user).delete()
            liked = False
        else:
            # Like the post
            PostLike.objects.create(post=post, user=user)
            liked = True
        
        # Get updated like count
        likes_count = PostLike.objects.filter(post=post).count()
        
        return Response({
            'status': 'success',
            'likes_count': likes_count,
            'is_liked': liked
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def comment(self, request, pk=None):
        post = self.get_object()
        serializer = PostCommentSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save(user=request.user, post=post)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def save_post(self, request, pk=None):
        post = self.get_object()
        user = request.user
        
        if PostSave.objects.filter(user=user, post=post).exists():
            return Response(
                {"error": "You have already saved this post."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        PostSave.objects.create(user=user, post=post)
        return Response(
            {"status": "Post saved"},
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get'])
    def share(self, request, pk=None):
        post = self.get_object()
        share_url = request.build_absolute_uri(post.get_absolute_url())
        return Response(
            {"share_url": share_url},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        post = self.get_object()
        if not post.media_file:
            return Response(
                {'error': 'Media file not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        return FileResponse(
            open(post.media_file.path, 'rb'), 
            as_attachment=True, 
            filename=post.media_file.name
        )


class PostLikeViewSet(viewsets.ModelViewSet):
    queryset = PostLike.objects.all()
    serializer_class = PostLikeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class PostCommentViewSet(viewsets.ModelViewSet):
    queryset = PostComment.objects.all()
    serializer_class = PostCommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        post_id = self.kwargs.get('post_pk')
        if post_id:
            return PostComment.objects.filter(post__id=post_id)
        return super().get_queryset()

    def perform_create(self, serializer):
        post_id = self.kwargs.get('post_pk')
        try:
            post = SocialPost.objects.get(id=post_id)
        except SocialPost.DoesNotExist:
            raise ValidationError({"error": "Post not found"})
        serializer.save(user=self.request.user, post=post)


class PostSaveViewSet(viewsets.ModelViewSet):
    queryset = PostSave.objects.all()
    serializer_class = PostSaveSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


# Update UserViewSet to include social posts
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['get'])
    def social_posts(self, request, pk=None):
        user = self.get_object()
        posts = SocialPost.objects.filter(user=user)
        page = self.paginate_queryset(posts)
        
        if page is not None:
            serializer = SocialPostSerializer(
                page, 
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
            
        serializer = SocialPostSerializer(
            posts, 
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)