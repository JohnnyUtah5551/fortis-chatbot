import os
import smtplib
import socket  # <-- ДОБАВЛЕНО ДЛЯ ТЕСТА
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

# ===================================================
# ТЕСТ СЕТИ RENDER (удалите после получения результатов)
# ===================================================
def test_render_network_capabilities():
    """Тестируем, какие сетевые возможности есть у Render."""
    print("\n" + "="*60)
    print("🔍 ТЕСТ СЕТЕВЫХ ВОЗМОЖНОСТЕЙ RENDER")
    print("="*60)
    
    # 1. Тест DNS (разрешение имен)
    print("\n1. 🌐 DNS разрешение:")
    try:
        ip_address = socket.gethostbyname("smtp.yandex.ru")
        print(f"   ✅ DNS работает: smtp.yandex.ru → {ip_address}")
    except Exception as e:
        print(f"   ❌ DNS не работает: {e}")
    
    # 2. Тест разных SMTP портов
    print("\n2. 📡 Тест SMTP портов Яндекс:")
    ports_to_test = [
        (465, "SSL (основной для Яндекс)"),
        (587, "STARTTLS (альтернативный)"),
        (25, "SMTP стандартный"),
    ]
    
    for port, description in ports_to_test:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)  # 3 секунды таймаут
            result = sock.connect_ex(("smtp.yandex.ru", port))
            
            if result == 0:
                print(f"   Порт {port} ({description}): ✅ ОТКРЫТ")
                sock.close()
                
                # Пробуем SMTP handshake
                try:
                    if port == 465:
                        server = smtplib.SMTP_SSL("smtp.yandex.ru", port, timeout=5)
                    else:
                        server = smtplib.SMTP("smtp.yandex.ru", port, timeout=5)
                        if port == 587:
                            server.starttls()
                    
                    response = server.ehlo()
                    print(f"     SMTP handshake: ✅ УСПЕХ ({response[0]})")
                    server.quit()
                except Exception as smtp_e:
                    print(f"     SMTP handshake: ❌ {str(smtp_e)[:50]}")
                    
            else:
                print(f"   Порт {port} ({description}): ❌ ЗАКРЫТ (ошибка {result})")
                
        except socket.timeout:
            print(f"   Порт {port} ({description}): ❌ ТАЙМАУТ (блокировка)")
        except Exception as e:
            print(f"   Порт {port} ({description}): ❌ {str(e)[:50]}")
    
    # 3. Тест HTTP(S) запросов (важно для альтернатив)
    print("\n3. 🌍 Тест HTTP(S) запросов (для API email):")
    try:
        import requests
        test_urls = [
            ("https://httpbin.org/ip", "Публичный HTTP"),
            ("https://api.resend.com", "Resend API"),
            ("https://api.sendgrid.com", "SendGrid API"),
        ]
        
        for url, name in test_urls:
            try:
                response = requests.get(url, timeout=10)
                print(f"   {name}: ✅ Доступен (статус {response.status_code})")
            except Exception as e:
                print(f"   {name}: ❌ Недоступен ({str(e)[:30]})")
                
    except ImportError:
        print("   Библиотека requests не установлена")
    
    print("\n" + "="*60)
    print("📊 РЕЗУЛЬТАТ:")
    print("="*60)
    print("Если все SMTP порты закрыты, но HTTP работает - используйте")
    print("email через API (Resend, SendGrid, Mailgun, etc.)")
    print("="*60)

# Запуск теста при импорте (временно!)
print("🚀 Запускаю тест сетевых возможностей Render...")
test_render_network_capabilities()
