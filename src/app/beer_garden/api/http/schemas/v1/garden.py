from brewtils.schemas import GardenSchema


class GardenReadSchema(GardenSchema):
    """Garden schema for users with read only access. It removes the connection
    paramters, which should be considered sensitive data"""

    class Meta:
        exclude = ["connection_params"]
