from tools.news_tools import fetch_news
from tools.system_tools import (
    open_application,
    open_url,
    open_multiple_urls,
    take_screenshot,
    get_system_info,
    set_volume,
    get_clipboard,
    set_clipboard,
)
from tools.communication_tools import (
    send_whatsapp_message,
    send_sms,
    send_email,
)
from tools.productivity_tools import (
    create_file,
    read_file,
    list_directory,
    search_files,
    open_file,
    add_reminder,
    get_reminders,
    delete_reminder,
)
from tools.memory_tools import (
    remember_fact,
    recall_fact,
    list_memories,
)

ALL_TOOLS = [
    fetch_news,
    open_application,
    open_url,
    open_multiple_urls,
    take_screenshot,
    get_system_info,
    set_volume,
    get_clipboard,
    set_clipboard,
    send_whatsapp_message,
    send_sms,
    send_email,
    create_file,
    read_file,
    list_directory,
    search_files,
    open_file,
    add_reminder,
    get_reminders,
    delete_reminder,
    remember_fact,
    recall_fact,
    list_memories,
]