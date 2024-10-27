import os

import requests
from garth.exc import GarthHTTPError

from garmin_connect.service import Garmin
from garmin_connect.configuration import garmin_connect_configuration
from garmin_connect.exceptions import GarminConnectAuthenticationError
from garmin_connect.utils import get_mfa


def init_api():
    """Initialize Garmin API with your credentials."""

    try:
        print(
            f"Trying to login to Garmin Connect using token data from the tokenstore directory ...\n"
        )

        garmin = Garmin(garmin_connect_configuration)
        garmin.login()

    except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError):
        print(
            "Login tokens not present, login with your Garmin Connect credentials to generate them.\n"
            f"They will be stored in tokenstore for future use.\n"
        )
        try:
            garmin = Garmin(
                garmin_connect_configuration,
                is_cn=False,
                prompt_mfa=get_mfa,
            )
            garmin.login()

            # Save Oauth1 and Oauth2 token files to directory for next login
            garmin.garth.dump(garmin_connect_configuration.tokenstore)

            print(
                f"Oauth tokens stored in tokenstore directory for future use. (first method)\n"
            )
        except (
            FileNotFoundError,
            GarthHTTPError,
            GarminConnectAuthenticationError,
            requests.exceptions.HTTPError,
        ) as err:
            print(err)
            return None

    return garmin
