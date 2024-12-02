from typing_extensions import override

from garth import Client

from garmin_connect.repository import BaseOAuthRepository


class GarminConnectHTTPClient(Client):
    def __init__(self, repository: BaseOAuthRepository, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repository = repository

    @override
    def loads(self):
        oauth1, oauth2 = self.repository.get_oauth()
        self.configure(
            oauth1_token=oauth1,
            oauth2_token=oauth2,
            domain=oauth1.domain,
        )

    def dumps(self):
        self.repository.set_oauth(self.oauth1_token, self.oauth2_token)