"""Python 3 API wrapper for Garmin Connect."""

import logging
import os
from datetime import date, datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union

from withings_sync import fit

from garmin_connect.configuration import GarminConnectConfiguration
from garmin_connect.constants import API_URLS, ACTIVITY_VISIBILITIES
from garmin_connect.exceptions import (
    GarminConnectInvalidFileFormatError,
    GarminConnectAuthenticationError,
)
from garmin_connect.http_client import GarminConnectHTTPClient
from garmin_connect.repository import BaseOAuthRepository
from garmin_connect.utils import get_caller_name

logger = logging.getLogger(__name__)


class Garmin:
    """Class for fetching data from Garmin Connect."""

    def __init__(
            self,
            oauth_repository: BaseOAuthRepository,
            garmin_configuration: GarminConnectConfiguration,
            prompt_mfa=None,
    ):
        """Create a new class instance."""
        self.username = garmin_configuration.email
        self.password = garmin_configuration.password

        self.prompt_mfa = prompt_mfa

        self.display_name = None
        self.full_name = None
        self.unit_system = None

        self.garth = GarminConnectHTTPClient(
            repository=oauth_repository,
            domain="garmin.com"
        )

        self.garmin_connect_hill_score_url = "/metrics-service/metrics/hillscore"

        self.garmin_connect_endurance_score_url = (
            "/metrics-service/metrics/endurancescore"
        )

        self.garmin_connect_pregnancy_snapshot_url = (
            "periodichealth-service/menstrualcycle/pregnancysnapshot"
        )
        self.garmin_connect_goals_url = "/goal-service/goal/goals"

        self.garmin_connect_hrv_url = "/hrv-service/hrv"

        self.garmin_connect_training_readiness_url = (
            "/metrics-service/metrics/trainingreadiness"
        )

        self.garmin_connect_race_predictor_url = (
            "/metrics-service/metrics/racepredictions"
        )
        self.garmin_connect_training_status_url = (
            "/metrics-service/metrics/trainingstatus/aggregated"
        )
        self.garmin_connect_user_summary_chart = (
            "/wellness-service/wellness/dailySummaryChart"
        )
        self.garmin_connect_floors_chart_daily_url = (
            "/wellness-service/wellness/floorsChartData/daily"
        )
        self.garmin_connect_heartrates_daily_url = (
            "/wellness-service/wellness/dailyHeartRate"
        )
        self.garmin_connect_daily_respiration_url = (
            "/wellness-service/wellness/daily/respiration"
        )

        self.garmin_connect_fit_download = "/download-service/files/activity"
        self.garmin_connect_tcx_download = "/download-service/export/tcx/activity"
        self.garmin_connect_gpx_download = "/download-service/export/gpx/activity"
        self.garmin_connect_kml_download = "/download-service/export/kml/activity"
        self.garmin_connect_csv_download = "/download-service/export/csv/activity"

        self.garmin_connect_gear = "/gear-service/gear/filterGear"
        self.garmin_connect_gear_baseurl = "/gear-service/gear/"

        self.garmin_request_reload_url = "/wellness-service/wellness/epoch/request"

        self.garmin_workouts = "/workout-service"

        self.garmin_connect_delete_activity_url = "/activity-service/activity"

    @staticmethod
    def get_url(**url_params) -> str:
        url = API_URLS.get(get_caller_name(), "").format(**url_params)
        return url

    def connectapi(self, path, **kwargs):
        return self.garth.connectapi(path, **kwargs)

    def download(self, path, **kwargs):
        return self.garth.download(path, **kwargs)

    def login(self, use_creds: bool = False):
        """Log in using Garth."""
        if use_creds:
            self.garth.login(self.username, self.password)
        else:
            self.garth.loads()

        self.display_name = self.garth.profile.get("displayName")
        self.full_name = self.garth.profile.get("fullName")

        user_settings_url = self.get_url()
        settings = self.garth.connectapi(user_settings_url)
        self.unit_system = settings["userData"]["measurementSystem"]

        return True

    def get_full_name(self):
        """Return full name."""

        return self.full_name

    def get_unit_system(self):
        """Return unit system."""

        return self.unit_system

    def get_stats(self, cdate: str) -> Dict[str, Any]:
        """
        Return user activity summary for 'cdate' format 'YYYY-MM-DD'
        (compat for garminconnect).
        """

        return self.get_user_summary(cdate)

    def get_user_summary(self, cdate: str) -> Dict[str, Any]:
        """Return user activity summary for 'cdate' format 'YYYY-MM-DD'."""

        url = self.get_url(display_name=self.display_name)
        params = {"calendarDate": str(cdate)}
        logger.debug("Requesting user summary")

        response = self.connectapi(url, params=params)

        if response["privacyProtected"] is True:
            raise GarminConnectAuthenticationError("Authentication error")

        return response

    def get_steps_data(self, cdate):
        """Fetch available steps data 'cDate' format 'YYYY-MM-DD'."""

        url = f"{self.garmin_connect_user_summary_chart}/{self.display_name}"
        params = {"date": str(cdate)}
        logger.debug("Requesting steps data")

        return self.connectapi(url, params=params)

    def get_floors(self, cdate):
        """Fetch available floors data 'cDate' format 'YYYY-MM-DD'."""

        url = f"{self.garmin_connect_floors_chart_daily_url}/{cdate}"
        logger.debug("Requesting floors data")

        return self.connectapi(url)

    def get_daily_steps(self, start, end):
        """Fetch available steps data 'start' and 'end' format 'YYYY-MM-DD'."""

        url = self.get_url(start=start, end=end)
        logger.debug("Requesting daily steps data")

        return self.connectapi(url)

    def get_heart_rates(self, cdate):
        """Fetch available heart rates data 'cDate' format 'YYYY-MM-DD'."""

        url = f"{self.garmin_connect_heartrates_daily_url}/{self.display_name}"
        params = {"date": str(cdate)}
        logger.debug("Requesting heart rates")

        return self.connectapi(url, params=params)

    def get_stats_and_body(self, cdate):
        """Return activity data and body composition (compat for garminconnect)."""

        return {
            **self.get_stats(cdate),
            **self.get_body_composition(cdate)["totalAverage"],
        }

    def get_body_composition(self, start_date: str, end_date=None) -> Dict[str, Any]:
        """
        Return available body composition data for 'start_date' format
        'YYYY-MM-DD' through end_date 'YYYY-MM-DD'.
        """

        if end_date is None:
            end_date = start_date
        url = self.get_url()
        params = {"startDate": str(start_date), "endDate": str(end_date)}
        logger.debug("Requesting body composition")

        return self.connectapi(url, params=params)

    def add_body_composition(
            self,
            timestamp: Optional[str],
            weight: float,
            percent_fat: Optional[float] = None,
            percent_hydration: Optional[float] = None,
            visceral_fat_mass: Optional[float] = None,
            bone_mass: Optional[float] = None,
            muscle_mass: Optional[float] = None,
            basal_met: Optional[float] = None,
            active_met: Optional[float] = None,
            physique_rating: Optional[float] = None,
            metabolic_age: Optional[float] = None,
            visceral_fat_rating: Optional[float] = None,
            bmi: Optional[float] = None,
    ):
        dt = datetime.fromisoformat(timestamp) if timestamp else datetime.now()
        fitEncoder = fit.FitEncoderWeight()
        fitEncoder.write_file_info()
        fitEncoder.write_file_creator()
        fitEncoder.write_device_info(dt)
        fitEncoder.write_weight_scale(
            dt,
            weight=weight,
            percent_fat=percent_fat,
            percent_hydration=percent_hydration,
            visceral_fat_mass=visceral_fat_mass,
            bone_mass=bone_mass,
            muscle_mass=muscle_mass,
            basal_met=basal_met,
            active_met=active_met,
            physique_rating=physique_rating,
            metabolic_age=metabolic_age,
            visceral_fat_rating=visceral_fat_rating,
            bmi=bmi,
        )
        fitEncoder.finish()

        url = API_URLS.get("upload_activity")  # TODO revoke
        files = {
            "file": ("body_composition.fit", fitEncoder.getvalue()),
        }
        return self.garth.post("connectapi", url, files=files, api=True)

    def add_weigh_in(self, weight: int, unitKey: str = "kg", timestamp: str = ""):
        """Add a weigh-in (default to kg)"""

        url = self.get_url()
        dt = datetime.fromisoformat(timestamp) if timestamp else datetime.now()
        # Apply timezone offset to get UTC/GMT time
        dtGMT = dt.astimezone(timezone.utc)
        payload = {
            "dateTimestamp": dt.isoformat()[:19] + ".00",
            "gmtTimestamp": dtGMT.isoformat()[:19] + ".00",
            "unitKey": unitKey,
            "sourceType": "MANUAL",
            "value": weight,
        }
        logger.debug("Adding weigh-in")

        return self.garth.post("connectapi", url, json=payload)

    def get_weigh_ins(self, start_date: str, end_date: str):
        """Get weigh-ins between start_date and end_date using format 'YYYY-MM-DD'."""

        url = self.get_url(start_date=start_date, end_date=end_date)
        params = {"includeAll": True}
        logger.debug("Requesting weigh-ins")

        return self.connectapi(url, params=params)

    def get_daily_weigh_ins(self, cdate: str):
        """Get weigh-ins for 'cdate' format 'YYYY-MM-DD'."""

        url = self.get_url(cdate=cdate)
        params = {"includeAll": True}
        logger.debug("Requesting weigh-ins")

        return self.connectapi(url, params=params)

    def delete_weigh_in(self, weight_pk: str, cdate: str):
        """Delete specific weigh-in."""
        url = self.get_url(weight_pk=weight_pk, cdate=cdate)
        logger.debug("Deleting weigh-in")

        return self.garth.request(
            "DELETE",
            "connectapi",
            url,
            api=True,
        )

    def delete_weigh_ins(self, cdate: str, delete_all: bool = False):
        """
        Delete weigh-in for 'cdate' format 'YYYY-MM-DD'.
        Includes option to delete all weigh-ins for that date.
        """

        daily_weigh_ins = self.get_daily_weigh_ins(cdate)
        weigh_ins = daily_weigh_ins.get("dateWeightList", [])
        if not weigh_ins or len(weigh_ins) == 0:
            logger.warning(f"No weigh-ins found on {cdate}")
            return
        elif len(weigh_ins) > 1:
            logger.warning(f"Multiple weigh-ins found for {cdate}")
            if not delete_all:
                logger.warning(
                    f"Set delete_all to True to delete all {len(weigh_ins)} weigh-ins"
                )
                return

        for w in weigh_ins:
            self.delete_weigh_in(w["samplePk"], cdate)

        return len(weigh_ins)

    def get_body_battery(self, start_date: str, end_date=None) -> List[Dict[str, Any]]:
        """
        Return body battery values by day for 'start_date' format
        'YYYY-MM-DD' through end_date 'YYYY-MM-DD'
        """
        end_date = end_date if end_date is not None else start_date
        params = {"startDate": str(start_date), "endDate": str(end_date)}

        url = self.get_url()
        logger.debug("Requesting body battery data")
        return self.connectapi(url, params=params)

    def get_body_battery_events(self, cdate: str) -> List[Dict[str, Any]]:
        """
        Return body battery events for date 'cdate' format 'YYYY-MM-DD'.
        The return value is a list of dictionaries, where each dictionary contains event data for a specific event.
        Events can include sleep, recorded activities, auto-detected activities, and naps
        """

        url = self.get_url(cdate=cdate)
        logger.debug("Requesting body battery event data")

        return self.connectapi(url)

    def set_blood_pressure(
            self,
            systolic: int,
            diastolic: int,
            pulse: int,
            timestamp: str = "",
            notes: str = "",
    ):
        """
        Add blood pressure measurement
        """

        url = self.get_url()
        dt = datetime.fromisoformat(timestamp) if timestamp else datetime.now()
        # Apply timezone offset to get UTC/GMT time
        dtGMT = dt.astimezone(timezone.utc)
        payload = {
            "measurementTimestampLocal": dt.isoformat()[:19] + ".00",
            "measurementTimestampGMT": dtGMT.isoformat()[:19] + ".00",
            "systolic": systolic,
            "diastolic": diastolic,
            "pulse": pulse,
            "sourceType": "MANUAL",
            "notes": notes,
        }

        logger.debug("Adding blood pressure")

        return self.garth.post("connectapi", url, json=payload)

    def get_blood_pressure(self, start_date: str, end_date=None) -> Dict[str, Any]:
        """
        Returns blood pressure by day for 'start_date' format
        'YYYY-MM-DD' through end_date 'YYYY-MM-DD'
        """
        end_date = end_date if end_date is not None else start_date

        url = self.get_url(start_date=start_date, end_date=end_date)
        params = {"includeAll": True}
        logger.debug("Requesting blood pressure data")

        return self.connectapi(url, params=params)

    def get_max_metrics(self, cdate: str) -> Dict[str, Any]:
        """Return available max metric data for 'cdate' format 'YYYY-MM-DD'."""

        url = self.get_url(cdate=cdate)
        logger.debug("Requesting max metrics")

        return self.connectapi(url)

    def add_hydration_data(
            self, value_in_ml: float, timestamp=None, cdate: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add hydration data in ml.  Defaults to current date and current timestamp if left empty
        :param float required - value_in_ml: The number of ml of water you wish to add (positive) or subtract (negative)
        :param timestamp optional - timestamp: The timestamp of the hydration update, format 'YYYY-MM-DDThh:mm:ss.ms' Defaults to current timestamp
        :param date optional - cdate: The date of the weigh in, format 'YYYY-MM-DD'. Defaults to current date
        """

        url = self.get_url()

        if timestamp is None and cdate is None:
            # If both are null, use today and now
            raw_date = date.today()
            cdate = str(raw_date)

            raw_ts = datetime.now()
            timestamp = datetime.strftime(raw_ts, "%Y-%m-%dT%H:%M:%S.%f")

        elif cdate is not None and timestamp is None:
            # If cdate is not null, use timestamp associated with midnight
            raw_ts = datetime.strptime(cdate, "%Y-%m-%d")
            timestamp = datetime.strftime(raw_ts, "%Y-%m-%dT%H:%M:%S.%f")

        elif cdate is None and timestamp is not None:
            # If timestamp is not null, set cdate equal to date part of timestamp
            raw_ts = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")
            cdate = str(raw_ts.date())

        payload = {
            "calendarDate": cdate,
            "timestampLocal": timestamp,
            "valueInML": value_in_ml,
        }

        logger.debug("Adding hydration data")

        return self.garth.put("connectapi", url, json=payload)

    def get_hydration_data(self, cdate: str) -> Dict[str, Any]:
        """Return available hydration data 'cdate' format 'YYYY-MM-DD'."""

        url = self.get_url(cdate=cdate)
        logger.debug("Requesting hydration data")

        return self.connectapi(url)

    def get_respiration_data(self, cdate: str) -> Dict[str, Any]:
        """Return available respiration data 'cdate' format 'YYYY-MM-DD'."""

        url = f"{self.garmin_connect_daily_respiration_url}/{cdate}"
        logger.debug("Requesting respiration data")

        return self.connectapi(url)

    def get_spo2_data(self, cdate: str) -> Dict[str, Any]:
        """Return available SpO2 data 'cdate' format 'YYYY-MM-DD'."""

        url = self.get_url(cdate=cdate)
        logger.debug("Requesting SpO2 data")

        return self.connectapi(url)

    def get_all_day_stress(self, cdate: str) -> Dict[str, Any]:
        """Return available all day stress data 'cdate' format 'YYYY-MM-DD'."""

        url = self.get_url(cdate=cdate)
        logger.debug("Requesting all day stress data")

        return self.connectapi(url)

    def get_all_day_events(self, cdate: str) -> Dict[str, Any]:
        """
        Return available daily events data 'cdate' format 'YYYY-MM-DD'.
        Includes autodetected activities, even if not recorded on the watch
        """

        url = self.get_url(cdate=cdate)
        logger.debug("Requesting all day stress data")

        return self.connectapi(url)

    def get_personal_record(self) -> Dict[str, Any]:
        """Return personal records for current user."""

        url = self.get_url(display_name=self.display_name)
        logger.debug("Requesting personal records for user")

        return self.connectapi(url)

    def get_earned_badges(self) -> Dict[str, Any]:
        """Return earned badges for current user."""

        url = self.get_url()
        logger.debug("Requesting earned badges for user")

        return self.connectapi(url)

    def get_adhoc_challenges(self, start, limit) -> Dict[str, Any]:
        """Return adhoc challenges for current user."""

        url = self.get_url()
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting adhoc challenges for user")

        return self.connectapi(url, params=params)

    def get_badge_challenges(self, start, limit) -> Dict[str, Any]:
        """Return badge challenges for current user."""

        url = self.get_url()
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting badge challenges for user")

        return self.connectapi(url, params=params)

    def get_available_badge_challenges(self, start, limit) -> Dict[str, Any]:
        """Return available badge challenges."""

        url = self.get_url()
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting available badge challenges")

        return self.connectapi(url, params=params)

    def get_non_completed_badge_challenges(self, start, limit) -> Dict[str, Any]:
        """Return badge non-completed challenges for current user."""

        url = self.get_url()
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting badge challenges for user")

        return self.connectapi(url, params=params)

    def get_inprogress_virtual_challenges(self, start, limit) -> Dict[str, Any]:
        """Return in-progress virtual challenges for current user."""

        url = self.get_url()
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting in-progress virtual challenges for user")

        return self.connectapi(url, params=params)

    def get_sleep_data(self, cdate: str) -> Dict[str, Any]:
        """Return sleep data for current user."""
        url = self.get_url(display_name=self.display_name)
        params = {"date": str(cdate), "nonSleepBufferMinutes": 60}
        logger.debug("Requesting sleep data")

        return self.connectapi(url, params=params)

    def get_stress_data(self, cdate: str) -> Dict[str, Any]:
        """Return stress data for current user."""

        url = self.get_url(cdate=cdate)
        logger.debug("Requesting stress data")

        return self.connectapi(url)

    def get_rhr_day(self, cdate: str) -> Dict[str, Any]:
        """Return resting heartrate data for current user."""

        url = self.get_url(display_name=self.display_name)
        params = {
            "fromDate": str(cdate),
            "untilDate": str(cdate),
            "metricId": 60,
        }
        logger.debug("Requesting resting heartrate data")

        return self.connectapi(url, params=params)

    def get_hrv_data(self, cdate: str) -> Dict[str, Any]:
        """Return Heart Rate Variability (hrv) data for current user."""

        url = f"{self.garmin_connect_hrv_url}/{cdate}"
        logger.debug("Requesting Heart Rate Variability (hrv) data")

        return self.connectapi(url)

    def get_training_readiness(self, cdate: str) -> Dict[str, Any]:
        """Return training readiness data for current user."""

        url = f"{self.garmin_connect_training_readiness_url}/{cdate}"
        logger.debug("Requesting training readiness data")

        return self.connectapi(url)

    def get_endurance_score(self, start_date: str, end_date=None):
        """
        Return endurance score by day for 'start_date' format 'YYYY-MM-DD'
        through end_date 'YYYY-MM-DD'.
        Using a single day returns the precise values for that day.
        Using a range returns the aggregated weekly values for that week.
        """

        if end_date is None:
            url = self.garmin_connect_endurance_score_url
            params = {"calendarDate": str(start_date)}
            logger.debug("Requesting endurance score data for a single day")

            return self.connectapi(url, params=params)
        else:
            url = f"{self.garmin_connect_endurance_score_url}/stats"
            params = {
                "startDate": str(start_date),
                "endDate": str(end_date),
                "aggregation": "weekly",
            }
            logger.debug("Requesting endurance score data for a range of days")

            return self.connectapi(url, params=params)

    def get_race_predictions(self, start_date=None, end_date=None, _type=None):
        """
        Return race predictions for the 5k, 10k, half marathon and marathon.
        Accepts either 0 parameters or all three:
        If all parameters are empty, returns the race predictions for the current date
        Or returns the race predictions for each day or month in the range provided

        Keyword Arguments:
        'start_date' the date of the earliest race predictions
        Cannot be more than one year before 'end_date'
        'end_date' the date of the last race predictions
        '_type' either 'daily' (the predictions for each day in the range) or
        'monthly' (the aggregated monthly prediction for each month in the range)
        """

        valid = {"daily", "monthly", None}
        if _type not in valid:
            raise ValueError("results: _type must be one of %r." % valid)

        if _type is None and start_date is None and end_date is None:
            url = (
                    self.garmin_connect_race_predictor_url + f"/latest/{self.display_name}"
            )
            return self.connectapi(url)

        elif _type is not None and start_date is not None and end_date is not None:
            url = (
                    self.garmin_connect_race_predictor_url + f"/{_type}/{self.display_name}"
            )
            params = {
                "fromCalendarDate": str(start_date),
                "toCalendarDate": str(end_date),
            }
            return self.connectapi(url, params=params)

        else:
            raise ValueError("You must either provide all parameters or no parameters")

    def get_training_status(self, cdate: str) -> Dict[str, Any]:
        """Return training status data for current user."""

        url = f"{self.garmin_connect_training_status_url}/{cdate}"
        logger.debug("Requesting training status data")

        return self.connectapi(url)

    def get_fitnessage_data(self, cdate: str) -> Dict[str, Any]:
        """Return Fitness Age data for current user."""

        url = self.get_url(cdate=cdate)
        logger.debug("Requesting Fitness Age data")

        return self.connectapi(url)

    def get_hill_score(self, start_date: str, end_date=None):
        """
        Return hill score by day from 'start_date' format 'YYYY-MM-DD'
        to end_date 'YYYY-MM-DD'
        """

        if end_date is None:
            url = self.garmin_connect_hill_score_url
            params = {"calendarDate": str(start_date)}
            logger.debug("Requesting hill score data for a single day")

            return self.connectapi(url, params=params)

        else:
            url = f"{self.garmin_connect_hill_score_url}/stats"
            params = {
                "startDate": str(start_date),
                "endDate": str(end_date),
                "aggregation": "daily",
            }
            logger.debug("Requesting hill score data for a range of days")

            return self.connectapi(url, params=params)

    def get_devices(self) -> List[Dict[str, Any]]:
        """Return available devices for the current user account."""

        url = self.get_url()
        logger.debug("Requesting devices")

        return self.connectapi(url)

    def get_device_settings(self, device_id: str) -> Dict[str, Any]:
        """Return device settings for device with 'device_id'."""

        url = self.get_url(device_id=device_id)
        logger.debug("Requesting device settings")

        return self.connectapi(url)

    def get_primary_training_device(self) -> Dict[str, Any]:
        """Return detailed information around primary training devices, included the specified device and the
        priority of all devices.
        """

        url = self.get_url()
        logger.debug("Requesting primary training device information")

        return self.connectapi(url)

    def get_device_solar_data(
            self, device_id: str, start_date: str, end_date=None
    ) -> Dict[str, Any]:
        """Return solar data for compatible device with 'device_id'"""
        if end_date is None:
            end_date = start_date
            single_day = True
        else:
            single_day = False

        params = {"singleDayView": single_day}

        url = self.get_url()
        return self.connectapi(url, params=params)["deviceSolarInput"]

    def get_device_alarms(self) -> List[Any]:
        """Get list of active alarms from all devices."""

        logger.debug("Requesting device alarms")

        alarms = []
        devices = self.get_devices()
        for device in devices:
            device_settings = self.get_device_settings(device["deviceId"])
            device_alarms = device_settings["alarms"]
            if device_alarms is not None:
                alarms += device_alarms
        return alarms

    def get_device_last_used(self):
        """Return device last used."""

        url = self.get_url()
        logger.debug("Requesting device last used")

        return self.connectapi(url)

    def get_activities(self, start, limit):
        """Return available activities."""

        url = self.get_url()
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting activities")

        return self.connectapi(url, params=params)

    def get_activities_fordate(self, for_date: str):
        """Return available activities for date."""

        url = self.get_url(for_date=for_date)
        logger.debug(f"Requesting activities for date {for_date}")

        return self.connectapi(url)

    def set_activity_name(self, activity_id, title):
        """Set name for activity with id."""

        url = self.get_url(activity_id=activity_id)
        payload = {"activityId": activity_id, "activityName": title}

        return self.garth.put("connectapi", url, json=payload, api=True)

    def change_activity_visibility(
            self, activity_id: Union[int, str], visibility: ACTIVITY_VISIBILITIES
    ):
        url = self.get_url(activity_id=activity_id)

        payload = {
            "accessControlRuleDTO": {"typeKey": visibility},
            "activityId": activity_id,
        }

        return self.garth.put("connectapi", url, json=payload, api=True)

    def get_last_activity(self):
        """Return last activity."""

        activities = self.get_activities(0, 1)
        if activities:
            return activities[-1]

        return None

    def upload_activity(self, activity_path: str):
        """Upload activity in fit format from file."""
        # This code is borrowed from python-garminconnect-enhanced ;-)

        file_base_name = os.path.basename(activity_path)
        file_extension = file_base_name.split(".")[-1]
        allowed_file_extension = (
                file_extension.upper() in Garmin.ActivityUploadFormat.__members__
        )

        if allowed_file_extension:
            files = {
                "file": (file_base_name, open(activity_path, "rb" or "r")),
            }
            url = self.get_url()
            return self.garth.post("connectapi", url, files=files, api=True)
        else:
            raise GarminConnectInvalidFileFormatError(
                f"Could not upload {activity_path}"
            )

    def delete_activity(self, activity_id):
        """Delete activity with specified id"""

        url = f"{self.garmin_connect_delete_activity_url}/{activity_id}"
        logger.debug("Deleting activity with id %s", activity_id)

        return self.garth.request(
            "DELETE",
            "connectapi",
            url,
            api=True,
        )

    def get_activities_by_date(self, start_date, end_date, activity_type=None):
        """
        Fetch available activities between specific dates
        :param start_date: String in the format YYYY-MM-DD
        :param end_date: String in the format YYYY-MM-DD
        :param activity_type: (Optional) Type of activity you are searching
                             Possible values are [cycling, running, swimming,
                             multi_sport, fitness_equipment, hiking, walking, other]
        :return: list of JSON activities
        """

        activities = []
        start = 0
        limit = 20
        # mimicking the behavior of the web interface that fetches
        # 20 activities at a time
        # and automatically loads more on scroll
        url = self.get_url()
        params = {
            "startDate": str(start_date),
            "endDate": str(end_date),
            "start": str(start),
            "limit": str(limit),
        }
        if activity_type:
            params["activityType"] = str(activity_type)

        logger.debug(f"Requesting activities by date from {start_date} to {end_date}")
        while True:
            params["start"] = str(start)
            logger.debug(f"Requesting activities {start} to {start + limit}")
            act = self.connectapi(url, params=params)
            if act:
                activities.extend(act)
                start = start + limit
            else:
                break

        return activities

    def get_progress_summary_between_dates(
            self, start_date, end_date, metric="distance", group_by_activities=True
    ):
        """
        Fetch progress summary data between specific dates
        :param start_date: String in the format YYYY-MM-DD
        :param end_date: String in the format YYYY-MM-DD
        :param metric: metric to be calculated in the summary:
            "elevationGain", "duration", "distance", "movingDuration"
        :param group_by_activities: group the summary by activity type
        :return: list of JSON activities with their aggregated progress summary
        """

        url = self.get_url()
        params = {
            "startDate": str(start_date),
            "endDate": str(end_date),
            "aggregation": "lifetime",
            "groupByParentActivityType": str(group_by_activities),
            "metric": str(metric),
        }

        logger.debug(f"Requesting fitness-stats by date from {start_date} to {end_date}")
        return self.connectapi(url, params=params)

    def get_activity_types(self):
        url = self.get_url()
        logger.debug("Requesting activity types")
        return self.connectapi(url)

    def get_goals(self, status="active", start=1, limit=30):
        """
        Fetch all goals based on status
        :param status: Status of goals (valid options are "active", "future", or "past")
        :type status: str
        :param start: Initial goal index
        :type start: int
        :param limit: Pagination limit when retrieving goals
        :type limit: int
        :return: list of goals in JSON format
        """

        goals = []
        url = self.garmin_connect_goals_url
        params = {
            "status": status,
            "start": str(start),
            "limit": str(limit),
            "sortOrder": "asc",
        }

        logger.debug(f"Requesting {status} goals")
        while True:
            params["start"] = str(start)
            logger.debug(f"Requesting {status} goals {start} to {start + limit - 1}")
            goals_json = self.connectapi(url, params=params)
            if goals_json:
                goals.extend(goals_json)
                start = start + limit
            else:
                break

        return goals

    def get_gear(self, userProfileNumber):
        """Return all user gear."""
        url = f"{self.garmin_connect_gear}?userProfilePk={userProfileNumber}"
        logger.debug("Requesting gear for user %s", userProfileNumber)

        return self.connectapi(url)

    def get_gear_stats(self, gearUUID):
        url = f"{self.garmin_connect_gear_baseurl}stats/{gearUUID}"
        logger.debug("Requesting gear stats for gearUUID %s", gearUUID)
        return self.connectapi(url)

    def get_gear_defaults(self, userProfileNumber):
        url = (
            f"{self.garmin_connect_gear_baseurl}user/"
            f"{userProfileNumber}/activityTypes"
        )
        logger.debug("Requesting gear for user %s", userProfileNumber)
        return self.connectapi(url)

    def set_gear_default(self, activityType, gearUUID, defaultGear=True):
        defaultGearString = "/default/true" if defaultGear else ""
        method_override = "PUT" if defaultGear else "DELETE"
        url = (
            f"{self.garmin_connect_gear_baseurl}{gearUUID}/"
            f"activityType/{activityType}{defaultGearString}"
        )
        return self.garth.request(method_override, "connectapi", url, api=True)

    class ActivityDownloadFormat(Enum):
        """Activity variables."""

        ORIGINAL = auto()
        TCX = auto()
        GPX = auto()
        KML = auto()
        CSV = auto()

    class ActivityUploadFormat(Enum):
        FIT = auto()
        GPX = auto()
        TCX = auto()

    def download_activity(self, activity_id, dl_fmt=ActivityDownloadFormat.TCX):
        """
        Downloads activity in requested format and returns the raw bytes. For
        "Original" will return the zip file content, up to user to extract it.
        "CSV" will return a csv of the splits.
        """
        activity_id = str(activity_id)
        urls = {
            Garmin.ActivityDownloadFormat.ORIGINAL: f"{self.garmin_connect_fit_download}/{activity_id}",  # noqa
            Garmin.ActivityDownloadFormat.TCX: f"{self.garmin_connect_tcx_download}/{activity_id}",  # noqa
            Garmin.ActivityDownloadFormat.GPX: f"{self.garmin_connect_gpx_download}/{activity_id}",  # noqa
            Garmin.ActivityDownloadFormat.KML: f"{self.garmin_connect_kml_download}/{activity_id}",  # noqa
            Garmin.ActivityDownloadFormat.CSV: f"{self.garmin_connect_csv_download}/{activity_id}",  # noqa
        }
        if dl_fmt not in urls:
            raise ValueError(f"Unexpected value {dl_fmt} for dl_fmt")
        url = urls[dl_fmt]

        logger.debug("Downloading activities from %s", url)

        return self.download(url)

    def get_activity_splits(self, activity_id):
        """Return activity splits."""

        activity_id = str(activity_id)
        url = self.get_url(activity_id=activity_id)
        logger.debug("Requesting splits for activity id %s", activity_id)

        return self.connectapi(url)

    def get_activity_typed_splits(self, activity_id):
        """Return typed activity splits. Contains similar info to `get_activity_splits`, but for certain activity types
        (e.g., Bouldering), this contains more detail."""

        url = self.get_url(activity_id=str(activity_id))
        logger.debug("Requesting typed splits for activity id %s", activity_id)

        return self.connectapi(url)

    def get_activity_split_summaries(self, activity_id):
        """Return activity split summaries."""

        url = self.get_url(activity_id=str(activity_id))
        logger.debug("Requesting split summaries for activity id %s", activity_id)

        return self.connectapi(url)

    def get_activity_weather(self, activity_id):
        """Return activity weather."""

        url = self.get_url(activity_id=str(activity_id))
        logger.debug(f"Requesting weather for {activity_id=}")

        return self.connectapi(url)

    def get_activity_hr_in_timezones(self, activity_id):
        """Return activity heartrate in timezones."""

        url = self.get_url(activity_id=str(activity_id))
        logger.debug("Requesting split summaries for activity id %s", activity_id)

        return self.connectapi(url)

    def get_activity(self, activity_id):
        """Return activity summary, including basic splits."""

        url = self.get_url(activity_id=str(activity_id))
        logger.debug("Requesting activity summary data for activity id %s", activity_id)

        return self.connectapi(url)

    def get_activity_details(self, activity_id, maxchart=2000, maxpoly=4000):
        """Return activity details."""

        activity_id = str(activity_id)
        params = {
            "maxChartSize": str(maxchart),
            "maxPolylineSize": str(maxpoly),
        }
        url = self.get_url(activity_id=activity_id)
        logger.debug(f"Requesting details for {activity_id=}")

        return self.connectapi(url, params=params)

    def get_activity_exercise_sets(self, activity_id):
        """Return activity exercise sets."""

        url = self.get_url(activity_id=str(activity_id))
        logger.debug(f"Requesting exercise sets for {activity_id}")

        return self.connectapi(url)

    def get_activity_gear(self, activity_id):
        """Return gears used for activity id."""

        activity_id = str(activity_id)
        params = {
            "activityId": str(activity_id),
        }
        url = self.garmin_connect_gear
        logger.debug("Requesting gear for activity_id %s", activity_id)

        return self.connectapi(url, params=params)

    def get_gear_activities(self, gear_uuid):
        """Return activities where gear uuid was used."""

        url = self.get_url(gear_uuid=str(gear_uuid))
        logger.debug(f"Requesting activities for {gear_uuid=}")

        return self.connectapi(url)

    def get_user_profile(self):
        """Get all users settings."""

        url = self.get_url()
        logger.debug("Requesting user profile.")

        return self.connectapi(url)

    def request_reload(self, cdate: str):
        """
        Request reload of data for a specific date. This is necessary because
        Garmin offloads older data.
        """

        url = f"{self.garmin_request_reload_url}/{cdate}"
        logger.debug(f"Requesting reload of data for {cdate}.")

        return self.garth.post("connectapi", url, api=True)

    def get_workouts(self, start=0, end=100):
        """Return workouts from start till end."""

        url = f"{self.garmin_workouts}/workouts"
        logger.debug(f"Requesting workouts from {start}-{end}")
        params = {"start": start, "limit": end}
        return self.connectapi(url, params=params)

    def get_workout_by_id(self, workout_id):
        """Return workout by id."""

        url = f"{self.garmin_workouts}/workout/{workout_id}"
        return self.connectapi(url)

    def download_workout(self, workout_id):
        """Download workout by id."""

        url = f"{self.garmin_workouts}/workout/FIT/{workout_id}"
        logger.debug("Downloading workout from %s", url)

        return self.download(url)

    # def upload_workout(self, workout_json: str):
    #     """Upload workout using json data."""

    #     url = f"{self.garmin_workouts}/workout"
    #     logger.debug("Uploading workout using %s", url)

    #     return self.garth.post("connectapi", url, json=workout_json, api=True)
    def get_menstrual_data_for_date(self, for_date: str):
        """Return menstrual data for date."""

        url = self.get_url(for_date=for_date)
        logger.debug(f"Requesting menstrual data for date: {for_date}")

        return self.connectapi(url)

    def get_menstrual_calendar_data(self, start_date: str, end_date: str):
        """Return summaries of cycles that have days between start_date and end_date."""

        url = self.get_url(start_date=start_date, end_date=end_date)
        logger.debug(
            f"Requesting menstrual data for dates {start_date} through {end_date}"
        )

        return self.connectapi(url)

    def get_pregnancy_summary(self):
        """Return snapshot of pregnancy data"""

        url = f"{self.garmin_connect_pregnancy_snapshot_url}"
        logger.debug("Requesting pregnancy snapshot data")

        return self.connectapi(url)

    def logout(self):
        """Log user out of session."""

        logger.error("Deprecated: Alternative is to delete login tokens to logout.")
