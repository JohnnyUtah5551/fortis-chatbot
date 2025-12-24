import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import requests
from chatbot_logic import generate_bot_reply, check_interesting_application
from email_utils import send_application_email
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем папку static, чтобы отдавать widget.js
app.mount("/static", StaticFiles(directory="static"), name="static")

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")


@app.post("/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    user_message = data.get("message", "")

    # Генерируем ответ бота через Replicate API
    bot_reply = generate_bot_reply(REPLICATE_API_TOKEN, user_message)

    # Проверяем, является ли сообщение интересной заявкой
    is_interesting, amount = check_interesting_application(user_message)

    if is_interesting:
        send_application_email(user_message, amount)

    return {"reply": bot_reply}

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "chatbot-api"}

@app.get("/")
async def root():
    return {
        "service": "Fortis Chatbot API", 
        "status": "running",
        "endpoints": {
            "chat": "/chat (POST)",
            "health": "/health (GET)"
        }
    }
