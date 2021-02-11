from enum import Enum
import logging

from brewtils.models import Operation

logger = logging.getLogger(__name__)


class Permissions(Enum):
    """Admin permissions are required to execute anything within the Admin drop-down in
    regards to Systems and Gardens. Local Admins can manage user roles  and permissions.
    """

    READ = 1
    OPERATOR = 2
    ADMIN = 3
    LOCAL_ADMIN = 4


PermissionRequiredAccess = {
    Permissions.READ: ["ADMIN", "OPERATOR", "READ"],
    Permissions.OPERATOR: ["ADMIN", "OPERATOR"],
    Permissions.ADMIN: ["ADMIN"],
    Permissions.LOCAL_ADMIN: ["ADMIN"],
}

Permissions.values = {p.value for p in Permissions}

route_accesses = {
    "REQUEST_CREATE": Permissions.OPERATOR,
    "REQUEST_START": Permissions.OPERATOR,
    "REQUEST_COMPLETE": Permissions.OPERATOR,
    "REQUEST_READ": Permissions.READ,
    "REQUEST_READ_ALL": Permissions.READ,
    "REQUEST_COUNT": Permissions.READ,
    "COMMAND_READ": Permissions.READ,
    "COMMAND_READ_ALL": Permissions.READ,
    "INSTANCE_READ": Permissions.READ,
    "INSTANCE_DELETE": Permissions.ADMIN,
    "INSTANCE_UPDATE": Permissions.OPERATOR,
    "INSTANCE_HEARTBEAT": Permissions.OPERATOR,
    "INSTANCE_INITIALIZE": Permissions.OPERATOR,
    "INSTANCE_START": Permissions.ADMIN,
    "INSTANCE_STOP": Permissions.ADMIN,
    "INSTANCE_LOGS": Permissions.ADMIN,
    "JOB_CREATE": Permissions.OPERATOR,
    "JOB_READ": Permissions.READ,
    "JOB_READ_ALL": Permissions.READ,
    "JOB_PAUSE": Permissions.OPERATOR,
    "JOB_RESUME": Permissions.OPERATOR,
    "JOB_DELETE": Permissions.OPERATOR,
    "SYSTEM_CREATE": Permissions.OPERATOR,
    "SYSTEM_READ": Permissions.READ,
    "SYSTEM_READ_ALL": Permissions.READ,
    "SYSTEM_UPDATE": Permissions.OPERATOR,
    "SYSTEM_RELOAD": Permissions.ADMIN,
    "SYSTEM_RESCAN": Permissions.ADMIN,
    "SYSTEM_DELETE": Permissions.ADMIN,
    "GARDEN_CREATE": Permissions.ADMIN,
    "GARDEN_READ": Permissions.READ,
    "GARDEN_READ_ALL": Permissions.READ,
    "GARDEN_UPDATE_STATUS": Permissions.ADMIN,
    "GARDEN_UPDATE_CONFIG": Permissions.ADMIN,
    "GARDEN_DELETE": Permissions.ADMIN,
    "GARDEN_SYNC": Permissions.ADMIN,
    "PLUGIN_LOG_READ": Permissions.OPERATOR,
    "PLUGIN_LOG_READ_LEGACY": Permissions.OPERATOR,
    "PLUGIN_LOG_RELOAD": Permissions.OPERATOR,
    "QUEUE_READ": Permissions.READ,
    "QUEUE_DELETE": Permissions.ADMIN,
    "QUEUE_DELETE_ALL": Permissions.ADMIN,
    "QUEUE_READ_INSTANCE": Permissions.READ,
    "NAMESPACE_READ_ALL": Permissions.READ,
    "FILE_CREATE": Permissions.OPERATOR,
    "FILE_CHUNK": Permissions.OPERATOR,
    "FILE_FETCH": Permissions.READ,
    "FILE_DELETE": Permissions.OPERATOR,
    "FILE_OWNER": Permissions.OPERATOR,
    "RUNNER_READ": Permissions.READ,
    "RUNNER_READ_ALL": Permissions.READ,
    "RUNNER_START": Permissions.ADMIN,
    "RUNNER_STOP": Permissions.ADMIN,
    "RUNNER_DELETE": Permissions.ADMIN,
    "RUNNER_RELOAD": Permissions.ADMIN,
    "RUNNER_RESCAN": Permissions.ADMIN,
    "PUBLISH_EVENT": Permissions.OPERATOR,
    "ROLE_READ_ALL": Permissions.READ,
    "ROLE_READ": Permissions.READ,
    "ROLE_DELETE": Permissions.LOCAL_ADMIN,
    "ROLE_UPDATE_PERMISSION": Permissions.LOCAL_ADMIN,
    "ROLE_REMOVE_PERMISSION": Permissions.LOCAL_ADMIN,
    "ROLE_UPDATE_DESCRIPTION": Permissions.LOCAL_ADMIN,
    "ROLE_CREATE": Permissions.LOCAL_ADMIN,
    "USER_READ_ALL": Permissions.LOCAL_ADMIN,
    "USER_READ": Permissions.ADMIN,
    "USER_DELETE": Permissions.LOCAL_ADMIN,
    "USER_UPDATE_ROLE": Permissions.LOCAL_ADMIN,
    "USER_REMOVE_ROLE": Permissions.LOCAL_ADMIN,
    "USER_CREATE": Permissions.LOCAL_ADMIN,
    "USER_UPDATE": Permissions.LOCAL_ADMIN,
}


def determine_permission(operation: Operation):
    if operation.operation_type in route_accesses.keys():
        return route_accesses[operation.operation_type]

    logger.error(f"Unable to map {operation.operation_type} to access level")

    return None
