from django.contrib.auth.models import User
from django.contrib.auth import authenticate as auth_authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Post, Like, Comment, Profile, Network,Job, Conversation, Message, Notification


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

        'profile_picture': request.build_absolute_uri(profile.profile_picture.url)
                           if profile.profile_picture else None,
        'cover_picture':   request.build_absolute_uri(profile.cover_picture.url)
                           if profile.cover_picture else None,
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
            "content": m.content,
            "is_mine": m.sender == request.user 
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_conversation(request):
    username = request.data.get('username')
    
    if not username:
        return Response(
            {"error": "username required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
   
    try:
        recipient = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response(
            {"error": "User not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    
    existing = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=recipient
    ).first()
    
    if existing:
        return Response({"id": existing.id}, status=status.HTTP_200_OK)
    
   
    conv = Conversation.objects.create()
    conv.participants.add(request.user, recipient)
    conv.save()
    
    return Response({"id": conv.id}, status=status.HTTP_201_CREATED)


def _time_ago(created_at):
    now  = timezone.now()
    diff = now - created_at
    if diff < timedelta(minutes=1): return "just now"
    if diff < timedelta(hours=1):   return f"{int(diff.seconds // 60)}m"
    if diff < timedelta(days=1):    return f"{int(diff.seconds // 3600)}h"
    if diff < timedelta(days=7):    return f"{diff.days}d"
    return created_at.strftime("%b %d")


def _build_message(n):
    try:
        sender_name = n.sender.username if n.sender else "Someone"
        msgs = {
            'like':               f"{sender_name} liked your post.",
            'comment':            f"{sender_name} commented on your post.",
            'connection_request': f"{sender_name} sent you a connection request.",
            'connection_accept':  f"{sender_name} accepted your connection request.",
            'profile_view':       f"{sender_name} viewed your profile.",
            'job_alert':          f"New job: {n.job.title} at {n.job.company}" if n.job else "New job posted.",
            'mention':            f"{sender_name} mentioned you in a post.",
        }
        return msgs.get(n.notif_type, "You have a new notification.")
    except Exception:
        return "You have a new notification."
 
 
def _notif_to_dict(n):
    try:
        sender_data = {
            'username': n.sender.username,
            'profile_picture': (
                n.sender.profile.profile_picture.url
                if hasattr(n.sender, 'profile') and n.sender.profile.profile_picture
                else None
            )
        } if n.sender else None
    except Exception:
        sender_data = None
 
    return {
        'id':         n.id,
        'notif_type': n.notif_type,
        'message':    _build_message(n),
        'is_read':    n.is_read,
        'time_ago':   _time_ago(n.created_at),
        'sender':     sender_data,
        'job_url':    None,
    }
 


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notifications_view(request):
    
    filter_type = request.GET.get('filter', 'all')  

    notifications = Notification.objects.filter(recipient=request.user)

    if filter_type == 'jobs':
        notifications = notifications.filter(notif_type='job_alert')
    elif filter_type == 'my_posts':
        notifications = notifications.filter(notif_type__in=['like', 'comment'])
    elif filter_type == 'mentions':
        notifications = notifications.filter(notif_type='mention')
  

   
    notifications.update(is_read=True)

    unread_count = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).count()

    context = {
        'notifications': notifications,
        'filter_type':   filter_type,
        'unread_count':  unread_count,
    }
    data = [_notif_to_dict(n) for n in notifications]
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unread_count_view(request):
   
    count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    return JsonResponse({'unread_count': count})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_read_view(request, notif_id):
    
    
    notif = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    notif.mark_as_read()
    return JsonResponse({'status': 'ok', 'id': notif_id})



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_read_view(request):
    
    updated = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)
    return JsonResponse({'status': 'ok', 'marked_read': updated})




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_notification_view(request, notif_id):
    
    notif = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    notif.delete()
    return JsonResponse({'status': 'deleted', 'id': notif_id})




def create_like_notification(liker, post):
    
    if post.author != liker:
        Notification.objects.create(
            recipient  = post.author,
            sender     = liker,
            notif_type = 'like',
            post       = post,
        )

def create_comment_notification(commenter, post, comment):
   
    if post.author != commenter:
        Notification.objects.create(
            recipient  = post.author,
            sender     = commenter,
            notif_type = 'comment',
            post       = post,
            comment    = comment,
        )

def create_connection_request_notification(sender, receiver):
    
    Notification.objects.create(
        recipient  = receiver,
        sender     = sender,
        notif_type = 'connection_request',
    )

def create_connection_accept_notification(acceptor, original_sender):
    
    Notification.objects.create(
        recipient  = original_sender,
        sender     = acceptor,
        notif_type = 'connection_accept',
    )

def create_profile_view_notification(viewer, profile_owner):
    
    if viewer != profile_owner:
        Notification.objects.create(
            recipient  = profile_owner,
            sender     = viewer,
            notif_type = 'profile_view',
        )

def create_job_alert_notification(job, recipient):
   
    Notification.objects.create(
        recipient  = recipient,
        sender     = None,       
        notif_type = 'job_alert',
        job        = job,
    )