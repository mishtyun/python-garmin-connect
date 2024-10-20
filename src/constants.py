from typing import Literal

__all__ = ["API_URLS", "ACTIVITY_VISIBILITIES"]


ACTIVITY_VISIBILITIES = Literal["public"]

API_URLS = {
    "login": "/userprofile-service/userprofile/user-settings",
    "get_user_profile": "/userprofile-service/userprofile/user-settings",
    "get_devices": "/device-service/deviceregistration/devices",
    "get_device_settings": "/device-service/deviceservice/device-info/settings/{device_id}",
    "get_device_last_used": "/device-service/deviceservice/mylastused",
    "get_primary_training_device": "/web-gateway/device-info/primary-training-device",
    "get_device_solar_data": "/web-gateway/solar/{device_id}/{startdate}/{enddate}",
    "get_body_composition": "/weight-service/weight/dateRange",
    "add_weigh_in": "/weight-service/user-weight",
    "get_weigh_ins": "/weight-service/user-weight/weight/range/{startdate}/{enddate}",
    "get_daily_weigh_ins": "/weight-service/user-weight/weight/dayview/{cdate}",
    "delete_weigh_in": "/weight-service/user-weight/weight/{cdate}/byversion/{weight_pk}",
    "get_user_summary": "/usersummary-service/usersummary/daily/{display_name}",
    "get_max_metrics": "/metrics-service/metrics/maxmet/daily/{cdate}/{cdate}",
    "get_hydration_data": "/usersummary-service/usersummary/hydration/daily/{cdate}",
    "add_hydration_data": "usersummary-service/usersummary/hydration/log",
    "get_daily_steps": "/usersummary-service/stats/steps/daily/{start}/{end}",
    "get_personal_record": "/personalrecord-service/personalrecord/prs/{display_name}",
    #     ------
    "get_earned_badges": "/badge-service/badge/earned",
    "get_adhoc_challenges": "/adhocchallenge-service/adHocChallenge/historical",
    "get_badge_challenges": "/badgechallenge-service/badgeChallenge/completed",
    "get_available_badge_challenges": "/badgechallenge-service/badgeChallenge/available",
    "get_non_completed_badge_challenges": "/badgechallenge-service/badgeChallenge/non-completed",
    "get_inprogress_virtual_challenges": "/badgechallenge-service/virtualChallenge/inProgress",
    # Activity urls
    "get_activities": "/activitylist-service/activities/search/activities",
    "get_activities_by_date": "/activitylist-service/activities/search/activities",
    "get_gear_activities": "/activitylist-service/activities/{gear_uuid}/gear?start=0&limit=9999",
    "set_activity_name": "/activity-service/activity/{activity_id}",
    "change_activity_visibility": "/activity-service/activity/{activity_id}",
    "get_activity_splits": "/activity-service/activity/{activity_id}/splits",
    "get_activity_typed_splits": "/activity-service/activity/{activity_id}/typedsplits",
    "get_activity_split_summaries": "/activity-service/activity/{activity_id}/split_summaries",
    "get_activity_weather": "/activity-service/activity/{activity_id}/weather",
    "get_activity_hr_in_timezones": "/activity-service/activity/{activity_id}/hrTimeInZones",
    "get_activity": "/activity-service/activity/{activity_id}",
    "get_activity_details": "/activity-service/activity/{activity_id}/details",
    "get_activity_exercise_sets": "/activity-service/activity/{activity_id}/exerciseSets",
    "get_activity_types": "/activity-service/activity/activityTypes",
    "upload_activity": "/upload-service/upload",
}
