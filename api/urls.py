from django.urls import path
from .views import GenerateCommentView, CheckPostView, UpdateCommentStatusView, IncomingMessageView, ProcessNotificationView, CheckGroupView, SaveGroupView, GetWelcomeMessageView

urlpatterns = [
    path('generate-comment/', GenerateCommentView.as_view(), name='generate_comment'),
    path('check-post/', CheckPostView.as_view(), name='check_post'),
    path('update-status/', UpdateCommentStatusView.as_view(), name='update_status'), # NEW
    path('incoming-message/', IncomingMessageView.as_view(), name='incoming_message'),
    path('process-notification/', ProcessNotificationView.as_view(), name='process_notification'),
    path('check-group/', CheckGroupView.as_view(), name='check_group'),
    path('save-group/', SaveGroupView.as_view(), name='save_group'),
    path('get-welcome/', GetWelcomeMessageView.as_view(), name='get_welcome'),


]