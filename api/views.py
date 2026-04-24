from django.contrib.auth.models import User
from django.contrib.auth import authenticate as auth_authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Post, Like, Comment, Profile


# Register
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    username = request.data.get('username')
    email    = request.data.get('email')
    password = request.data.get('password')

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already exists'}, status=400)

    user = User.objects.create_user(username=username, email=email, password=password)
    Profile.objects.create(user=user)

    return Response({'message': 'Account created!'})


# login
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    email    = request.data.get('email')
    password = request.data.get('password')

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'error': 'user does not exist'}, status=404)

    user = auth_authenticate(username=user.username, password=password)
    if user is None:
        return Response({'error': 'wrong password'}, status=400)

    refresh = RefreshToken.for_user(user)

    return Response({
        'token': str(refresh.access_token),
        'user': {
            'id': user.id,
            'name': user.username,
            'email': user.email,
        }
    })


# Profile
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    profile = Profile.objects.get(user=request.user)

    return Response({
        'name': request.user.username,
        'email': request.user.email,
        'location': profile.location,
        'bio': profile.bio,
        'headline': profile.headline,
        'skills': profile.skills,
    })


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    profile = Profile.objects.get(user=request.user)

    fields = [
        'location','bio','headline','exp_title','exp_company',
        'exp_date','edu_school','edu_degree','edu_date','skills'
    ]

    for field in fields:
        setattr(profile, field, request.data.get(field, getattr(profile, field)))

    profile.save()

    return Response({'message': 'Profile updated'})


# post
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_posts(request):
    posts = Post.objects.all().order_by('-created_at')

    data = []
    for post in posts:
        data.append({
            'id': post.id,
            'author': post.author.username,
            'content': post.content,
            'likes': post.likes.count(),
            'comments': post.comments.count(),
            'created_at': str(post.created_at),
        })

    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_post(request):
    post = Post.objects.create(
        author=request.user,
        content=request.data.get('content')
    )

    return Response({'id': post.id, 'content': post.content})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_post(request, post_id):
    post = Post.objects.get(id=post_id)

    like, created = Like.objects.get_or_create(post=post, user=request.user)

    if not created:
        like.delete()
        return Response({'message': 'Unliked', 'likes': post.likes.count()})

    return Response({'message': 'Liked', 'likes': post.likes.count()})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_comment(request, post_id):
    post = Post.objects.get(id=post_id)

    comment = Comment.objects.create(
        post=post,
        author=request.user,
        content=request.data.get('content')
    )

    return Response({
        'author': comment.author.username,
        'content': comment.content
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_comments(request, post_id):
    post = Post.objects.get(id=post_id)
    comments = Comment.objects.filter(post=post).order_by('-created_at')

    data = []
    for comment in comments:
        data.append({
            'author': comment.author.username,
            'content': comment.content,
        })

    return Response(data)


