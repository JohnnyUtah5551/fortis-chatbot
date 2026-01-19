import os
import requests  # <-- Теперь используем requests для API
from dotenv import load_dotenv

load_dotenv()

# НАСТРОЙКИ RESEND API (единственный рабочий вариант для Render)
RESEND_API_KEY = os.getenv("RESEND_API_KEY")  # Ваш API ключ с resend.com
EMAIL_FROM = "notify@fortis-steel.ru"  # Отправитель (должен быть verified в Resend)
EMAIL_TO = os.getenv("EMAIL_TO", "fmd@fortis-steel.ru")  # Получатель

def send_application_email(text: str, amount: int):
    """Отправка заявки через Resend API (работает на Render)."""
    try:
        # Проверяем, есть ли API ключ
        if not RESEND_API_KEY:
            print("⚠️ RESEND_API_KEY не настроен. Письмо не будет отправлено.")
            return
        
        # Формируем письмо для Resend API
        email_data = {
            "from": f"Чат-бот Fortis <{EMAIL_FROM}>",
            "to": [EMAIL_TO],
            "subject": f"🚀 Новая заявка с сайта на {amount} руб.",
            "text": f"Поступила заявка на сумму {amount} руб.\n\nТекст заявки:\n{text}\n\n---\nОтправлено чат-ботом сайта Fortis Steel"
        }
        
        # Отправляем через Resend API
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json=email_data,
            timeout=10  # Таймаут 10 секунд
        )
        
        # Проверяем ответ
        if response.status_code == 200:
            print(f"✅ Email успешно отправлен на {EMAIL_TO} через Resend API")
        else:
            # Логируем ошибку от API, но не ломаем бота
            print(f"⚠️ Resend API вернул ошибку {response.status_code}: {response.text[:100]}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети при отправке email: {str(e)}")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {str(e)}")
