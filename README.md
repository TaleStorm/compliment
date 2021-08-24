This is an open source python project based on [`aiogram`](https://github.com/aiogram/aiogram) and [`pyrogram`](https://github.com/pyrogram/pyrogram)

# Compliment
It's a telegram bot for busy people that helps not to forget to text somebody during the day and does it for you.  
Project consist of 2 parallel working scripts.  
The first one is telegram bot which serves as a interface for creating contacts which will reseve messages from you.  
And the second one is pyrogram script which activate your or other telegram clients and send messages from it.

You can use our telegram bot [`@ComplimentTaleStormBot`](https://t.me/ComplimentTaleStormBot) or for security reasons run your own on your machine.  
#### For the second option follow the next steps.

# Getting started

## Get bot token
For the first you should create you telegram bot in Telegram [BotFather](https://t.me/botfather).  
You can read how to do it [here](https://core.telegram.org/bots).  
Then save your BotToken.

## Get telegram api id and hash
The next step is get `api_id` and `api hash` from [Telegram Core](https://my.telegram.org/auth).  
Authorize with your phone number and then go to `API development tools`.  
Create your application with any App Title and Short Name.  
Then save it and you will get `api_id` and `api hash`


![alt text](https://i.ibb.co/mRDgYT3/2021-08-24-13-35-34.png)

Now you have all data to get started.

## .env
Create `.env` file in main path of cloned project and add your tokens to it.  
You can find example in repository.  

## Run project
The project consists of 2 scripts and you should run it in diffrent terminals by two commands:  
`python bot.py`  
`python client.py`  

Now you can interract with it by your bot.
