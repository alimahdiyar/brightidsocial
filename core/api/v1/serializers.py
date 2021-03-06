import uuid

from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers

from brightidsocial.settings import ALLOWED_HASH_COUNT
from core.consts import BrightIdNetwork
from core.models import SocialMedia, SocialMediaVariation, ProfileHash


class SocialMediaVariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialMediaVariation
        fields = (
            'id',
            'name',
            'icon',
            'type',
            'share_type',
            'share_type_display',
            'share_action_type',
            'share_action_data_format',
            'bright_id_app_id',
        )


class SocialMediaUpdateSerializer(serializers.ModelSerializer):
    profile_hashes = serializers.ListField(child=serializers.CharField(max_length=32), write_only=True, max_length=ALLOWED_HASH_COUNT)

    class Meta:
        model = SocialMedia
        fields = (
            'profile_hashes',
        )

    def update(self, instance, validated_data):
        with transaction.atomic():
            profile_hashes = validated_data.pop('profile_hashes')
            instance.profile_hashes.all().delete()
            for value in profile_hashes:
                ProfileHash.objects.create(
                    social_media=instance,
                    value=value
                )
            instance.save()
        return instance


class SocialMediaCreateSerializer(serializers.ModelSerializer):
    profile_hashes = serializers.ListField(child=serializers.CharField(max_length=32), write_only=True, max_length=3)

    class Meta:
        model = SocialMedia
        fields = (
            'app_user_id',
            'token',
            'network',
            'variation',
            'profile_hashes',
        )


    def create(self, validated_data):
        with transaction.atomic():
            profile_hashes = validated_data.pop('profile_hashes')
            django_user = User.objects.create_user(
                # random, with no purpose
                username=uuid.uuid4().hex[:30]
            )
            instance = SocialMedia.objects.create(
                **validated_data,
                django_user=django_user
            )
            for value in profile_hashes:
                ProfileHash.objects.create(
                    social_media=instance,
                    value=value
                )
        return instance


class SocialMediaVerifySerializer(serializers.Serializer):
    app_user_id = serializers.UUIDField()
    network = serializers.ChoiceField(
        choices=BrightIdNetwork.choices,
    )


class SocialMediaQueryAPISerializer(serializers.Serializer):
    profile_hashes = serializers.ListField(child=serializers.CharField(max_length=32))
    network = serializers.ChoiceField(
        default=BrightIdNetwork.NODE,
        choices=BrightIdNetwork.choices,
    )


class SocialMediaQueryResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileHash
        fields = (
            'profile_hash',
            'variation'
        )
