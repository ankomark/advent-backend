from rest_framework import serializers
from .models import User
from .models import User,Track,Playlist,Profile,Comment,Like,Category,SocialPost,PostLike,PostComment,PostSave


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ('id', 'username', 'email',  'password','profile')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            # is_artist=validated_data.get('is_artist', False)
        )
        return user
class TrackSerializer(serializers.ModelSerializer):
     likes_count = serializers.SerializerMethodField()
     favorite = serializers.SerializerMethodField()
     artist = UserSerializer(read_only=True)  # Include full artist detai
     
     class Meta:
        model = Track
        fields = [
            'id', 'title', 'artist', 'album', 'audio_file',
            'cover_image', 'lyrics', 'slug', 'favorite',
            'views', 'downloads','likes_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['artist', 'slug', 'views', 'downloads', 'created_at', 'updated_at']
     def get_favorite(self, obj):
        user = self.context['request'].user
        return Like.objects.filter(user=user, track=obj).exists()
     def get_likes_count(self, obj):
      return obj.likes.count()
     def get_is_favorite(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and obj.favorites.filter(id=user.id).exists()    

class PlaylistSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    tracks = TrackSerializer(many=True, read_only=True)
    class Meta:
        model = Playlist
        fields = ('id', 'name', 'user', 'tracks', 'created_at', 'updated_at')


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['bio', 'birth_date', 'location', 'is_public', 'picture',]

    def create(self, validated_data):
        user = self.context['request'].user  # Access user from request
        # Remove 'user' from validated_data if it exists
        profile = Profile.objects.create(user=user, **validated_data)
        return profile

class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    track = TrackSerializer(read_only=True)
    class Meta:
        model = Comment
        fields = ('id', 'content', 'user', 'track', 'created_at', 'updated_at')


class LikeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    track = TrackSerializer(read_only=True)
    class Meta:
        model = Like
        fields = ('id', 'user', 'track', 'created_at')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'created_at', 'updated_at')






# Add these new serializers after your existing ones

class SocialPostSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    song = TrackSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    media_url = serializers.SerializerMethodField()

    class Meta:
        model = SocialPost
        fields = [
            'id', 'user', 'content_type', 'media_file', 'media_url', 'song',
            'caption', 'tags', 'location', 'duration', 'created_at', 'updated_at',
            'likes_count', 'comments_count', 'is_liked', 'is_saved'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def get_media_url(self, obj):
        request = self.context.get('request')
        if obj.media_file and request:
            return request.build_absolute_uri(obj.media_file.url)
        return None

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_is_liked(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return obj.likes.filter(user=user).exists()
        return False

    def get_is_saved(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return obj.saves.filter(user=user).exists()
        return False

    def validate(self, data):
        if data.get('content_type') == 'video' and 'media_file' in data:
            # Add video validation logic here
            pass
        return data


class PostLikeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    post = SocialPostSerializer(read_only=True)

    class Meta:
        model = PostLike
        fields = ['id', 'user', 'post', 'created_at']
        read_only_fields = ['user', 'post', 'created_at']


class PostCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    post = SocialPostSerializer(read_only=True)

    class Meta:
        model = PostComment
        fields = ['id', 'user', 'post', 'content', 'created_at']
        read_only_fields = ['user', 'post', 'created_at']


class PostSaveSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    post = SocialPostSerializer(read_only=True)

    class Meta:
        model = PostSave
        fields = ['id', 'user', 'post', 'created_at']
        read_only_fields = ['user', 'post', 'created_at']


# Update UserSerializer to include social posts
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    social_posts = serializers.SerializerMethodField()
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'password', 
            'social_posts', 'profile'
        )

    def get_social_posts(self, obj):
        posts = obj.social_posts.all()[:5]  # Get latest 5 posts
        return SocialPostSerializer(posts, many=True, context=self.context).data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        return user