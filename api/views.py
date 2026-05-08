from django.contrib.auth.models import User
from django.contrib.auth import authenticate as auth_authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from rest_framework import status

from .models import Post, Like, Comment, Profile, Network,Job, Conversation, Message


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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_users(request):
    users = User.objects.exclude(id= request.user.id)
    data = []
    for u in users:
        connection = Network.objects.filter(
            sender= request.user, receiver = u
            ).first()or Network.objects.filter(sender = u , receiver = request.user).first()
        
        data.append({
            'id': u.id,
            'name': u.username,
            'email': u.email,
            'status': connection.status if connection else 'none'
       })
    
    return Response (data)

@api_view(['POST'])
def send_request(request, user_id):
    receiver = User.objects.get(id = user_id)
    if Network.objects.filter(sender = request.user, receiver= receiver).exists():
        return Response({'error': 'Already sent'}, status=400)
    Network.objects.create(sender= request.user, receiver= receiver)
    return Response ({'message': 'Request sent'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_request(request,user_id):
    sender = User.objects.get(id= user_id)
    connection = Network.objects.filter(sender = sender, receiver= request.user).first()
    if not connection:
        return Response({'error': 'Not found'}, status=400)
    
    connection.status = 'accepted'
    connection.save()
    return Response({'message': 'Accepted'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_request(request,user_id):
    sender = User.objects.get(id= user_id)
    connection = Network.objects.filter(sender = sender, receiver= request.user).first()
    if not connection:
        return Response({'error': 'Not found'}, status=400)
    
    connection.status = 'rejected'
    connection.save()
    return Response({'message': 'Rejected'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_connections(request):
    connections = Network.objects.filter(status='accepted').filter(sender=request.user) | \
                  Network.objects.filter(status='accepted').filter(receiver=request.user)


    data=[]
    for c in connections:
        other= c.reciever if c.sender == request.user else c.sender
        data.append({
            'id': other.id,
            'name': other.username,
            'email': other.email
        })
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pending_requests(request):
     requests = Network.objects.filter(
        receiver=request.user,
        status='pending'
    )
     data = []                        
    
     for r in requests:               
        data.append({               
            'id': r.sender.id,
            'name': r.sender.username,
            'email': r.sender.email,
        })
    
     return Response(data) 

@api_view(['GET']) 
@permission_classes([IsAuthenticated])  
def get_jobs(request):
    jobs = Job.objects.all().order_by('-posted')

    job_list =[]

    for job in jobs:
         job_data ={
             'id' : job.id,
             'title': job.title,
             'company':job.company,
             'location':job.location,
             'job_type': job.job_type
             }
         job_list.append(job_data)

    return Response(job_list)   


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversations(request):
    convs = Conversation.objects.filter(participants = request.user)
    data = []
    for c in convs:
        data.append({
            "id" : c.id,
            "participants":[u.username for u in c.participants.all()]

        })
    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_messages(request, conversation_id):
    msgs = Message.objects.filter(conversation_id= conversation_id)
    data =[]
    for m in msgs:
        data.append({
            "sender" : m.sender.username,
            "content": m.content
        })

    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request):
    conversation_id= request.data.get('conversation_id')
    content = request.data.get('content')
    if not conversation_id or not content:
        return Response(
            {"error": "conversation id and content are required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    conv = get_object_or_404(Conversation, id=conversation_id)

    Message.objects.create(
        conversation=conv,
        sender=request.user,
        content=content
    )
    return Response({"message": "sent"}, status=status.HTTP_201_CREATED)