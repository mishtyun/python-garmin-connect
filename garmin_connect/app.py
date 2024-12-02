import logging

import requests
from garth.exc import GarthHTTPError

from garmin_connect.repository import FileOAuthRepository
from garmin_connect.service import Garmin
from garmin_connect.configuration import garmin_connect_configuration
from garmin_connect.exceptions import GarminConnectAuthenticationError
from garmin_connect.utils import get_mfa

logger = logging.getLogger(__name__)



def init_api():
    """Initialize Garmin API with your credentials."""

    oauth_repo = FileOAuthRepository(garmin_connect_configuration.tokenstore)

    try:
        logger.info(
            f"Trying to login to Garmin Connect using token data from the tokenstore directory ...\n"
        )

        garmin = Garmin(oauth_repo, garmin_connect_configuration)
        garmin.login()

    except (Exception, FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError):
        logger.info(
            "Login tokens not present, login with your Garmin Connect credentials to generate them.\n"
            f"They will be stored in tokenstore for future use.\n"
        )
        try:
            garmin = Garmin(
                oauth_repo,
                garmin_connect_configuration,
                prompt_mfa=get_mfa,
            )
            garmin.login(use_creds=True)

            # Save Oauth1 and Oauth2 token files to directory for next login
            garmin.garth.dumps()

            logger.info(
                f"Oauth tokens stored in tokenstore directory for future use. (first method)\n"
            )
        except (
            FileNotFoundError,
            GarthHTTPError,
            GarminConnectAuthenticationError,
            requests.exceptions.HTTPError,
        ) as err:
            logger.error(err)
            return None

    return garmin
