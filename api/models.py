from django.db import models
from django.contrib.auth.models import User

# User Profile
class Profile(models.Model):
    user             = models.OneToOneField(User, on_delete=models.CASCADE)
    location         = models.CharField(max_length=100, blank=True)
    bio              = models.TextField(blank=True)
    headline         = models.CharField(max_length=200, blank=True)
    profile_picture  = models.ImageField(upload_to='profiles/', blank=True)
    cover_picture    = models.ImageField(upload_to='covers/', blank=True)
    profile_viewers  = models.IntegerField(default=0)
    post_impressions = models.IntegerField(default=0)
    
    exp_title   = models.CharField(max_length=100, blank=True)
    exp_company = models.CharField(max_length=100, blank=True)
    exp_date    = models.CharField(max_length=100, blank=True)
    
    edu_school = models.CharField(max_length=100, blank=True)
    edu_degree = models.CharField(max_length=100, blank=True)
    edu_date   = models.CharField(max_length=100, blank=True)
    
    skills = models.TextField(blank=True)  

    def __str__(self):
        return self.user.username

# Post
class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author.username} - {self.content[:30]}"

# Like
class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

# Comment
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

#Network

class Network(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name= 'sent_requests')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name= 'recieve_requests')
    status = models.CharField(max_length=20, choices=[
        ('pending','Pending'),
        ('accepted','Accepted'),
        ('rejected','Rejected'),
        ], default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('sender', 'receiver')

    def __str__(self):
        return f"{self.sender.username}  → {self.receiver.username} ({self.status})"

class Job(models.Model):
    company = models.CharField(max_length=200)
    job_type = models.CharField(max_length=200, default= "Full-time")
    location = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    posted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title}- {self.company}" 
    

class Conversation(models.Model):
    participants = models. ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        names = ", ".join([u.username for u in self.participants.all()])
        return f"Conversation: {names}"
    
    def last_message(self):
        return self.messages.order_by('-sent_at').first()
     
    def unread_count(self, user):
        return self.messages.filter(is_read = False).exclude(sender= user).count()
    
class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender= models.ForeignKey(User,on_delete=models.CASCADE, related_name='sent_messages')
    content= models.TextField()
    is_read= models.BooleanField(default=False)
    sent_at= models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sent_at']
  
    def __str__(self):
        return f"{self.sender.username}: {self.content[:40]}"
    


class Notification(models.Model):
 
    
    NOTIF_TYPE = [
        ('like',               'Like'),               
        ('comment',            'Comment'),            
        ('connection_request', 'Connection Request'),  
        ('connection_accept',  'Connection Accept'),   
        ('profile_view',       'Profile View'),        
        ('job_alert',          'Job Alert'),           
        ('mention',            'Mention'),            
    ]
 
    
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
 
    
    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sent_notifications'
    )
 
    notif_type = models.CharField(max_length=30, choices=NOTIF_TYPE)
 
   
    post = models.ForeignKey(        
        Post,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='notifications'
    )
    comment = models.ForeignKey(      
        Comment,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='notifications'
    )
    network = models.ForeignKey(      
        Network,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='notifications'
    )
    job = models.ForeignKey(          
        Job,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='notifications'
    )
 
    
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ['-created_at']  
 
    def __str__(self):
        return f"[{self.notif_type}] → {self.recipient.username} | read={self.is_read}"
 
    def mark_as_read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])
 
   
    def get_message(self):
        sender_name = self.sender.get_full_name() or self.sender.username if self.sender else "Someone"
 
        messages = {
            'like' : f"{sender_name} liked your post.",
            'comment' : f"{sender_name} commented on your post.",
            'connection_request' : f"{sender_name} sent you a connection request.",
            'connection_accept' : f"{sender_name} accepted your connection request.",
            'profile_view' : f"{sender_name} viewed your profile.",
            'job_alert' : f"New job alert:{self.job.title}at{self.job.company}",

        }

        return messages.get( self.notif_type,"You have a new notification.")