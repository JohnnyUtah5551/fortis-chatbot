import os
import sys
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from chatbot_logic import generate_bot_reply, check_interesting_application
from email_utils import send_application_email, send_incomplete_application_email
from dotenv import load_dotenv
import re
from datetime import datetime, timedelta
import requests
import threading
import asyncio

# Загружаем переменные окружения ДО всего остального
load_dotenv()

def validate_environment():
    """
    Проверяем все обязательные переменные окружения.
    Вызывается при старте приложения.
    """
    print("🔍 Проверка переменных окружения...")
    
    required_vars = {
        "REPLICATE_API_TOKEN": {
            "description": "API ключ для Replicate (Llama 3)",
            "how_to_get": "https://replicate.com/account/api-tokens",
            "example": "r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        },
        "FORMSPREE_URL": {
            "description": "URL формы Formspree для отправки email",
            "example": "https://formspree.io/f/xgozobyn",
            "note": "Получи на formspree.io после создания формы"
        }
    }
    
    optional_vars = {
        "EMAIL_TO": {
            "description": "Email получателя заявок",
            "default": "229@fortis-steel.ru",
            "note": "Основной email менеджеров"
        },
        "RENDER_EXTERNAL_URL": {
            "description": "URL приложения на Render (для keep-alive)",
            "default": "https://fortis-steel-bot.onrender.com"
        },
        "ENVIRONMENT": {
            "description": "Режим работы (development/production)",
            "default": "production"
        }
    }
    
    missing = []
    
    # Проверяем обязательные переменные
    for var_name, var_info in required_vars.items():
        value = os.getenv(var_name)
        
        if not value or value.strip() == "":
            missing.append((var_name, var_info))
            print(f"   ❌ {var_name}: ОТСУТСТВУЕТ")
        else:
            # Маскируем секретные значения в логах
            if "API" in var_name or "TOKEN" in var_name or "KEY" in var_name:
                if len(value) > 12:
                    masked_value = value[:8] + "..." + value[-4:]
                else:
                    masked_value = "***"
                print(f"   ✅ {var_name}: {masked_value}")
            else:
                print(f"   ✅ {var_name}: {value}")
    
    # Проверяем необязательные переменные
    for var_name, var_info in optional_vars.items():
        value = os.getenv(var_name)
        if value:
            if "URL" in var_name:
                print(f"   🌐 {var_name}: {value}")
            else:
                print(f"   ⚙️  {var_name}: {value}")
        else:
            default_value = var_info.get("default", "не задано")
            print(f"   🔧 {var_name}: не задано (по умолчанию: {default_value})")
    
    # Если есть отсутствующие переменные
    if missing:
        error_msg = f"""
{'='*80}
🚨 КРИТИЧЕСКАЯ ОШИБКА: Отсутствуют обязательные переменные окружения
{'='*80}

Отсутствуют следующие переменные:
"""
        for var_name, var_info in missing:
            error_msg += f"\n🔸 {var_name}:"
            error_msg += f"\n   📝 {var_info['description']}"
            if 'example' in var_info:
                error_msg += f"\n   📋 Пример: {var_info['example']}"
            if 'how_to_get' in var_info:
                error_msg += f"\n   🔗 Получить: {var_info['how_to_get']}"
            if 'note' in var_info:
                error_msg += f"\n   💡 Примечание: {var_info['note']}"
        
        error_msg += f"""

{'='*80}
🛠️  КАК ИСПРАВИТЬ:
{'='*80}

1. На Render.com перейдите в Dashboard → Ваше приложение → Environment
2. Нажмите "Add Environment Variable"
3. Добавьте все отсутствующие переменные из списка выше

📋 Пример заполнения:
   - REPLICATE_API_TOKEN: ваш_токен_из_replicate
   - FORMSPREE_URL: https://formspree.io/f/xgozobyn

⚠️  Без этих переменных приложение не сможет работать!
{'='*80}
"""
        
        # В development режиме показываем предупреждение, но продолжаем
        if os.getenv("ENVIRONMENT", "production").lower() == "development":
            print("⚠️  Development режим: продолжаем с ограниченной функциональностью")
            print("⚠️  Предупреждение: Некоторые API могут не работать!")
            return False
        else:
            # В production приложение должно падать
            print(error_msg)
            return False
    
    print("✅ Все обязательные переменные окружения присутствуют")
    return True

# Проверяем переменные окружения ПЕРЕД созданием приложения
print("\n" + "="*60)
print("🚀 Запуск Fortis Chatbot API")
print("="*60)

# Проверяем переменные окружения
env_valid = validate_environment()
if not env_valid and os.getenv("ENVIRONMENT", "production").lower() != "development":
    print("\n❌ Приложение остановлено из-за отсутствия обязательных переменных окружения")
    sys.exit(1)

# Создаем приложение FastAPI
app = FastAPI(
    title="Fortis Chatbot API",
    description="Чат-бот для сайта Fortis Steel с отправкой заявок на email",
    version="1.0.0"
)

# Настраиваем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене замените на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем папку static, чтобы отдавать widget.js
app.mount("/static", StaticFiles(directory="static"), name="static")

# Получаем переменные окружения (теперь они точно есть)
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
FORMSPREE_URL = os.getenv("FORMSPREE_URL", "https://formspree.io/f/xgozobyn")
EMAIL_TO = os.getenv("EMAIL_TO", "229@fortis-steel.ru")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "https://fortis-steel-bot.onrender.com")

# Хранилище сессий пользователей (ключ: IP, значение: данные сессии)
user_sessions = {}

# ====== ФУНКЦИИ ДЛЯ ПОДДЕРЖАНИЯ АКТИВНОСТИ ======

async def keep_alive_ping():
    """Периодически пингуем сам себя, чтобы сервер не засыпал на Render."""
    while True:
        try:
            # Ждем 5 минут (меньше чем 15 минут таймаут Render)
            await asyncio.sleep(300)  # 300 секунд = 5 минут
            
            # Пингуем наш же сервер
            base_url = RENDER_EXTERNAL_URL
            
            # Пробуем разные endpoint'ы
            endpoints_to_ping = ["/health", "/", "/ping"]
            
            for endpoint in endpoints_to_ping:
                try:
                    url = f"{base_url}{endpoint}"
                    response = requests.get(url, timeout=10)
                    print(f"🔔 Keep-alive ping to {endpoint}: {response.status_code}")
                    
                except requests.exceptions.Timeout:
                    print(f"⚠️ Keep-alive ping timeout for {endpoint}")
                except Exception as e:
                    print(f"⚠️ Keep-alive ping failed for {endpoint}: {e}")
                    
        except Exception as e:
            print(f"❌ Keep-alive loop error: {e}")
            await asyncio.sleep(60)  # Ждем минуту при ошибке

def start_keep_alive():
    """Запускаем keep-alive в фоновом потоке."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(keep_alive_ping())
    except Exception as e:
        print(f"❌ Ошибка в keep-alive потоке: {e}")

# Запускаем keep-alive при старте приложения
@app.on_event("startup")
async def startup_event():
    """Запускается при старте приложения."""
    print("\n" + "="*60)
    print("🚀 Запуск Fortis Chatbot API...")
    print("="*60)
    
    print(f"📧 Email сервис: {'✅ Formspree' if FORMSPREE_URL else '❌ Не настроен'}")
    print(f"🤖 AI сервис: {'✅ Replicate' if REPLICATE_API_TOKEN else '❌ Не настроен'}")
    print(f"📨 Отправка писем на: {EMAIL_TO}")
    print(f"🌐 Внешний URL: {RENDER_EXTERNAL_URL}")
    
    # Запускаем keep-alive в фоне только если есть URL
    if RENDER_EXTERNAL_URL and RENDER_EXTERNAL_URL.startswith("http"):
        print("🔔 Starting keep-alive service...")
        threading.Thread(target=start_keep_alive, daemon=True).start()
        print("✅ Keep-alive service started")
    else:
        print("⚠️ Keep-alive service disabled (no valid external URL)")
    
    print("✅ Приложение успешно запущено")
    print("="*60 + "\n")

def cleanup_old_sessions():
    """
    Очистка старых сессий:
    - После 10 минут отправляем неполную заявку (если есть хотя бы один контакт)
    - После 2 часов удаляем сессию полностью
    """
    now = datetime.now()
    to_delete = []
    
    for session_id, session_data in user_sessions.items():
        session_age = now - session_data['created_at']
        
        # Если сессии больше 10 минут И есть хотя бы один контакт И письмо еще не отправлено
        if (session_age > timedelta(minutes=10) and 
            not session_data['email_sent'] and 
            (session_data['phone'] or session_data['email'])):
            
            print(f"⏰ ТАЙМАУТ 10 минут: отправляем неполную заявку для сессии {session_id}")
            
            # Отправляем неполную заявку
            full_text = "\n".join(session_data['text_parts'])
            send_incomplete_application_email(
                full_text, 
                session_data['amount'], 
                session_data['phone'], 
                session_data['email']
            )
            session_data['email_sent'] = True
            session_data['incomplete_sent'] = True
            session_data['timeout_reason'] = "10 минут без второго контакта"
        
        # Удаляем очень старые сессии (больше 2 часов)
        if session_age > timedelta(hours=2):
            to_delete.append(session_id)
            print(f"🧹 Удаляем старую сессию {session_id} (больше 2 часов)")
    
    for session_id in to_delete:
        del user_sessions[session_id]

@app.post("/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    user_message = data.get("message", "")
    user_ip = request.client.host  # Используем IP как идентификатор сессии
    
    print(f"\n=== /chat endpoint вызван ===")
    print(f"👤 Пользователь IP: {user_ip}")
    print(f"💬 Сообщение: '{user_message}'")

    # Очищаем старые сессии перед обработкой нового сообщения
    cleanup_old_sessions()

    # 1. Проверяем, является ли это интересной заявкой (>50,000 руб)
    is_interesting, amount = check_interesting_application(user_message)
    print(f"🔍 Результат проверки заявки: интересная={is_interesting}, сумма={amount}")

    # 2. Если это большая заявка (>50,000 руб)
    if is_interesting:
        print(f"🚨 БОЛЬШАЯ ЗАЯВКА! Сумма: {amount} руб.")
        
        # Создаем новую сессию или получаем существующую
        if user_ip not in user_sessions:
            user_sessions[user_ip] = {
                'created_at': datetime.now(),
                'amount': amount,
                'phone': None,           # Найденный телефон
                'email': None,           # Найденный email
                'text_parts': [],        # Все сообщения пользователя в этой сессии
                'email_sent': False,     # Отправлено ли письмо
                'incomplete_sent': False,# Отправлено ли неполное письмо (таймаут)
                'reminder_sent': False,  # Отправлено ли напоминание о втором контакте
                'message_count': 0       # Количество сообщений в сессии
            }
            print(f"🆕 Создана новая сессия для {user_ip}")
        
        session = user_sessions[user_ip]
        session['text_parts'].append(user_message)
        session['message_count'] += 1
        full_text = "\n".join(session['text_parts'])
        
        # Ищем контакты в текущем сообщении
        
        # Телефон: ищем по паттерну (+7, 8, и т.д.)
        phone_pattern = r'[\+7]?[-\s]?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}'
        phone_matches = re.findall(phone_pattern, user_message)
        
        # Email: ищем стандартный email паттерн
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        email_matches = re.findall(email_pattern, user_message)
        
        # Обновляем найденные контакты
        if phone_matches and not session['phone']:
            session['phone'] = phone_matches[0]
            print(f"📞 Найден телефон в сообщении: {session['phone']}")
        
        if email_matches and not session['email']:
            session['email'] = email_matches[0]
            print(f"📧 Найден email в сообщении: {session['email']}")
        
        # Дополнительная проверка по ключевым словам (если не нашли паттерном)
        if not session['phone'] and any(word in user_message.lower() for word in ['тел', 'телефон', '+7', '8-9', '89', 'моб', 'сотов']):
            session['phone'] = "Указан в тексте (не распознан автоматически)"
            print(f"📞 Телефон указан в тексте")
        
        if not session['email'] and '@' in user_message:
            session['email'] = "Указан в тексте (не распознан автоматически)"
            print(f"📧 Email указан в тексте")
        
        # Логируем текущее состояние сессии
        print(f"📊 СОСТОЯНИЕ СЕССИИ {user_ip}:")
        print(f"   📝 Сообщений: {session['message_count']}")
        print(f"   📞 Телефон: {'✅ ' + str(session['phone']) if session['phone'] else '❌ Нет'}")
        print(f"   📧 Email: {'✅ ' + str(session['email']) if session['email'] else '❌ Нет'}")
        print(f"   📨 Полное письмо отправлено: {'✅' if session['email_sent'] and not session.get('incomplete_sent') else '❌'}")
        print(f"   ⚠️ Неполное письмо отправлено: {'✅' if session.get('incomplete_sent') else '❌'}")
        print(f"   💡 Напоминание отправлено: {'✅' if session['reminder_sent'] else '❌'}")
        
        # ===== ЛОГИКА ОТВЕТА БОТА =====
        
        # Случай 1: Письмо уже отправлено (полное или неполное)
        if session['email_sent']:
            if session.get('incomplete_sent'):
                bot_reply = "Заявка передана менеджеру. Мы свяжемся с вами по имеющимся контактам. Спасибо!"
            else:
                bot_reply = "Спасибо! Полная заявка передана менеджеру. С вами свяжутся в течение 30 минут."
        
        # Случай 2: Есть ОБА контакта - отправляем ПОЛНУЮ заявку
        elif session['phone'] and session['email']:
            print(f"📨 ОТПРАВЛЯЕМ ПОЛНУЮ ЗАЯВКУ (есть и телефон, и email)")
            success = send_application_email(full_text, amount, session['phone'], session['email'])
            if success:
                session['email_sent'] = True
                bot_reply = "Спасибо! Полная заявка передана менеджеру. С вами свяжутся в течение 30 минут."
            else:
                bot_reply = "Произошла ошибка при отправке заявки. Пожалуйста, попробуйте еще раз или свяжитесь с нами напрямую."
        
        # Случай 3: Есть только ОДИН контакт
        elif session['phone'] or session['email']:
            has_phone = bool(session['phone'])
            has_email = bool(session['email'])
            
            # Если это уже не первое сообщение с контактом, отправляем напоминание
            if not session['reminder_sent'] and session['message_count'] >= 2:
                if has_phone and not has_email:
                    bot_reply = f"Спасибо за телефон! Для быстрого оформления заказа на {amount} руб. укажите также email. Это ускорит обработку заявки."
                elif has_email and not has_phone:
                    bot_reply = f"Спасибо за email! Для быстрого оформления заказа на {amount} руб. укажите также телефон для связи. Это ускорит обработку заявки."
                session['reminder_sent'] = True
                print(f"💡 Отправлено напоминание о втором контакте")
            
            else:
                # Просим недостающий контакт
                if has_phone and not has_email:
                    bot_reply = f"Спасибо! Для оформления заказа на {amount} руб. мне также нужен ваш email. Напишите его, пожалуйста."
                elif has_email and not has_phone:
                    bot_reply = f"Спасибо! Для оформления заказа на {amount} руб. мне также нужен ваш телефон для связи. Напишите его, пожалуйста."
                else:
                    bot_reply = f"Это уже серьёзный заказ ({amount} руб.) — назовите, пожалуйста, телефон и email для связи?"
        
        # Случай 4: Нет контактов вообще
        else:
            bot_reply = f"Это уже серьёзный заказ ({amount} руб.) — давайте я передам его менеджеру для лучших условий. Назовите, пожалуйста, телефон и email для связи?"
    
    # 3. Если это обычный запрос (не заявка >50,000 руб)
    else:
        print(f"✓ Обычный запрос, сумма меньше 50,000 руб или не указана")
        if REPLICATE_API_TOKEN:
            bot_reply = generate_bot_reply(REPLICATE_API_TOKEN, user_message)
        else:
            bot_reply = "Извините, в данный момент AI-сервис недоступен. Пожалуйста, свяжитесь с нами по телефону."
            print("⚠️ REPLICATE_API_TOKEN отсутствует, AI-ответы недоступны")

    print(f"🤖 Ответ бота: '{bot_reply[:100]}...'" if len(bot_reply) > 100 else f"🤖 Ответ бота: '{bot_reply}'")
    print("="*40)
    
    return {"reply": bot_reply}


@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check(request: Request):
    """Эндпоинт для проверки здоровья, поддерживает GET и HEAD."""
    if request.method == "HEAD":
        return Response(status_code=200)
    
    # Проверяем доступность внешних сервисов
    services_status = {
        "replicate_api": bool(REPLICATE_API_TOKEN),
        "formspree_api": bool(FORMSPREE_URL),
        "email_to": bool(EMAIL_TO)
    }
    
    # Общий статус
    all_services_ok = all(services_status.values())
    
    return {
        "status": "ok" if all_services_ok else "degraded",
        "service": "fortis-chatbot-api",
        "timestamp": datetime.now().isoformat(),
        "sessions_count": len(user_sessions),
        "services": services_status,
        "environment": os.getenv("ENVIRONMENT", "production"),
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Корневой endpoint с информацией о сервисе."""
    return {
        "service": "Fortis Chatbot API",
        "description": "Чат-бот для сайта Fortis Steel с отправкой заявок на email",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "chat": {
                "url": "/chat",
                "method": "POST",
                "description": "Основной endpoint для общения с ботом"
            },
            "health": {
                "url": "/health",
                "method": "GET, HEAD",
                "description": "Проверка работоспособности сервиса"
            },
            "ping": {
                "url": "/ping",
                "method": "GET",
                "description": "Простой пинг для keep-alive"
            },
            "debug_sessions": {
                "url": "/debug/sessions",
                "method": "GET",
                "description": "Просмотр активных сессий (только для разработки)"
            }
        },
        "features": {
            "ai_provider": "Replicate (Llama 3 70B)" if REPLICATE_API_TOKEN else "Не настроен",
            "email_provider": "Formspree" if FORMSPREE_URL else "Не настроен",
            "session_timeout": "10 minutes for incomplete applications",
            "min_order_amount": "50,000 RUB",
            "target_email": EMAIL_TO
        },
        "environment": os.getenv("ENVIRONMENT", "production")
    }


@app.get("/ping")
async def ping():
    """Простой endpoint для пинга сервера (используется для keep-alive)."""
    return {
        "status": "pong",
        "timestamp": datetime.now().isoformat(),
        "service": "fortis-chatbot",
        "message": "Server is alive and responding"
    }


@app.get("/debug/sessions")
async def debug_sessions():
    """Отладочный эндпоинт для просмотра активных сессий (только для разработки)."""
    # Проверяем режим - только для разработки
    if os.getenv("ENVIRONMENT", "production").lower() == "production":
        return {"error": "Доступ запрещен в production режиме"}
    
    now = datetime.now()
    active_sessions = {}
    
    for session_id, session_data in user_sessions.items():
        session_age = now - session_data['created_at']
        active_sessions[session_id] = {
            "age_seconds": session_age.total_seconds(),
            "age_minutes": round(session_age.total_seconds() / 60, 1),
            "amount": session_data['amount'],
            "phone": session_data['phone'],
            "email": session_data['email'],
            "message_count": session_data['message_count'],
            "email_sent": session_data['email_sent'],
            "incomplete_sent": session_data.get('incomplete_sent', False),
            "timeout_reason": session_data.get('timeout_reason'),
            "text_parts": session_data['text_parts'][-3:]  # Последние 3 сообщения
        }
    
    return {
        "active_sessions_count": len(user_sessions),
        "current_time": now.isoformat(),
        "environment": os.getenv("ENVIRONMENT", "production"),
        "sessions": active_sessions
    }


@app.get("/test/email")
async def test_email():
    """Тестовый endpoint для проверки отправки email (только для разработки)."""
    # Проверяем режим - только для разработки
    if os.getenv("ENVIRONMENT", "production").lower() == "production":
        return {"error": "Доступ запрещен в production режиме"}
    
    # Проверяем наличие API ключей
    if not FORMSPREE_URL:
        return {
            "status": "error",
            "error": "FORMSPREE_URL не настроен"
        }
    
    test_amount = 75000
    test_phone = "+79161234567"
    test_email = "test@example.com"
    test_text = "Это тестовое сообщение для проверки отправки email через Formspree."
    
    try:
        # Тест полной заявки
        success_full = send_application_email(test_text, test_amount, test_phone, test_email)
        
        # Тест неполной заявки
        success_incomplete = send_incomplete_application_email(test_text, test_amount, test_phone, None)
        
        return {
            "status": "test_completed",
            "full_email_sent": success_full,
            "incomplete_email_sent": success_incomplete,
            "test_data": {
                "amount": test_amount,
                "phone": test_phone,
                "email": test_email
            },
            "email_to": EMAIL_TO,
            "formspree_url": FORMSPREE_URL
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "formspree_url_set": bool(FORMSPREE_URL)
        }


# Обработчик ошибок 404
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return Response(
        status_code=404,
        content=f"Endpoint {request.url.path} not found. Available endpoints: /chat (POST), /health (GET), / (GET)"
    )


# Глобальный обработчик ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"❌ Необработанная ошибка: {exc}")
    return Response(
        status_code=500,
        content=f"Internal Server Error: {str(exc)}"
    )

