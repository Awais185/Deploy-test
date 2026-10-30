from rest_framework import serializers


class PostTextRequestSerializer(serializers.Serializer):
    post_text = serializers.CharField()


class UpdateCommentStatusRequestSerializer(serializers.Serializer):
    db_id = serializers.IntegerField()
    status = serializers.ChoiceField(
        choices=('PENDING', 'POSTED', 'FAILED', 'SKIPPED'),
    )


class IncomingMessageRequestSerializer(serializers.Serializer):
    sender_name = serializers.CharField(required=False, default='Unknown')
    message = serializers.CharField()


class ProcessNotificationRequestSerializer(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=('message', 'follow'),
        required=False,
        default='message',
    )
    sender_name = serializers.CharField(required=False, default='Unknown')
    message = serializers.CharField(required=False, allow_blank=True, default='')


class GroupURLRequestSerializer(serializers.Serializer):
    group_url = serializers.URLField(required=False, allow_blank=True)


class GenerateCommentResponseSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=('comment', 'skip'))
    comment = serializers.CharField(allow_null=True, required=False)
    db_id = serializers.IntegerField(required=False)
    error = serializers.CharField(required=False)


class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()


class CheckPostResponseSerializer(serializers.Serializer):
    exists = serializers.BooleanField()


class CheckGroupResponseSerializer(serializers.Serializer):
    exists = serializers.BooleanField()


class UpdateCommentStatusResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(required=False)
    error = serializers.CharField(required=False)


class IncomingMessageResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(required=False)
    reply = serializers.CharField(required=False)
    id = serializers.IntegerField(required=False)
    error = serializers.CharField(required=False)


class ProcessNotificationResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    reply = serializers.CharField()


class SaveGroupResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    created = serializers.BooleanField(required=False)
    error = serializers.CharField(required=False)


class WelcomeMessageResponseSerializer(serializers.Serializer):
    welcome_text = serializers.CharField()
