from functools import reduce
from operator import or_

import requests as requests
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.api.v1.serializers import SocialMediaVariationSerializer, \
    SocialMediaVerifySerializer, SocialMediaCreateSerializer, SocialMediaUpdateSerializer, \
    SocialMediaQueryAPISerializer, SocialMediaQueryResponseSerializer
from core.consts import SocialMediaBrightVerificationStatus
from core.models import SocialMediaVariation, SocialMedia, ProfileHash


class SocialMediaVariationListView(generics.ListAPIView):
    """
        List social media variations
    """
    serializer_class = SocialMediaVariationSerializer
    queryset = SocialMediaVariation.objects.all()


class SocialMediaCreateView(generics.CreateAPIView):
    """
        Create or Update social media profile
    """
    serializer_class = SocialMediaCreateSerializer


class SocialMediaUpdateView(generics.UpdateAPIView):
    """
        Update social profile of user
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = SocialMediaUpdateSerializer

    def get_object(self):
        return self.request.user.social_media


class SocialMediaVerifyView(generics.GenericAPIView):
    """
        Check if BrightID app linked the social media profile
    """
    serializer_class = SocialMediaVerifySerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        network = serializer.validated_data.get('network')
        context_id = serializer.validated_data.get('context_id')
        social_media = get_object_or_404(SocialMedia,
                                         id=context_id,
                                         network=network
                                         )

        if social_media.bright_verification_status == \
                SocialMediaBrightVerificationStatus.VERIFIED:
            return Response(status=204)

        app_name = social_media.variation.bright_id_app_name

        if app_name:
            response = requests.get(
                f'http://{network}.brightid.org/brightid/'
                f'v6/verifications/{app_name}/{social_media.id}'
            ).json()
            if 'error' in response:
                return Response(response, 400)

            social_media.bright_verification_status = \
                SocialMediaBrightVerificationStatus.VERIFIED
            return Response(status=204)

        return Response({
            'error': True,
            'errorMessage': _('Verification not available for this social media variation'
                              )}, 400)


class SocialMediaDeleteView(generics.DestroyAPIView):
    """
        Remove social profile of user from search queries
    """
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user.social_media

    def perform_destroy(self, instance):
        instance.profile_hashes.delete()


class SocialMediaQueryView(generics.GenericAPIView):
    """
        Find social profiles that are registered in the app
    """
    serializer_class = SocialMediaQueryAPISerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        network = serializer.validated_data.get('network')
        profile_hashes = serializer.validated_data.get('profile_hashes')

        profile_hash_qs = ProfileHash.objects.filter(
            value__in=profile_hashes,
            social_media_network=network,
            social_media_bright_verification_status=SocialMediaBrightVerificationStatus.VERIFIED,
        )

        return Response(SocialMediaQueryResponseSerializer(profile_hash_qs, many=True).data, status=200)
