import os
import requests
from dotenv import load_dotenv

load_dotenv()

# === НАСТРОЙКИ MAILGUN ===
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")  # Ваш Private API Key
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN", "sandboxXXXXXX.mailgun.org")  # Ваш домен Mailgun
EMAIL_FROM = f"Fortis Chatbot <bot@{MAILGUN_DOMAIN}>"  # Отправитель
EMAIL_TO = os.getenv("EMAIL_TO", "fmd@fortis-steel.ru")  # Получатель

def send_application_email(text: str, amount: int):
    """Отправка заявки через Mailgun API."""
    try:
        # Проверяем API ключ
        if not MAILGUN_API_KEY:
            print("⚠️ MAILGUN_API_KEY не настроен. Письмо не будет отправлено.")
            return
        
        # Данные для письма
        email_data = {
            "from": EMAIL_FROM,
            "to": EMAIL_TO,
            "subject": f"🚀 Новая заявка с сайта Fortis: {amount} руб.",
            "text": f"Поступила заявка на сумму {amount} руб.\n\nТекст заявки:\n{text}\n\n---\nОтправлено чат-ботом сайта Fortis Steel"
        }
        
        # URL для Mailgun API
        mailgun_url = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"
        
        # Отправляем через Mailgun API (Basic Auth)
        response = requests.post(
            mailgun_url,
            auth=("api", MAILGUN_API_KEY),  # Mailgun использует Basic Auth
            data=email_data,
            timeout=10
        )
        
        # Проверяем ответ
        if response.status_code == 200:
            print(f"✅ Email успешно отправлен на {EMAIL_TO} через Mailgun API")
            print(f"   ID сообщения: {response.json().get('id', 'unknown')}")
        else:
            print(f"⚠️ Mailgun API вернул ошибку {response.status_code}")
            print(f"   Ответ: {response.text[:150]}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {str(e)}")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {str(e)}")

# === ТЕСТОВАЯ ФУНКЦИЯ (удалите после теста) ===
def test_mailgun_connection():
    """Тестируем подключение к Mailgun."""
    print("\n🔍 Тестируем подключение к Mailgun...")
    
    if not MAILGUN_API_KEY:
        print("❌ MAILGUN_API_KEY не найден в переменных окружения")
        return False
    
    try:
        # Простой запрос для проверки домена
        response = requests.get(
            f"https://api.mailgun.net/v3/domains/{MAILGUN_DOMAIN}",
            auth=("api", MAILGUN_API_KEY),
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Подключение к Mailgun успешно!")
            print(f"   Домен: {MAILGUN_DOMAIN}")
            return True
        else:
            print(f"❌ Ошибка доступа к домену: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

# Запускаем тест при импорте (удалите после проверки)
print("\n🚀 Проверяем настройки Mailgun...")
test_mailgun_connection()
