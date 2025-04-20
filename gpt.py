from openai import OpenAI
from config import OPENAI_API_KEY
import json


client = OpenAI(api_key=OPENAI_API_KEY) 

def extract_notary_data(text: str) -> dict:
    system_prompt = (
        "Твоя задача распределить данные в словаре Python.\n"
        "Поля: email, phone, address, date_notification.\n"
        "Найди email, телефон и адрес. Если чего-то нет, оставь пустую строку.\n"
        "Если date_notification не найден, напиши слово 'сегодня'"
        "Ответ строго в формате Python dict, чтобы его можно было распарсить как JSON, без пояснений, без ```json```.\n"
        "Пример:\n"
        "{\n"
        "  \"email\": \"ivanov@mail.ru\",\n"
        "  \"phone\": \"+7 777 777 7777\",\n"
        "  \"address\": \"г. Астана, ул. Аксынгир 13, кв.1\"\n"
        "  \"date_notification\": \"19.04.2025\",\n"
        "}"
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content.strip()
    try:
        # Пытаемся привести к dict
        data = json.loads(content.replace("'", '"'))
    except json.JSONDecodeError:
        data = {"error": "Не удалось распарсить ответ", "raw": content}
    
    return data