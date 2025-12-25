import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

# НАСТРОЙКИ ДЛЯ ЯНДЕКСА (исправленные!)
EMAIL_HOST = "smtp.yandex.ru"          # Обязательно smtp.yandex.ru
EMAIL_PORT = 465                        # Для SSL, а не 587!
EMAIL_USER = os.getenv("EMAIL_USER")    # Ваша почта 229@fortis-steel.ru
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # Пароль приложения
EMAIL_TO = os.getenv("EMAIL_TO", "fmd@fortis-steel.ru")  # Получатель

def send_application_email(text: str, amount: int):
    """Отправка заявки на email."""
    try:
        # Создаем сообщение
        msg = MIMEText(f"Поступила заявка на сумму {amount} руб.\n\nТекст заявки:\n{text}")
        msg["Subject"] = f"🚀 Заявка с сайта Fortis: {amount} руб"
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_TO
        
        # Подключаемся к SMTP серверу Яндекса (с SSL!)
        with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT) as server:  # SMTP_SSL вместо SMTP!
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
            print(f"✅ Email отправлен на {EMAIL_TO}")
            
    except Exception as e:
        print(f"❌ Ошибка отправки email: {str(e)}")
        # НЕ поднимаем исключение дальше, чтобы бот продолжал работать
