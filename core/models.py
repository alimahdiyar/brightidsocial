from typing import Callable
from uuid import uuid4
from xmlrpc.client import Boolean

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext as _
from rest_framework.authtoken.models import Token

from core.consts import SocialMediaType, SocialMediaShareTypeDisplay, \
    SocialMediaShareType, SocialMediaShareActionType, \
    BrightIdNetwork, SocialMediaBrightVerificationStatus


class SocialMediaVariation(models.Model):
    """
        Social Media types and platforms that we support.
    """
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=255)
    icon = models.TextField(blank=True, null=True)

    type = models.CharField(
        max_length=2,
        choices=SocialMediaType.choices,
        default=SocialMediaType.SOCIAL_PROFILE,
    )

    share_type = models.CharField(
        max_length=20,
        choices=SocialMediaShareType.choices,
        default=SocialMediaShareType.USERNAME,
    )

    share_type_display = models.CharField(
        max_length=40,
        choices=SocialMediaShareTypeDisplay.choices,
        default=SocialMediaShareTypeDisplay.USERNAME,
    )

    share_action_type = models.CharField(
        max_length=2,
        choices=SocialMediaShareActionType.choices,
        default=SocialMediaShareActionType.OPEN_LINK,
    )

    share_action_data_format = models.CharField(max_length=100)
    bright_id_app_id = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name


class SocialMedia(models.Model):
    """
        A social media profile that the user added
    """
    id = models.UUIDField(primary_key=True, default=uuid4)
    django_user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="social_media")
    network = models.CharField(
        max_length=20,
        choices=BrightIdNetwork.choices,
        default=BrightIdNetwork.NODE
    )
    bright_verification_status = models.CharField(
        max_length=1,
        choices=SocialMediaBrightVerificationStatus.choices,
        default=SocialMediaBrightVerificationStatus.PENDING
    )
    variation = models.ForeignKey(
        SocialMediaVariation, on_delete=models.PROTECT, related_name="social_medias")

    @property
    def app_user_id(self):
        """
            Used in BrightID app
        """
        return self.id

    @property
    def token(self):
        """
            Authentication Token
        """
        token, created = Token.objects.get_or_create(user=self.django_user)
        return token.key

    def __str__(self):
        return self.variation.name + ' ' + str(self.app_user_id)

    def get_and_save_verification_status(self, is_user_app_id_linked_func: Callable) -> (Boolean, dict):
        if self.bright_verification_status == SocialMediaBrightVerificationStatus.VERIFIED:
            return True, {}

        app_name = self.variation.bright_id_app_id
        if not app_name:
            response = {
                'error': True,
                'errorMessage': _('Verification not available for this social media variation'
                                  )}
            return False, response

        network = self.network
        user_app_id = self.app_user_id
        response = is_user_app_id_linked_func(network, app_name, user_app_id)
        if 'error' in response:
            return False, response

        self.bright_verification_status = SocialMediaBrightVerificationStatus.VERIFIED
        self.save()
        return True, {}


class ProfileHash(models.Model):
    """
        Hash of different profile representations.
        For example, a user might save a phone number with or without
        the country code in their contacts. So we store the hash value from
        both representations
    """
    social_media = models.ForeignKey(
        SocialMedia, on_delete=models.CASCADE, related_name='profile_hashes')
    value = models.CharField(max_length=32)

    @property
    def profile_hash(self):
        return self.value

    @property
    def variation(self):
        return self.social_media.variation

    def __str__(self):
        return self.value

    class Meta:
        indexes = [models.Index(fields=['value'])]
