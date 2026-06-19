import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
        else:
            # Create a unique group for this user
            self.user_group_name = f"user_{self.user.id}"

            # Join user group
            await self.channel_layer.group_add(
                self.user_group_name,
                self.channel_name
            )

            # Join global broadcast group
            await self.channel_layer.group_add(
                "global_notifications",
                self.channel_name
            )

            await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group_name'):
            # Leave user group
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
            # Leave global group
            await self.channel_layer.group_discard(
                "global_notifications",
                self.channel_name
            )

    # Receive message from room group
    async def send_notification(self, event):
        html = event["html"]

        # Send HTML snippet down the WebSocket for HTMX to swap
        await self.send(text_data=html)
