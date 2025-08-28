import hashlib
from typing import List, Union, Any

def generate_etag(event_ids: List[Union[str, int]]) -> str:
    """
    Генерирует ETag для списка event_ids.
    Используется для HTTP кэширования на фронте.
    """
    if not event_ids:
        return '"empty"'
    
    # Сортируем ID для консистентности
    sorted_ids = sorted(str(eid) for eid in event_ids)
    content = ",".join(sorted_ids)
    
    # Создаём MD5 хэш
    hash_obj = hashlib.md5(content.encode('utf-8'))
    return f'"{hash_obj.hexdigest()}"'

def generate_weak_etag(data: Any) -> str:
    """Generate weak ETag in unquoted form: W/<strong-etag-without-leading-quote>."""
    strong = generate_etag(data)
    # If strong is quoted like "abcd", produce W/abcd"
    if strong.startswith('"'):
        return 'W/' + strong[1:]
    return 'W/' + strong
