from brewtils.models import Event, Events, Operation
from mongoengine import DoesNotExist

import beer_garden.config as config
from beer_garden.db.mongo.models import CommandPublishingBlocklist
from beer_garden.events import publish


def command_publishing_blocklist_add(command: dict):
    """Creates the provided CommandPublishingBlocklist by setting its attributes to the provided arg.
    The created CommandPublishingBlocklist object is then saved to the database and returned.

    Args:
        command: a dict with {namespace: string, command: string, system: string}

    Returns:
        CommandPublishingBlocklist: the created CommandPublishingBlocklist instance
    """
    import beer_garden.router

    if config.get("garden.name") != command["namespace"]:
        blocked_command = CommandPublishingBlocklist(**command)
        blocked_command.save()
        command["id"] = str(blocked_command.id)
        beer_garden.router.route(
            Operation(
                operation_type="COMMAND_BLOCKLIST_ADD",
                kwargs={"command": command},
                target_garden_name=command["namespace"],
            )
        )
        blocked_command.status = "ADD_REQUESTED"
        blocked_command.save()
    else:
        blocked_command = CommandPublishingBlocklist(**command)
        blocked_command.status = "CONFIRMED"
        blocked_command.save()
    return blocked_command


def command_publishing_blocklist_save(command: dict):
    """Creates the provided CommandPublishingBlocklist by setting its attributes to the provided arg.
    The created CommandPublishingBlocklist object is then saved to the database.

    Args:
        command: a dict with {namespace: string, command: string, system: string}
    """
    blocked_command = CommandPublishingBlocklist(**command)
    blocked_command.status = "CONFIRMED"
    blocked_command.save()


def command_publishing_blocklist_delete(blocked_command: CommandPublishingBlocklist):
    """Deletes the provided CommandPublishingBlocklist object from database.

    Args:
        blocked_command: a CommandPublishingBlocklist object
    """
    if config.get("garden.name") != blocked_command.namespace:
        import beer_garden.router

        beer_garden.router.route(
            Operation(
                operation_type="COMMAND_BLOCKLIST_REMOVE",
                args=[blocked_command.id],
                target_garden_name=blocked_command.namespace,
            )
        )
        blocked_command.status = "REMOVE_REQUESTED"
        blocked_command.save()
    else:
        blocked_command.delete()


def command_publishing_blocklist_remove(command_publishing_id: str):
    """Deletes the CommandPublishingBlocklist object with corresponding id from database.

    Args:
        command_publishing_id: a string of an id used to get CommandPublishingBlocklist object from database
    """
    CommandPublishingBlocklist.objects.filter(id=command_publishing_id).delete()


def handle_event(event):
    """Handles COMMAND_PUBLISHING_BLOCKLIST_SYNC events"""
    if (event.name == Events.COMMAND_PUBLISHING_BLOCKLIST_SYNC.name) and (
        event.garden != config.get("garden.name")
    ):
        list_of_ids = []
        for blocked_command in event.metadata["command_publishing_blocklist"]:
            list_of_ids.append(blocked_command["id"])
            try:
                local_blocked_command = CommandPublishingBlocklist.objects.get(
                    namespace=blocked_command["namespace"],
                    system=blocked_command["system"],
                    command=blocked_command["command"],
                )

                if f"{local_blocked_command.id}" != blocked_command["id"]:
                    local_blocked_command.delete()
                    local_blocked_command = CommandPublishingBlocklist(
                        **blocked_command
                    )
                else:
                    local_blocked_command.status = blocked_command["status"]
                local_blocked_command.save()
            except DoesNotExist:
                CommandPublishingBlocklist(**blocked_command).save()
        CommandPublishingBlocklist.objects.filter(
            namespace=event.garden, id__nin=list_of_ids
        ).delete()


def publish_command_publishing_blocklist():
    """Publishes COMMAND_PUBLISHING_BLOCKLIST_SYNC event to sync the parent's
    CommandPublishingBlocklist with the child's CommandPublishingBlocklist
    """
    from beer_garden.api.http import CommandPublishingBlocklistSchema

    publish(
        Event(
            garden=config.get("garden.name"),
            name=Events.COMMAND_PUBLISHING_BLOCKLIST_SYNC.name,
            metadata={
                "command_publishing_blocklist": CommandPublishingBlocklistSchema(
                    many=True
                )
                .dump(CommandPublishingBlocklist.objects.all())
                .data
            },
        )
    )
