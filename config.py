import os
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    token: str
    allowed: frozenset[str]
    session_user: str = ''
    session_file: str = ''
    cooldown: int = 240

    @classmethod
    def from_environment(cls):
        token = os.environ.get('HC_WORKER_TOKEN', '')
        if len(token) < 32:
            raise RuntimeError('HC_WORKER_TOKEN must contain at least 32 characters')
        allowed = frozenset(x.strip().lower() for x in os.environ.get('HC_ALLOWED_USERNAMES', '').split(',') if x.strip())
        if not allowed or any(x != '*' and not re.fullmatch(r'[a-z0-9_.]{1,30}', x) for x in allowed):
            raise RuntimeError('Set HC_ALLOWED_USERNAMES to valid public handles or *')
        user = os.environ.get('HC_SESSION_USERNAME', '')
        file = os.environ.get('HC_SESSION_FILE', '')
        if bool(user) != bool(file):
            raise RuntimeError('Set both session username and session file, or neither')
        return cls(token, allowed, user, file)
