import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

# from capture.utils import run_task_capture, run_task_remove


class CaptureConsumer(WebsocketConsumer):
    def connect(self):
        self.room_group_name = "capture_kohn"

        print("conntected ", self.room_group_name, self.channel_name)

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        print("received message: ", message)


    # Receive message from room group
    def chat_message(self, event):
        print(event)

        # Send message to WebSocket
        self.send(text_data=json.dumps(event))
    