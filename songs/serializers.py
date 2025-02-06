from rest_framework import serializers
from .models import User
from .models import User,Track,Playlist,Profile,Comment,Like,Category


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ('id', 'username', 'email',  'password')

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
     def get_favorite(self, obj):
        user = self.context['request'].user
        return Like.objects.filter(user=user, track=obj).exists()
     class Meta:
        model = Track
        fields = [
            'id', 'title', 'artist', 'album', 'audio_file',
            'cover_image', 'lyrics', 'slug', 'favorite',
            'views', 'downloads','likes_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['artist', 'slug', 'views', 'downloads', 'created_at', 'updated_at']
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