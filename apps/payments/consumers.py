# apps/payments/consumers.py
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from uuid import UUID

from apps.payments.services import PaymentService


class PaymentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.payment_id = self.scope['url_route']['kwargs']['payment_id']
        self.payment_group_name = f'payment_{self.payment_id}'

        # Join payment group
        await self.channel_layer.group_add(
            self.payment_group_name,
            self.channel_name
        )

        # Check if payment exists and user has permission
        user_id = self.scope['user'].id if self.scope['user'].is_authenticated else None
        if not user_id:
            await self.close()
            return

        # Verify payment exists and belongs to user
        payment = await PaymentService.get_by_id(UUID(self.payment_id), user_id)
        if not payment:
            await self.close()
            return

        await self.accept()

        # Start background task to check payment status
        asyncio.create_task(self.check_payment_status())

    async def disconnect(self, close_code):
        # Leave payment group
        await self.channel_layer.group_discard(
            self.payment_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'check_status':
            # Manually trigger a status check
            user_id = self.scope['user'].id if self.scope['user'].is_authenticated else None
            status_info = await PaymentService.check_payment_status(UUID(self.payment_id), user_id)
            await self.send_status_update(status_info)

    async def payment_status_update(self, event):
        # Send payment status update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'payment_status',
            'status': event['status'],
            'verification_status': event['verification_status'],
            'message': event['message'],
            'timestamp': event['timestamp']
        }))

    async def check_payment_status(self):
        """Background task to periodically check payment status"""
        user_id = self.scope['user'].id if self.scope['user'].is_authenticated else None

        while True:
            # Check payment status
            status_info = await PaymentService.check_payment_status(UUID(self.payment_id), user_id)

            # Send status update
            await self.send_status_update(status_info)

            # If payment is no longer pending, stop checking
            if status_info['status'] not in ['pending', 'error']:
                break

            # Check every 5 seconds
            await asyncio.sleep(5)

    async def send_status_update(self, status_info):
        await self.channel_layer.group_send(
            self.payment_group_name,
            {
                'type': 'payment_status_update',
                **status_info
            }
        )


# apps/payments/routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/payments/<uuid:payment_id>/', consumers.PaymentConsumer.as_asgi()),
]