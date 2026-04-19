import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("YANDEX_API_KEY")
folder_id = os.getenv("YANDEX_FOLDER_ID")

print(f"API Key длина: {len(api_key) if api_key else 'НЕТ'}")
print(f"API Key начало: {api_key[:10] if api_key else 'НЕТ'}...")
print(f"Folder ID: {folder_id}")