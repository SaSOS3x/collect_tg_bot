async def default_post_text(user_name, user_login, message_text):
    
    text  = f"Пост от: <b>{user_name}</b>\n\n{message_text}\n\n<b>@{user_login}</b>"

    return text