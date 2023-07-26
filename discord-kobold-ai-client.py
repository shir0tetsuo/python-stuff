# This is a basic Discord-AI handler (For KobaldAI aiserver). Fine tune as needed
import discord
from discord.ext import commands
import requests
import json
import re

# Put your (Colab TPU /api/v1/generate or localhost:port/api/v1/generate) URL here
url = 'https://.trycloudflare.com/api/v1/generate'

# Put your Discord token here
discord_token = ""
bot_userid = ""

# Put your character in chub format
AICharacter = ""

chats = {}

def parse_json_string(json_string):
    try:
        json_object = json.loads(json_string)
        return json_object
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None


def remove_mentions(message):
    # Regular expression to match Discord mentions
    mention_pattern = r'\<@{}\>'.format(bot_userid)
    # Replace all mentions with an empty string
    cleaned_message = re.sub(mention_pattern, '', message)
    return cleaned_message

class MyClient(discord.Client):
    async def on_ready(self):
        print('👍 Bot is ready')

    async def on_message(self, message):
        # Ping to chat
        if not bot_userid in message.content:
            return

        if len(remove_mentions(message.content)) == 0:
            return
        
        async with message.channel.typing():
            
            message_author = str(message.author.id)
            author_name = str(message.author.name)

            # This is the prompt
            user_message = f'\nYou: '+remove_mentions(message.content)+'\nOshiko:'

            if chats.get(message_author) is not None:
                chat_record = chats[message_author]['ChatRecord'] + user_message
            else:
                chats[message_author] = {'ChatRecord': AICharacter + user_message}
                chat_record = chats[message_author]['ChatRecord']

            if len(chat_record.split()) > 2048:
                print('Had to trim!')
                chat_record = AICharacter + chat_record.replace(AICharacter,'')[1024:]

            # Send chat_record / user_message with that.
            headers = {
                'Content-Type': 'application/json'
            }

            # Edit some settings
            data = {
                'prompt': chat_record,
                'use_story': False,
                'use_memory': False,
                'use_authors_note': False,
                'use_world_info': False,
                'max_context_length': 2048,
                'max_length': 150,
                'rep_pen': 1.03, # repetition penalty
                'rep_pen_range': 120,
                'rep_pen_slope': 0.8,
                'temperature': 1.08,
                'tfs': 0.96,
                'top_a': 0,
                'top_k': 28,
                'top_p': 0.94,
                'typical': 0.98,
                'sampler_order': [ 6, 4, 3, 2, 0, 1, 5 ] }
            
            response = requests.post(url, json=data, headers=headers)
            try:
                response_data = parse_json_string(response.text)
                to_discord = response_data['results'][0]['text']
                await message.channel.send(to_discord,reference=message)
            except Exception as exc:
                print(exc)
        
        #return print(data,response)

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(discord_token)
