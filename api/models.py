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
