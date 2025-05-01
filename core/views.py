from typing import Type, Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime

from django.http import Http404
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated


class AsyncView(APIView):
    """Base class for async API views."""
    permission_classes = [IsAuthenticated]
    service_class = None

    async def get_object(self, pk, user_id=None):
        """Get object by ID with optional user filtering."""
        if not self.service_class or not hasattr(self.service_class, 'get_by_id'):
            raise NotImplementedError("Service class must implement get_by_id")

        obj = await self.service_class.get_by_id(pk, user_id)
        if obj is None:
            raise Http404
        return obj