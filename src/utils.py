async def split_text(message_text):

    # Разделяем текст по переносам строки
    parts = message_text.split('\n')

    # Удаляем пустые строки из списка
    non_empty_parts = [part.strip() for part in parts if part.strip()]

    # Проверяем, что есть хотя бы две непустые части
    if len(non_empty_parts) >= 2:
        post_text = non_empty_parts[0]  # Первая непустая часть — текст
        post_link = non_empty_parts[-1]  # Последняя непустая часть — ссылка
    else:
        post_text = message_text.strip()  # Если только одна часть, это текст
        post_link = ""  # Ссылка отсутствует

    text = (post_text, post_link) # Возвращаем кортеж с текстом и ссылкой

    return text