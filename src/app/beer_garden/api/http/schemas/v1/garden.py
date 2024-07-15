from brewtils.schemas import GardenSchema


class GardenReadSchema(GardenSchema):
    """Garden schema for users with read only access. It removes the connection
    paramters, which should be considered sensitive data"""

    class Meta:
        exclude = ["connection_params"]


class GardenRemoveStatusInfoSchema(GardenSchema):
    """Garden schema for users with read only access. It removes the connection
    parameters, which should be considered sensitive data"""

    class Meta:
        exclude = [
            "status_info.history",
            "systems.instances.status_info.history",
            "receiving_connections.status_info.history",
            "publishing_connections.status_info.history",
        ]
