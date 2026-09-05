from typing import Set

# Global flag indicating whether the last error was a network/proxy failure
proxy_error_flag: bool = False

# Store the error message for recovery notifications
last_error_message: str = ""

# Set of chat IDs that experienced a network error and need a follow‑up notification
failed_chats: Set[int] = set()
