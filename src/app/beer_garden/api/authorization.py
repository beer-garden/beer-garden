from enum import Enum


class Permissions(Enum):
    """Defines the list of valid permission strings, mostly used for validation
    that the permissions assigned to roles are ones that beer garden recognizes.
    """

    EVENT_FORWARD = "event:forward"

    JOB_CREATE = "job:create"
    JOB_READ = "job:read"
    JOB_UPDATE = "job:update"
    JOB_DELETE = "job:delete"

    GARDEN_CREATE = "garden:create"
    GARDEN_READ = "garden:read"
    GARDEN_UPDATE = "garden:update"
    GARDEN_DELETE = "garden:delete"

    INSTANCE_CREATE = "instance:create"
    INSTANCE_READ = "instance:read"
    INSTANCE_UPDATE = "instance:update"
    INSTANCE_DELETE = "instance:delete"

    QUEUE_CREATE = "queue:create"
    QUEUE_READ = "queue:read"
    QUEUE_UPDATE = "queue:update"
    QUEUE_DELETE = "queue:delete"

    REQUEST_CREATE = "request:create"
    REQUEST_READ = "request:read"
    REQUEST_UPDATE = "request:update"
    REQUEST_DELETE = "request:delete"

    ROLE_CREATE = "role:create"
    ROLE_READ = "role:read"
    ROLE_UPDATE = "role:update"
    ROLE_DELETE = "role:delete"

    SYSTEM_CREATE = "system:create"
    SYSTEM_READ = "system:read"
    SYSTEM_UPDATE = "system:update"
    SYSTEM_DELETE = "system:delete"

    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
