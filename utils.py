from num2words import num2words
import re





MONTHS = {
    'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04',
    'мая': '05', 'июня': '06', 'июля': '07', 'августа': '08',
    'сентября': '09', 'октября': '10', 'ноября': '11', 'декабря': '12'
}

def clean(text):
    return re.sub(r'\s+', ' ', text.strip())

def normalize_amount(amount_str):
    """
    Приводит строку с суммой к целому числу в тенге.
    Убирает пробелы, обрезает копейки, возвращает строку.
    """
    if not amount_str:
        return None
    cleaned = amount_str.replace(' ', '').replace(',', '.')
    match = re.match(r'(\d+)(\.\d+)?', cleaned)
    if match:
        return str(int(float(match.group(0))))
    return None

def normalize_name(name):
    return ' '.join(word.capitalize() for word in name.split())

def format_amount_with_words(amount_str):
    """
    Преобразует сумму в строку вида:
    "123456 тенге (сто двадцать три тысячи четыреста пятьдесят шесть тенге)"
    """
    if not amount_str:
        return None
    try:
        amount_int = int(amount_str)
        words = num2words(amount_int, lang='ru')
        return f"{amount_str} тенге ({words} тенге)"
    except:
        return f"{amount_str} тенге"

def convert_date_format(day, month_word, year):
    month = MONTHS.get(month_word.lower())
    if not month:
        return f"{day} {month_word} {year}"  # fallback
    return f"{day.zfill(2)}.{month}.{year}"


def get_initials(full_name):
    if not full_name:
        return None
    parts = full_name.split()
    if len(parts) >= 3:
        return f"{parts[0]} {parts[1][0]}.{parts[2][0]}."
    elif len(parts) == 2:
        return f"{parts[0]} {parts[1][0]}."
    return full_name


def extract_company_core_name(company_full_name):
    if not company_full_name:
        return None
    # Удаляем юр. форму и всё до неё
    company_core = re.sub(
        r'^(Товарищество с ограниченной ответственностью|Акционерное общество)\s+', '', company_full_name
    )
    # Удаляем "Микрофинансовая организация" и всё до неё
    company_core = re.sub(r'^"?Микрофинансовая организация"?\s+', '', company_core)
    # Удаляем все кавычки
    company_core = company_core.replace('"', '').replace('«', '').replace('»', '')
    return company_core.strip()




