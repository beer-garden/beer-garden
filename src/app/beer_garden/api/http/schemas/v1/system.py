from brewtils.schemas import SystemSchema as BrewtilsSystemSchema


class SystemSansQueueSchema(BrewtilsSystemSchema):
    class Meta:
        exclude = ("instances.queue_type", "instances.queue_info")
