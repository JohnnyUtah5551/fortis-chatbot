import os
import requests
from dotenv import load_dotenv

load_dotenv()

# НАСТРОЙКИ MAILGUN API
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")  # Ключ из Mailgun Dashboard
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN", "sandboxXXX.mailgun.org")  # Ваш домен Mailgun
EMAIL_FROM = f"Чат-бот Fortis <bot@{MAILGUN_DOMAIN}>"  # Отправитель
EMAIL_TO = os.getenv("EMAIL_TO", "fmd@fortis-steel.ru")  # Получатель

def send_application_email(text: str, amount: int):
    """Отправка заявки через Mailgun API."""
    try:
        # Проверяем API ключ
        if not MAILGUN_API_KEY:
            print("⚠️ MAILGUN_API_KEY не настроен. Письмо не будет отправлено.")
            return
        
        # Данные для Mailgun API
        email_data = {
            "from": EMAIL_FROM,
            "to": [EMAIL_TO],
            "subject": f"🚀 Новая заявка с сайта Fortis: {amount} руб.",
            "text": f"Поступила заявка на сумму {amount} руб.\n\nТекст заявки:\n{text}\n\n---\nОтправлено чат-ботом сайта Fortis Steel"
        }
        
        # Отправляем через Mailgun API
        response = requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),  # Basic Auth для Mailgun
            data=email_data,
            timeout=10
        )
        
        # Проверяем ответ
        if response.status_code == 200:
            print(f"✅ Email успешно отправлен на {EMAIL_TO} через Mailgun API")
        else:
            print(f"⚠️ Mailgun API вернул ошибку {response.status_code}: {response.text[:100]}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {str(e)}")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {str(e)}")
