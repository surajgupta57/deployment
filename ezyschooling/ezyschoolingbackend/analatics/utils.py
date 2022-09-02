import json
import sys

from django.conf import settings

from .tasks import save_request, click_action_task


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def save_user_actions(request):
    client_ip = get_client_ip(request)

    user = request.user.id if request.user.is_authenticated else None

    is_mobile = request.user_agent.is_mobile
    is_tablet = request.user_agent.is_tablet
    is_touch_capable = request.user_agent.is_touch_capable
    is_pc = request.user_agent.is_pc
    is_bot = request.user_agent.is_bot

    browser_family = request.user_agent.browser.family
    browser_version = request.user_agent.browser.version
    browser_version_string = request.user_agent.browser.version_string

    os_family = request.user_agent.os.family
    os_version = request.user_agent.os.version
    os_version_string = request.user_agent.os.version_string

    device_family = request.user_agent.device.family

    save_request.delay(
        path=request.data.get("path", None),
        client_ip=client_ip,
        user_id=user,
        is_mobile=is_mobile,
        is_tablet=is_tablet,
        is_touch_capable=is_touch_capable,
        is_pc=is_pc,
        is_bot=is_bot,
        browser_family=browser_family,
        browser_version=browser_version,
        browser_version_string=browser_version_string,
        os_family=os_family,
        os_version=os_version,
        os_version_string=os_version_string,
        device_family=device_family,
        object_slug=request.data.get("object_slug", None),
        object_type=request.data.get("object_type", None),
    )


def save_click_actions(request):
    client_ip = get_client_ip(request)

    user = request.user.id if request.user.is_authenticated else None

    is_mobile = request.user_agent.is_mobile
    is_tablet = request.user_agent.is_tablet
    is_touch_capable = request.user_agent.is_touch_capable
    is_pc = request.user_agent.is_pc
    is_bot = request.user_agent.is_bot

    browser_family = request.user_agent.browser.family
    browser_version = request.user_agent.browser.version
    browser_version_string = request.user_agent.browser.version_string

    os_family = request.user_agent.os.family
    os_version = request.user_agent.os.version
    os_version_string = request.user_agent.os.version_string

    device_family = request.user_agent.device.family

    click_action_task.delay(
        path=request.data.get("path", None),
        client_ip=client_ip,
        user_id=user,
        is_mobile=is_mobile,
        is_tablet=is_tablet,
        is_touch_capable=is_touch_capable,
        is_pc=is_pc,
        is_bot=is_bot,
        browser_family=browser_family,
        browser_version=browser_version,
        browser_version_string=browser_version_string,
        os_family=os_family,
        os_version=os_version,
        os_version_string=os_version_string,
        device_family=device_family,
        action_flag=request.data.get("action_flag", None),
        action_message=request.data.get("action_message", None),
        object_type=request.data.get("object_type", None),
        next_page_path=request.data.get("next_page_path", None),
        object_slug=request.data.get("object_slug", None),
        object_id=request.data.get("object_id", None),
    )
