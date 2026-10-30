from django.db import models



class GeneratedComment(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('POSTED', 'Posted'),
        ('FAILED', 'Failed'),
        ('SKIPPED', 'Skipped'),
    )
    
    post_text = models.TextField()
    ai_comment = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.status} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class IncomingReply(models.Model):
    sender_name = models.CharField(max_length=255, blank=True, null=True)
    original_post_text = models.TextField(blank=True, null=True) # The group post
    our_comment = models.TextField(blank=True, null=True) # What we commented
    client_reply = models.TextField() # What they replied
    ai_response = models.TextField(blank=True, null=True) # What AI replies back
    status = models.CharField(max_length=50, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender_name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class JoinedGroup(models.Model):
    group_url = models.URLField(max_length=500, unique=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.group_url

class WelcomeTemplate(models.Model):
    message_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)