import os
import json
import openai
from openai import OpenAI
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
client = OpenAI(api_key=os.environ.get('OPENAI_APIKEY'))
class ChatConsumer(WebsocketConsumer):
     def connect(self):
        # Generate or retrieve the session key for anonymous users
        if not self.scope['session'].session_key:
            self.scope['session'].save()
        print(self.scope['session'].session_key)
        if 'thread_id' not in self.scope['session']:
            # Generate a new assistant thread ID (you can create a UUID or similar identifier)
            thread = client.beta.threads.create()

            self.scope['session']['thread_id'] = thread.id

            # Save the session to persist the assistant thread ID
            self.scope['session'].save()

        # Use the session key as the room name for anonymous users
        self.thread_id = self.scope['session']['thread_id']
        self.room_group_name = f"chat_{self.thread_id}"

        self.accept()
        # Join the unique room for this session
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name,
        )

     def disconnect(self, close_code):
        # Leave the room when the WebSocket connection is closed
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name,
        )

     def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        response = self.get_response(message)

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': response,
            }
        )
     def chat_message(self, event):
        self.send(text_data=json.dumps(event))

     def get_response(self,user_message):
        message = client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role='user',
            content=user_message
        )
        run = client.beta.threads.runs.create_and_poll(
            thread_id=self.thread_id,
            assistant_id='asst_BunrX4vdD5yRKBIhrbuDohIi',
        ) 
        if run.status == 'completed': 
            messages = client.beta.threads.messages.list(
                thread_id=self.thread_id
            )
            return messages.data[0].content[0].text.value
        else:
            return run.status