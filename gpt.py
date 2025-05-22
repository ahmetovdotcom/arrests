from openai import OpenAI
from config import OPENAI_API_KEY
import json


client = OpenAI(api_key=OPENAI_API_KEY) 

def extract_notary_data(text: str) -> dict:
    system_prompt = "Твоя задача распределить данные в словаре Python. Поля: email, phone, address, date_notification, isMale. Найди email, телефон и адрес. Если чего-то нет, оставь пустую строку. Если date_notification не найден, напиши слово 'сегодня'. В поле isMale укажи булево значение: True, если человек мужчина, и False, если женщина. Ответ строго в формате Python dict, чтобы его можно было распарсить как JSON, без пояснений, без ```json```. Пример: { \"email\": \"ivanov@mail.ru\", \"phone\": \"+7 777 777 7777\", \"address\": \"г. Астана, ул. Аксынгир 13, кв.1\", \"date_notification\": \"19.04.2025\", \"isMale\": true }"

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