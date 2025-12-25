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

import socket  # Добавьте этот импорт в начало файла

def test_render_smtp_ports():
    """Тестируем, какие SMTP порты доступны на бесплатном Render."""
    print("\n" + "="*60)
    print("🔍 ТЕСТИРУЕМ ДОСТУПНОСТЬ SMTP ПОРТОВ НА RENDER")
    print("="*60)
    
    # Тестируем основные SMTP порты
    ports_to_test = [
        (587, "Yandex/Gmail стандартный (STARTTLS)"),
        (465, "Yandex/Gmail SSL"),
        (25, "SMTP станддартный"),
        (2525, "Альтернативный (часто открыт)"),
        (8025, "Тестовый порт"),
    ]
    
    for port, description in ports_to_test:
        try:
            # Пробуем подключиться к Яндекс SMTP
            print(f"\n📡 Порт {port} ({description}):")
            print(f"   Подключаемся к smtp.yandex.ru:{port}...")
            
            # Создаем сокет с таймаутом 5 секунд
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            result = sock.connect_ex(("smtp.yandex.ru", port))
            
            if result == 0:
                print(f"   ✅ ПОРТ ОТКРЫТ! Можно подключиться")
                
                # Пробуем отправить EHLO команду
                try:
                    if port == 465:
                        server = smtplib.SMTP_SSL("smtp.yandex.ru", port, timeout=5)
                    else:
                        server = smtplib.SMTP("smtp.yandex.ru", port, timeout=5)
                    
                    server.ehlo()
                    print(f"   ✅ SMTP сервер отвечает")
                    server.quit()
                    
                    # Тест с авторизацией (если есть данные)
                    if EMAIL_USER and EMAIL_PASSWORD:
                        try:
                            print(f"   Тестируем авторизацию...")
                            if port == 465:
                                server = smtplib.SMTP_SSL("smtp.yandex.ru", port, timeout=5)
                            else:
                                server = smtplib.SMTP("smtp.yandex.ru", port, timeout=5)
                                if port == 587:
                                    server.starttls()
                            
                            server.login(EMAIL_USER, EMAIL_PASSWORD)
                            print(f"   ✅ АВТОРИЗАЦИЯ УСПЕШНА!")
                            server.quit()
                            return port  # Нашли рабочий порт!
                            
                        except Exception as auth_error:
                            print(f"   ⚠️ Авторизация не удалась: {str(auth_error)[:50]}")
                    
                except Exception as smtp_error:
                    print(f"   ⚠️ SMTP ошибка: {str(smtp_error)[:50]}")
                    
            else:
                print(f"   ❌ ПОРТ ЗАБЛОКИРОВАН Render (код: {result})")
                
            sock.close()
            
        except socket.timeout:
            print(f"   ❌ ТАЙМАУТ - порт заблокирован")
        except Exception as e:
            print(f"   ❌ Ошибка: {str(e)[:50]}")
    
    print("\n" + "="*60)
    print("📊 ВЫВОД: Если все порты заблокированы - нужен обходной путь")
    print("="*60)
    return None

# === ВРЕМЕННЫЙ ТЕСТ ===
# Удалите эти строки после тестирования!
if __name__ == "__main__":
    print("🚀 Запускаем тест SMTP портов...")
    working_port = test_render_smtp_ports()
    if working_port:
        print(f"\n🎉 Найден рабочий порт: {working_port}")
        print(f"Исправьте EMAIL_PORT = {working_port} в настройках")
    else:
        print(f"\n⚠️ Все SMTP порты заблокированы Render")
        print("Нужно использовать HTTP-based email сервис (Resend, SendGrid API)")
