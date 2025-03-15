from fastapi import FastAPI, HTTPException, Header, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from datetime import datetime, timedelta
import asyncio
from aiogram.utils import executor
import json
import base64
from fastapi.responses import JSONResponse, RedirectResponse
import secrets
import time
import hmac
import hashlib
from urllib.parse import parse_qs
from functools import lru_cache

logging.basicConfig(level=logging.ERROR)

DATABASE_URL = "database.db"

def get_db():
    try:
        conn = sqlite3.connect(DATABASE_URL)
        return conn
    except sqlite3.Error as e:
        logging.error(f"Ошибка при подключении к базе данных: {e}")
        raise

def init_db():
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                rank TEXT,
                points INTEGER
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                admin_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                proofs TEXT NOT NULL,
                images TEXT,
                ban_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES admins (user_id)
            )
        """)
        cursor.execute("CREATE TABLE IF NOT EXISTS mutes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, admin_id INTEGER NOT NULL, reason TEXT NOT NULL, proofs TEXT NOT NULL, duration TEXT NOT NULL, mute_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (admin_id) REFERENCES admins (user_id))")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                target_id INTEGER,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES admins (user_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_ips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL UNIQUE,
                ip_address TEXT NOT NULL,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES admins (user_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                admin_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                proofs TEXT NOT NULL,
                count INTEGER NOT NULL,
                warning_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES admins (user_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id BIGINT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                username TEXT,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()

app = FastAPI(title="Backend API")

origins = [
    "https://thunderous-mermaid-3a3523.netlify.app",
    "http://thunderous-mermaid-3a3523.netlify.app",
    "https://t.me",
    "http://localhost:5173",
    "http://localhost:3000",
    "https://usfbase.ru",
    "http://usfbase.ru",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)
BOT_TOKEN = '7892645481:AAESpSKDbi8yOOeuxSUOe1WkELhiZaWvieI'
WEBAPP_URL = "https://thunderous-mermaid-3a3523.netlify.app"
bot = Bot(token=BOT_TOKEN, parse_mode='HTML')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

init_db()

active_tokens = {}


def create_admin_token(user_id: int) -> str:
    if not is_admin(user_id):
        return None
    token = secrets.token_urlsafe(32)
    active_tokens[token] = {'user_id': user_id, 'expires': time.time() + 86400}
    return token

def verify_admin_token(token: str) -> int:
    if token not in active_tokens:
        raise HTTPException(status_code=401, detail="Неверный токен")
    token_data = active_tokens[token]
    if time.time() > token_data['expires']:
        del active_tokens[token]
        raise HTTPException(status_code=401, detail="Токен истёк")
    return token_data['user_id']

def is_admin(user_id: int) -> bool:
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM admins WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return bool(result)
    finally:
        conn.close()

def is_banned(user_id: int) -> bool:
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM bans WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return bool(result)
    finally:
        conn.close()

def is_muted(user_id: int) -> bool:
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM mutes WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return bool(result)
    finally:
        conn.close()

def add_admin(user_id: int) -> bool:
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO admins (user_id) VALUES (?)", (user_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        logging.error(f"Ошибка при добавлении админа: {e}")
        return False
    finally:
        conn.close()

def add_ban(user_id: int, admin_id: int, reason: str, proofs: str, images: List[str] = None) -> bool:
    conn = get_db()
    try:
        cursor = conn.cursor()
        images_json = json.dumps(images) if images else None
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO bans (user_id, admin_id, reason, proofs, images, ban_date) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, admin_id, reason, proofs, images_json, current_time))
        conn.commit()
        return True
    except sqlite3.Error as e:
        logging.error(f"Ошибка при добавлении бана: {e}")
        return False
    finally:
        conn.close()

def add_mute(user_id: int, admin_id: int, reason: str, proofs: str, duration: str) -> bool:
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO mutes (user_id, admin_id, reason, proofs, duration) VALUES (?, ?, ?, ?, ?)",
            (user_id, admin_id, reason, proofs, duration))
        conn.commit()
        return True
    except sqlite3.Error as e:
        logging.error(f"Ошибка при добавлении мута: {e}")
        return False
    finally:
        conn.close()

def remove_ban(user_id: int) -> bool:
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bans WHERE user_id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logging.error(f"Ошибка при удалении бана: {e}")
        return False
    finally:
        conn.close()

def get_group_ids() -> List[int]:
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT group_id FROM groups")
        return [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()

def parse_duration(duration_str: str) -> int:
    try:
        multipliers = {'с': 1, 'м': 60, 'ч': 3600, 'д': 86400, 'н': 604800, 'мес': 2592000, 'г': 31536000}
        amount = ''
        unit = ''
        for char in duration_str:
            if char.isdigit():
                amount += char
            else:
                unit += char.lower()
        if not amount or not unit:
            raise ValueError("Неверный формат длительности")
        if unit == 'м' and int(amount) > 60:
            multiplier = multipliers['мес']
        else:
            multiplier = multipliers.get(unit)
        if not multiplier:
            raise ValueError("Неверная единица измерения")
        return int(amount) * multiplier
    except Exception as e:
        logging.error(f"Ошибка при парсинге длительности: {e}")
        raise ValueError("Неверный формат длительности")

def validate_telegram_webapp_data(init_data: str) -> dict:
    try:
        if not init_data:
            raise HTTPException(status_code=401, detail="Init data not provided")
            
        try:
            json_data = json.loads(init_data)
            if isinstance(json_data, dict) and 'id' in json_data:
                return json_data
        except json.JSONDecodeError:
            pass

        parsed_data = dict(parse_qs(init_data))
        parsed_data = {k: v[0] if isinstance(v, list) else v for k, v in parsed_data.items()}
        received_hash = parsed_data.pop('hash', None)
        
        if not received_hash:
            raise HTTPException(status_code=401, detail="Hash not found")
            
        sorted_items = sorted(parsed_data.items(), key=lambda x: x[0])
        data_check_string = "\n".join([f"{k}={v}" for k, v in sorted_items])
        
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        if calculated_hash != received_hash:
            raise HTTPException(status_code=401, detail="Invalid hash")
            
        user_data = json.loads(parsed_data.get('user', '{}'))
        
        if not user_data.get('id'):
            raise HTTPException(status_code=400, detail="User ID not found")
            
        return user_data
    except Exception as e:
        logging.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

def verify_webapp_and_admin(authorization: str) -> int:
    """
    Проверяет валидность данных веб-приложения и статус админа.
    Возвращает ID админа если все проверки пройдены.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Отсутствует авторизация")
    
    try:
        user_data = validate_telegram_webapp_data(authorization)
        user_id = int(user_data.get('id'))
        
        if not user_id:
            raise HTTPException(status_code=401, detail="ID пользователя не найден")
            
        if not is_admin(user_id):
            raise HTTPException(status_code=403, detail="Пользователь не является администратором")
            
        return user_id
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Ошибка авторизации: {str(e)}")

@app.get("/")
async def root():
    return {"message": "API работает"}

@app.get("/check_admin/{user_id}")
async def check_admin(user_id: int, authorization: str = Header(None)):
    try:
        admin_id = verify_webapp_and_admin(authorization)
        is_user_admin = is_admin(user_id)
        return {"is_admin": is_user_admin, "message": "Доступ разрешен" if is_user_admin else "Доступ запрещен"}
    except Exception as e:
        logging.error(f"Ошибка при проверке админа: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/generate_token/{user_id}")
async def get_admin_token(user_id: int, authorization: str = Header(None)):
    try:
        admin_id = verify_webapp_and_admin(authorization)
        token = create_admin_token(user_id)
        if not token:
            raise HTTPException(status_code=403, detail="Пользователь не является администратором")
        return {"token": token}
    except Exception as e:
        logging.error(f"Ошибка при генерации токена: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/login/{user_id}")
async def login(user_id: int, authorization: str = Header(None)):
    try:
        admin_id = verify_webapp_and_admin(authorization)
        token = create_admin_token(user_id)
        if not token:
            raise HTTPException(status_code=403, detail="Пользователь не является администратором")
        return {"token": token}
    except Exception as e:
        logging.error(f"Ошибка при входе: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/USFAPI/ban")
async def banuser_with_images(
    request: Request,
    user_id: str = Form(...), 
    reason: str = Form(...), 
    proofs: str = Form(...),
    images: List[UploadFile] = File(None), 
    authorization: str = Header(None)
):
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Отсутствует авторизация")
            
        user_data = validate_telegram_webapp_data(authorization)
        admin_id = int(user_data.get('id'))
        
        if not admin_id:
            raise HTTPException(status_code=401, detail="ID администратора не найден")
        
        if not is_admin(admin_id):
            raise HTTPException(status_code=403, detail="Пользователь не является администратором")

        try:
            user_id = int(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Неверный формат ID пользователя")

        if is_banned(user_id):
            raise HTTPException(status_code=400, detail="Пользователь уже забанен")

        image_data_list = []
        if images:
            for image in images:
                contents = await image.read()
                base64_image = base64.b64encode(contents).decode()
                image_data_list.append(base64_image)

        if not add_ban(user_id, admin_id, reason, proofs, image_data_list):
            raise HTTPException(status_code=500, detail="Ошибка при добавлении бана")

        groups = get_group_ids()
        success_groups = []
        failed_groups = []
        
        for group_id in groups:
            try:
                await bot.ban_chat_member(
                    chat_id=group_id, 
                    user_id=user_id, 
                    revoke_messages=True
                )
                success_groups.append(group_id)
                
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton(
                    text="Информация о бане",
                    url=f"https://t.me/groupp_managerbot?startApp=user/{user_id}"
                ))
                
                await bot.send_message(
                    group_id,
                    f"🚫 <b>Пользователь заблокирован</b>\n\n👤 ID: <code>{user_id}</code>\n📝 Причина: {reason}",
                    reply_markup=keyboard
                )
            except Exception as e:
                logging.error(f"Ban error in group {group_id}: {str(e)}")
                failed_groups.append({"group_id": group_id, "error": str(e)})

        await log_admin_action(
            admin_id=admin_id,
            action_type="ban",
            target_id=user_id,
            details=f"Причина: {reason}"
        )
        await log_admin_ip(admin_id, request)

        return {
            "status": "success",
            "message": "Пользователь успешно заблокирован",
            "success_groups": success_groups,
            "failed_groups": failed_groups,
            "total_groups": len(groups),
            "success_count": len(success_groups),
            "failed_count": len(failed_groups)
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Ban error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Неожиданная ошибка: {str(e)}")

@app.get("/USFAPI/bans")
async def get_bans(authorization: str = Header(None), search_id: Optional[str] = None):
    try:
        admin_id = verify_webapp_and_admin(authorization)
        logging.info(f"Запрос списка банов от админа {admin_id}")

        conn = get_db()
        try:
            cursor = conn.cursor()
            sql = """
                SELECT 
                    bans.id, 
                    bans.user_id, 
                    bans.admin_id, 
                    bans.reason, 
                    bans.proofs, 
                    bans.images, 
                    bans.ban_date 
                FROM bans
            """
            params = []
            
            if search_id:
                sql += " WHERE bans.user_id LIKE ?"
                params.append(f"%{search_id}%")
                
            sql += " ORDER BY bans.ban_date DESC"
            
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
                
            bans = cursor.fetchall()
            
            formatted_bans = []
            for ban in bans:
                try:
                    images = json.loads(ban[5]) if ban[5] else []
                except json.JSONDecodeError:
                    images = []
                    logging.error(f"Ошибка при парсинге изображений для бана {ban[0]}")
                
                formatted_bans.append({
                    "id": ban[0],
                    "user_id": ban[1],
                    "admin_id": ban[2],
                    "reason": ban[3],
                    "proofs": ban[4],
                    "images": images,
                    "ban_date": ban[6]
                })
            
            return formatted_bans
        finally:
            conn.close()
    except Exception as e:
        logging.error(f"Ошибка при получении списка банов: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    
    if is_admin(message.from_user.id):
        keyboard.add(types.InlineKeyboardButton(
            text="Открыть админ панель",
            web_app=types.WebAppInfo(url=f"{WEBAPP_URL}/admin")
        ))
        await message.reply("<b>С помощью кнопки ниже вы можете открыть админ панель:</b>", 
            reply_markup=keyboard)
    else:
        keyboard.add(types.InlineKeyboardButton(
            text="Открыть меню USF",
            web_app=types.WebAppInfo(url=f"{WEBAPP_URL}/defaultuser")
        ))
        await message.reply("<b>С помощью кнопки ниже вы можете открыть меню ???:</b>", 
            reply_markup=keyboard)

@dp.message_handler(commands=['admin'])
async def send_admin_panel(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.reply("<b>⛔️ У вас нет доступа к админ панели.</b>")
        return
    keyboard = types.InlineKeyboardMarkup()
    webapp_button = types.InlineKeyboardButton(text="Открыть админ панель",
        web_app=types.WebAppInfo(url=WEBAPP_URL))
    keyboard.add(webapp_button)
    await message.reply("<b>Нажмите кнопку ниже, чтобы открыть админ панель:</b>\nВаш ID: <code>{}</code>".format(
        message.from_user.id), reply_markup=keyboard)

@app.get("/add_admin/{user_id}")
async def add_new_admin(user_id: int, authorization: str = Header(None)):
    try:
        admin_id = verify_webapp_and_admin(authorization)
        
        # Проверяем ранг текущего админа
        conn = get_db()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT points FROM admins WHERE user_id = ?", (admin_id,))
            admin_data = cursor.fetchone()
            if not admin_data or admin_data[0] < 90:
                raise HTTPException(status_code=403, detail="Недостаточно прав для добавления админов")
        finally:
            conn.close()

        if add_admin(user_id):
            logging.info(f"Админ {admin_id} добавил нового админа {user_id}")
            await log_admin_action(
                admin_id=admin_id,
                action_type="admin_add",
                target_id=user_id,
                details=f"Очки: {admin_data[0]}"
            )
            return {"message": f"Админ {user_id} успешно добавлен"}
        else:
            raise HTTPException(status_code=500, detail="Ошибка при добавлении админа")
    except Exception as e:
        logging.error(f"Ошибка при добавлении админа: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/debug/validate_webapp")
async def debug_validate_webapp(request: Request, authorization: str = Header(None)):
    try:
        admin_id = verify_webapp_and_admin(authorization)
        body = await request.body()
        init_data = body.decode()
        result = validate_telegram_webapp_data(init_data)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/debug/check_data")
async def debug_check_data(request: Request, authorization: str = Header(None)):
    try:
        admin_id = verify_webapp_and_admin(authorization)
        headers = dict(request.headers)
        params = dict(request.query_params)
        return {
            "headers": headers,
            "params": params,
            "message": "Данные успешно получены"
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/USFAPI/admins")
async def get_admins(authorization: str = Header(None)):
    try:
        admin_id = verify_webapp_and_admin(authorization)
        
        conn = get_db()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, points FROM admins")
            admins = cursor.fetchall()
            admin_list = []
            
            for admin in admins:
                admin_id, points = admin
                try:
                    user_info = await bot.get_chat(admin_id)
                    photos = await bot.get_user_profile_photos(admin_id, limit=1)
                    
                    admin_data = {
                        "user_id": admin_id,
                        "username": user_info.username or str(admin_id),
                        "full_name": user_info.full_name or str(admin_id),
                        "points": points,
                        "avatar": None
                    }
                    
                    if photos and photos.total_count > 0:
                        file_info = await bot.get_file(photos.photos[0][-1].file_id)
                        admin_data["avatar"] = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
                    
                    admin_list.append(admin_data)
                except Exception as e:
                    logging.error(f"Ошибка при получении информации об админе {admin_id}: {e}")
                    admin_list.append({
                        "user_id": admin_id,
                        "username": str(admin_id),
                        "full_name": str(admin_id),
                        "points": points,
                        "avatar": None
                    })
            
            # Отключаем все кэширование
            return JSONResponse(
                content=admin_list,
                headers={
                    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0, private",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
        finally:
            conn.close()
    except Exception as e:
        logging.error(f"Ошибка в get_admins: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Кэш для аватарок на 5 минут
@lru_cache(maxsize=100)
def get_cached_avatar(user_id: int, timestamp: int):
    """
    Получает аватарку пользователя с кэшированием
    timestamp обновляется каждые 5 минут для обновления кэша
    """
    try:
        photos = bot.get_user_profile_photos(user_id, limit=1)
        if photos and photos.total_count > 0:
            file_info = bot.get_file(photos.photos[0][-1].file_id)
            return f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        return None
    except:
        return None

@app.get("/USFAPI/admin/{admin_id}")
async def get_admin_info(admin_id: int, authorization: str = Header(None)):
    try:
        verify_webapp_and_admin(authorization)
        if not is_admin(admin_id):
            raise HTTPException(status_code=404, detail="Администратор не найден")

        try:
            user_info = await bot.get_chat(admin_id)
            # Обновляем timestamp каждые 5 минут
            current_timestamp = int(time.time() / 300)
            avatar_url = get_cached_avatar(admin_id, current_timestamp)
            
            admin_data = {
                "user_id": admin_id,
                "username": user_info.username or str(admin_id),
                "full_name": user_info.full_name or str(admin_id),
                "avatar": avatar_url
            }
            
            return admin_data
        except Exception as e:
            logging.error(f"Ошибка при получении информации об админе {admin_id}: {e}")
            return {
                "user_id": admin_id,
                "username": str(admin_id),
                "full_name": str(admin_id),
                "avatar": None
            }
    except Exception as e:
        logging.error(f"Ошибка в get_admin_info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/USFAPI/admin/avatar/{file_id}")
async def get_admin_avatar(file_id: str, authorization: str = Header(None)):
    try:
        verify_webapp_and_admin(authorization)
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        return RedirectResponse(url=file_url)
    except Exception as e:
        logging.error(f"Ошибка при получении аватара: {e}")
        raise HTTPException(status_code=404, detail="Аватар не найден")

@app.get("/USFAPI/current-admin")
async def get_current_admin(authorization: str = Header(None)):
    try:
        admin_id = verify_webapp_and_admin(authorization)
        
        conn = get_db()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT points FROM admins WHERE user_id = ?", (admin_id,))
            result = cursor.fetchone()
            
            if result:
                return {"points": result[0]}
            return {"points": 0}
        finally:
            conn.close()
    except Exception as e:
        logging.error(f"Ошибка при получении текущего админа: {e}")
        return {"points": 0}

@app.post("/USFAPI/admin/add")
async def add_new_admin(
    request: Request,
    user_id: int = Form(...),
    points: int = Form(...),
    authorization: str = Header(None)
):
    try:
        current_admin_id = verify_webapp_and_admin(authorization)
        await log_admin_ip(current_admin_id, request)
        
        conn = get_db()
        try:
            cursor = conn.cursor()
            # Проверяем ранг текущего админа
            cursor.execute("SELECT points FROM admins WHERE user_id = ?", (current_admin_id,))
            admin_data = cursor.fetchone()
            if not admin_data or admin_data[0] < 90:
                raise HTTPException(status_code=403, detail="Недостаточно прав для добавления админов")

            # Проверяем, существует ли пользователь в Telegram
            try:
                user_info = await bot.get_chat(user_id)
            except:
                raise HTTPException(status_code=404, detail="Пользователь не найден в Telegram")

            # Проверяем, не существует ли уже такой админ
            cursor.execute("SELECT id FROM admins WHERE user_id = ?", (user_id,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Администратор уже существует")

            # Проверяем валидность очков
            if points < 1 or points > 100:
                raise HTTPException(status_code=400, detail="Очки должны быть от 1 до 100")

            # Добавляем нового админа
            cursor.execute(
                "INSERT INTO admins (user_id, points) VALUES (?, ?)",
                (user_id, points)
            )
            conn.commit()
            
            # Логируем действие
            await log_admin_action(
                admin_id=current_admin_id,
                action_type="admin_add",
                target_id=user_id,
                details=f"Очки: {points}"
            )
            
            return {"message": "Администратор успешно добавлен"}
        finally:
            conn.close()
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Ошибка при добавлении админа: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/USFAPI/admin/{admin_id}")
async def remove_admin_endpoint(
    request: Request,
    admin_id: int,
    authorization: str = Header(None)
):
    try:
        current_admin_id = verify_webapp_and_admin(authorization)
        await log_admin_ip(current_admin_id, request)
        
        conn = get_db()
        try:
            cursor = conn.cursor()
            
            # Проверяем ранг текущего админа
            cursor.execute("SELECT points FROM admins WHERE user_id = ?", (current_admin_id,))
            admin_data = cursor.fetchone()
            if not admin_data or admin_data[0] < 90:
                raise HTTPException(status_code=403, detail="Недостаточно прав")

            # Нельзя удалить самого себя
            if current_admin_id == admin_id:
                raise HTTPException(status_code=400, detail="Нельзя удалить самого себя")

            # Удаляем админа
            cursor.execute("DELETE FROM admins WHERE user_id = ?", (admin_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Администратор не найден")
            
            conn.commit()
            await log_admin_action(
                admin_id=current_admin_id,
                action_type="admin_remove",
                target_id=admin_id,
                details=f"Администратор удален"
            )
            return {"message": "Администратор успешно удален"}
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Ошибка при удалении админа: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/USFAPI/admin/update")
async def update_admin_rank(
    request: Request,
    admin_id: int = Form(...),
    points: int = Form(...),
    authorization: str = Header(None)
):
    try:
        current_admin_id = verify_webapp_and_admin(authorization)
        await log_admin_ip(current_admin_id, request)
        
        conn = get_db()
        try:
            cursor = conn.cursor()
            
            # Проверяем ранг текущего админа
            cursor.execute("SELECT points FROM admins WHERE user_id = ?", (current_admin_id,))
            admin_data = cursor.fetchone()
            if not admin_data or admin_data[0] < 90:
                raise HTTPException(status_code=403, detail="Недостаточно прав")

            # Проверяем валидность очков
            if points < 1 or points > 100:
                raise HTTPException(status_code=400, detail="Очки должны быть от 1 до 100")

            # Получаем информацию о целевом админе
            cursor.execute("SELECT points FROM admins WHERE user_id = ?", (admin_id,))
            target_admin_data = cursor.fetchone()
            if not target_admin_data:
                raise HTTPException(status_code=404, detail="Администратор не найден")

            # Обновляем данные админа
            cursor.execute(
                "UPDATE admins SET points = ? WHERE user_id = ?",
                (points, admin_id)
            )
            
            conn.commit()

            # Получаем юзернеймы админов для лога
            try:
                current_admin_info = await bot.get_chat(current_admin_id)
                target_admin_info = await bot.get_chat(admin_id)
                current_admin_username = current_admin_info.username or str(current_admin_id)
                target_admin_username = target_admin_info.username or str(admin_id)
            except:
                current_admin_username = str(current_admin_id)
                target_admin_username = str(admin_id)

            # Логируем действие
            await log_admin_action(
                admin_id=current_admin_id,
                action_type="admin_update",
                target_id=admin_id,
                details=f"@{current_admin_username} → @{target_admin_username} (Очки: {points})"
            )
            
            return {"message": "Данные администратора успешно обновлены"}
        finally:
            conn.close()
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Ошибка при обновлении данных админа: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/USFAPI/check_admin/{user_id}")
async def check_admin_endpoint(user_id: int, authorization: str = Header(None)):
    try:
        if authorization:
            validate_telegram_webapp_data(authorization)
            
        conn = get_db()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT rank, points FROM admins WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            
            return {
                "is_admin": bool(result),
                "rank": result[0] if result else None,
                "points": result[1] if result else 0
            }
        finally:
            conn.close()
    except Exception as e:
        logging.error(f"Ошибка при проверке админа: {e}")
        return {"is_admin": False, "rank": None, "points": 0}

@app.get("/USFAPI/check_ban/{user_id}")
async def check_ban(user_id: int):
    try:
        conn = get_db()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM bans WHERE user_id = ?", (user_id,))
            is_banned = bool(cursor.fetchone())
            return {"is_banned": is_banned}
        finally:
            conn.close()
    except Exception as e:
        logging.error(f"Ошибка при проверке бана: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/USFAPI/user/{user_id}")
async def get_user_info(user_id: int):
    try:
        # Проверяем бан
        conn = get_db()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM bans WHERE user_id = ?", (user_id,))
            is_banned = bool(cursor.fetchone())
        finally:
            conn.close()

        # Получаем информацию о пользователе через бота
        try:
            user_info = await bot.get_chat(user_id)
            photos = await bot.get_user_profile_photos(user_id, limit=1)
            
            user_data = {
                "user_id": user_id,
                "username": user_info.username,
                "first_name": user_info.first_name,
                "last_name": user_info.last_name,
                "is_banned": is_banned,
                "avatar": None
            }
            
            if photos and photos.total_count > 0:
                file_info = await bot.get_file(photos.photos[0][-1].file_id)
                user_data["avatar"] = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
            
            return user_data
        except Exception as e:
            logging.error(f"Ошибка при получении информации о пользователе через бота: {e}")
            return {
                "user_id": user_id,
                "username": None,
                "first_name": None,
                "last_name": None,
                "is_banned": is_banned,
                "avatar": None
            }
    except Exception as e:
        logging.error(f"Ошибка при получении информации о пользователе: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/USFAPI/public/ban/{user_id}")
async def get_public_ban_info(user_id: int):
    try:
        # Проверяем валидность user_id
        if not isinstance(user_id, int) or user_id <= 0:
            raise HTTPException(status_code=400, detail="Неверный формат ID пользователя")

        conn = get_db()
        try:
            cursor = conn.cursor()
            # Используем параметризованный запрос для защиты от SQL-инъекций
            cursor.execute("""
                SELECT 
                    bans.user_id,
                    bans.admin_id,
                    bans.reason,
                    bans.proofs,
                    bans.images,
                    bans.ban_date,
                    admins.points as admin_points
                FROM bans
                LEFT JOIN admins ON bans.admin_id = admins.user_id
                WHERE bans.user_id = ?
            """, (user_id,))
            
            ban = cursor.fetchone()
            
            if not ban:
                return {"is_banned": False}
                
            # Получаем информацию об админе через бота
            try:
                admin_info = await bot.get_chat(ban[1])
                admin_username = admin_info.username or str(ban[1])
            except:
                admin_username = str(ban[1])
            
            return {
                "is_banned": True,
                "user_id": ban[0],
                "admin": {
                    "id": ban[1],
                    "username": admin_username,
                    "points": ban[6]
                },
                "reason": ban[2],
                "proofs": ban[3],
                "images": json.loads(ban[4]) if ban[4] else [],
                "ban_date": ban[5]
            }
        finally:
            conn.close()
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат ID пользователя")
    except Exception as e:
        logging.error(f"Ошибка при получении информации о бане: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

async def log_admin_action(admin_id: int, action_type: str, target_id: int = None, details: str = None):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO admin_logs (admin_id, action_type, target_id, details) VALUES (?, ?, ?, ?)",
            (admin_id, action_type, target_id, details)
        )
        conn.commit()
    except Exception as e:
        logging.error(f"Ошибка при логировании действия: {e}")
        raise
    finally:
        conn.close()

@app.get("/USFAPI/logs")
async def get_admin_logs(
    request: Request,
    authorization: str = Header(None),
    filter_admin: Optional[int] = None,
    action_type: Optional[str] = None
):
    try:
        current_admin_id = verify_webapp_and_admin(authorization)
        await log_admin_ip(current_admin_id, request)
        
        conn = get_db()
        try:
            cursor = conn.cursor()
            query = """
                SELECT 
                    admin_logs.id,
                    admin_logs.admin_id,
                    admin_logs.action_type,
                    admin_logs.target_id,
                    admin_logs.details,
                    admin_logs.timestamp,
                    admins.points as admin_points,
                    (SELECT ip_address 
                     FROM admin_ips 
                     WHERE admin_id = admin_logs.admin_id 
                     ORDER BY last_seen DESC 
                     LIMIT 1) as last_ip
                FROM admin_logs
                LEFT JOIN admins ON admin_logs.admin_id = admins.user_id
                WHERE 1=1
            """
            params = []
            
            if filter_admin is not None:
                query += " AND admin_logs.admin_id = ?"
                params.append(filter_admin)
                
            if action_type:
                query += " AND admin_logs.action_type = ?"
                params.append(action_type)
                
            query += " ORDER BY admin_logs.timestamp DESC LIMIT 100"
            
            cursor.execute(query, params)
            logs = cursor.fetchall()
            
            formatted_logs = []
            for log in logs:
                try:
                    admin_info = await bot.get_chat(log[1])
                    admin_username = admin_info.username or str(log[1])
                except:
                    admin_username = str(log[1])
                    
                log_entry = {
                    "id": log[0],
                    "admin": {
                        "id": log[1],
                        "username": admin_username,
                        "points": log[6] or 0  # Если points равен None, используем 0
                    },
                    "action_type": log[2],
                    "target_id": log[3],
                    "details": log[4],
                    "timestamp": log[5]
                }
                
                # Добавляем IP только если points меньше 90
                if (log[6] or 0) < 90 and log[7]:  # log[7] это last_ip
                    log_entry["admin"]["ip"] = log[7]
                
                formatted_logs.append(log_entry)
            
            return formatted_logs
        finally:
            conn.close()
    except Exception as e:
        logging.error(f"Ошибка при получении логов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/USFAPI/unban")
async def unban_user(
    request: Request,
    user_id: int = Form(...),
    reason: str = Form(...),
    authorization: str = Header(None)
):
    try:
        admin_id = verify_webapp_and_admin(authorization)
        await log_admin_ip(admin_id, request)
        
        conn = get_db()
        try:
            cursor = conn.cursor()
            # Проверяем, забанен ли пользователь
            cursor.execute("SELECT id FROM bans WHERE user_id = ?", (user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail="Пользователь не забанен")
            
            # Удаляем бан из БД
            cursor.execute("DELETE FROM bans WHERE user_id = ?", (user_id,))
            conn.commit()
            
            # Разбаниваем во всех группах
            groups = get_group_ids()
            success_groups = []
            failed_groups = []
            
            for group_id in groups:
                try:
                    await bot.unban_chat_member(
                        chat_id=group_id,
                        user_id=user_id,
                        only_if_banned=True
                    )
                    success_groups.append(group_id)
                except Exception as e:
                    failed_groups.append({"group_id": group_id, "error": str(e)})
            
            # Логируем действие
            await log_admin_action(
                admin_id=admin_id,
                action_type="unban",
                target_id=user_id,
                details=f"Причина: {reason}"
            )
            
            return {
                "status": "success",
                "message": "Пользователь разбанен",
                "success_groups": success_groups,
                "failed_groups": failed_groups
            }
        finally:
            conn.close()
    except Exception as e:
        logging.error(f"Ошибка при разбане: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/USFAPI/mute")
async def mute_user(
    request: Request,
    user_id: int = Form(...),
    reason: str = Form(...),
    proofs: str = Form(...),
    duration: str = Form(...),
    authorization: str = Header(None)
):
    try:
        admin_id = verify_webapp_and_admin(authorization)
        await log_admin_ip(admin_id, request)
        
        # Парсим длительность
        mute_seconds = parse_duration(duration)
        
        conn = get_db()
        try:
            cursor = conn.cursor()
            # Добавляем мут в БД
            cursor.execute(
                "INSERT INTO mutes (user_id, admin_id, reason, proofs, duration) VALUES (?, ?, ?, ?, ?)",
                (user_id, admin_id, reason, proofs, duration)
            )
            conn.commit()
            
            # Мутим во всех группах
            groups = get_group_ids()
            success_groups = []
            failed_groups = []
            
            for group_id in groups:
                try:
                    await bot.restrict_chat_member(
                        chat_id=group_id,
                        user_id=user_id,
                        permissions=types.ChatPermissions(
                            can_send_messages=False,
                            can_send_media_messages=False,
                            can_send_other_messages=False
                        ),
                        until_date=int(time.time() + mute_seconds)
                    )
                    success_groups.append(group_id)
                except Exception as e:
                    failed_groups.append({"group_id": group_id, "error": str(e)})
            
            # Логируем действие
            await log_admin_action(
                admin_id=admin_id,
                action_type="mute",
                target_id=user_id,
                details=f"Причина: {reason}, Длительность: {duration}"
            )
            
            return {
                "status": "success",
                "message": "Пользователь замучен",
                "success_groups": success_groups,
                "failed_groups": failed_groups
            }
        finally:
            conn.close()
    except Exception as e:
        logging.error(f"Ошибка при муте: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def log_admin_ip(admin_id: int, request: Request):
    try:
        ip = request.client.host
        conn = get_db()
        cursor = conn.cursor()
        
        # Удаляем существующую таблицу admin_ips
        cursor.execute("DROP TABLE IF EXISTS admin_ips")
        
        # Создаем таблицу заново с UNIQUE constraint
        cursor.execute("""
            CREATE TABLE admin_ips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL UNIQUE,
                ip_address TEXT NOT NULL,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES admins (user_id)
            )
        """)
        
        # Обновляем существующую запись или создаем новую
        cursor.execute("""
            INSERT INTO admin_ips (admin_id, ip_address, last_seen)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(admin_id) DO UPDATE SET 
                ip_address = excluded.ip_address,
                last_seen = CURRENT_TIMESTAMP
        """, (admin_id, ip))
        
        conn.commit()
    finally:
        conn.close()

async def run_api():
    config = uvicorn.Config("app:app", host="0.0.0.0", port=8000, reload=True)
    server = uvicorn.Server(config)
    await server.serve()

async def run_bot():
    try:
        await dp.start_polling()
    finally:
        await bot.session.close()

async def main():
    await asyncio.gather(run_api(), run_bot())

@app.post("/USFAPI/warn")
async def warn_user(
    request: Request,
    user_id: int = Form(...),
    reason: str = Form(...),
    proofs: str = Form(...),
    count: int = Form(...),
    authorization: str = Header(None)
):
    try:
        admin_id = verify_webapp_and_admin(authorization)
        await log_admin_ip(admin_id, request)
        
        conn = get_db()
        try:
            cursor = conn.cursor()
            
            # Проверяем текущее количество варнов
            cursor.execute("SELECT SUM(count) FROM warnings WHERE user_id = ?", (user_id,))
            current_warnings = cursor.fetchone()[0] or 0
            total_warnings = current_warnings + count
            
            # Если суммарное количество варнов >= 3, баним пользователя
            if total_warnings >= 3:
                # Добавляем бан
                await banuser_with_images(
                    request=request,
                    user_id=str(user_id),
                    reason=f"Автоматический бан: достигнут лимит предупреждений ({total_warnings}/3)\nПоследняя причина: {reason}",
                    proofs=proofs,
                    images=None,
                    authorization=authorization
                )
                
                return {
                    "status": "banned",
                    "message": "Пользователь получил максимальное количество предупреждений и был забанен"
                }
            
            # Добавляем варн в БД
            cursor.execute(
                "INSERT INTO warnings (user_id, admin_id, reason, proofs, count) VALUES (?, ?, ?, ?, ?)",
                (user_id, admin_id, reason, proofs, count)
            )
            conn.commit()
            
            # Логируем действие
            await log_admin_action(
                admin_id=admin_id,
                action_type="warn",
                target_id=user_id,
                details=f"Причина: {reason}, Количество: {count}, Всего: {total_warnings}/3"
            )
            
            return {
                "status": "success",
                "message": f"Выдано предупреждение ({total_warnings}/3)"
            }
        finally:
            conn.close()
    except Exception as e:
        logging.error(f"Ошибка при выдаче предупреждения: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/USFAPI/groups")
async def get_groups(authorization: str = Header(None)):
    try:
        admin_id = verify_webapp_and_admin(authorization)
        
        conn = get_db()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT group_id FROM groups")
            groups = cursor.fetchall()
            
            group_list = []
            for group in groups:
                group_id = group[0]
                try:
                    chat = await bot.get_chat(group_id)
                    members_count = await bot.get_chat_members_count(group_id)
                    
                    group_data = {
                        "id": group_id,
                        "title": chat.title,
                        "username": chat.username,
                        "members_count": members_count,
                        "photo": None
                    }
                    
                    if chat.photo:
                        file_info = await bot.get_file(chat.photo.big_file_id)
                        group_data["photo"] = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
                    
                    group_list.append(group_data)
                except Exception as e:
                    logging.error(f"Ошибка при получении информации о группе {group_id}: {e}")
            
            return group_list
        finally:
            conn.close()
    except Exception as e:
        logging.error(f"Ошибка при получении списка групп: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/USFAPI/groups/add")
async def add_group(
    request: Request,
    group_id: str = Form(...),
    authorization: str = Header(None)
):
    try:
        admin_id = verify_webapp_and_admin(authorization)
        
        # Преобразуем group_id в правильный формат
        try:
            if group_id.startswith('-100'):
                clean_group_id = int(group_id)
            elif group_id.startswith('-'):
                clean_group_id = int('-100' + group_id[1:])
            else:
                clean_group_id = int('-100' + group_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Неверный формат ID группы")
        
        logging.info(f"Пытаемся добавить группу с ID: {clean_group_id}")
        
        conn = get_db()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT points FROM admins WHERE user_id = ?", (admin_id,))
            admin_data = cursor.fetchone()
            if not admin_data or admin_data[0] < 90:
                raise HTTPException(status_code=403, detail="Недостаточно прав для управления группами")
            
            try:
                chat = await bot.get_chat(clean_group_id)
                
                # Проверяем, не существует ли уже такая группа
                cursor.execute("SELECT id FROM groups WHERE group_id = ?", (clean_group_id,))
                if cursor.fetchone():
                    raise HTTPException(status_code=400, detail="Эта группа уже добавлена")
                
                # Добавляем группу в БД
                cursor.execute(
                    "INSERT INTO groups (group_id, title, username) VALUES (?, ?, ?)",
                    (clean_group_id, chat.title, chat.username)
                )
                conn.commit()
                
                await log_admin_action(
                    admin_id=admin_id,
                    action_type="group_add",
                    target_id=clean_group_id,
                    details=f"Добавлена группа: {chat.title}"
                )
                
                return {
                    "status": "success",
                    "message": f"Группа {chat.title} успешно добавлена. Внимание: убедитесь, что бот является администратором для корректной работы всех функций."
                }
                
            except Exception as e:
                logging.error(f"Ошибка при добавлении группы: {e}")
                raise HTTPException(status_code=400, detail="Не удалось получить информацию о группе. Проверьте ID группы")
                
        finally:
            conn.close()
            
    except Exception as e:
        logging.error(f"Ошибка при добавлении группы: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/USFAPI/groups/{group_id}")
async def remove_group(
    request: Request,
    group_id: int,
    authorization: str = Header(None)
):
    try:
        admin_id = verify_webapp_and_admin(authorization)
        
        # Проверяем права админа
        conn = get_db()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT points FROM admins WHERE user_id = ?", (admin_id,))
            admin_data = cursor.fetchone()
            if not admin_data or admin_data[0] < 90:
                raise HTTPException(status_code=403, detail="Недостаточно прав для управления группами")
            
            # Получаем информацию о группе перед удалением
            cursor.execute("SELECT title FROM groups WHERE group_id = ?", (group_id,))
            group_data = cursor.fetchone()
            
            if not group_data:
                raise HTTPException(status_code=404, detail="Группа не найдена")
            
            # Удаляем группу
            cursor.execute("DELETE FROM groups WHERE group_id = ?", (group_id,))
            conn.commit()
            
            await log_admin_action(
                admin_id=admin_id,
                action_type="group_remove",
                target_id=group_id,
                details=f"Удалена группа: {group_data[0]}"
            )
            
            return {
                "status": "success",
                "message": f"Группа успешно удалена"
            }
            
        finally:
            conn.close()
            
    except Exception as e:
        logging.error(f"Ошибка при удалении группы: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    asyncio.run(main())
