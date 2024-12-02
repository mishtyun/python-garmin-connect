import logging
import os
from abc import ABC, abstractmethod
from typing import Tuple
import json
from garth.utils import asdict
from garth.auth_tokens import OAuth1Token, OAuth2Token

__all__ = ["BaseOAuthRepository"]

logger = logging.getLogger(__name__)


class BaseOAuthRepository(ABC):
    @abstractmethod
    def get_oauth(self) -> Tuple[OAuth1Token, OAuth2Token]:
        pass

    @abstractmethod
    def set_oauth(self, oauth1_token: OAuth1Token, oauth2_token: OAuth2Token) -> bool:
        pass


class FileOAuthRepository(BaseOAuthRepository):
    def __init__(self, dir_path: str):
        self.dir_path = os.path.expanduser(dir_path)
        os.makedirs(self.dir_path, exist_ok=True)

    def get_oauth(self) -> Tuple[OAuth1Token, OAuth2Token]:
        oauth1_file = os.path.join(self.dir_path, "oauth1_token.json")
        oauth2_file = os.path.join(self.dir_path, "oauth2_token.json")

        with open(oauth1_file) as f:
            oauth1 = OAuth1Token(**json.load(f))
        with open(oauth2_file) as f:
            oauth2 = OAuth2Token(**json.load(f))

        return oauth1, oauth2

    def set_oauth(self, oauth1_token: OAuth1Token, oauth2_token: OAuth2Token) -> bool:
        if oauth1_token:
            path = os.path.join(self.dir_path, "oauth1_token.json")
            os.remove(path)

            with open(path, "w", encoding='utf-8') as f:
                json.dump(asdict(oauth1_token), f, ensure_ascii=False, indent=4)

        if oauth2_token:
            path = os.path.join(self.dir_path, "oauth2_token.json")
            os.remove(path)

            with open(path, "w", encoding='utf-8') as f:
                json.dump(asdict(oauth2_token), f, ensure_ascii=False, indent=4)
