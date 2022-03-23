from brewtils.models import Operation

import beer_garden.config as config
from beer_garden.db.mongo.models import CommandPublishingBlockList


def command_publishing_blocklist_add(command: dict):
    """Creates the provided CommandPublishingBlockList by setting its attributes the provided arg.
    The created CommandPublishingBlockList object is then saved to the database and returned.

    Args:
        command: a dict with {namespace: string, command: string, system: string}

    Returns:
        CommandPublishingBlockList: the created CommandPublishingBlockList instance
    """
    import beer_garden.router

    if config.get("garden.name") != command["namespace"]:
        blocked_command = CommandPublishingBlockList(**command)
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
        blocked_command = CommandPublishingBlockList(**command)
        blocked_command.save()
    return blocked_command


def command_publishing_blocklist_save(command):
    """Creates the provided CommandPublishingBlockList by setting its attributes the provided arg.
    The created CommandPublishingBlockList object is then saved to the database.

    Args:
        command: a dict with {namespace: string, command: string, system: string}
    """
    CommandPublishingBlockList(**command).save()


def command_publishing_blocklist_delete(blocked_command: CommandPublishingBlockList):
    """Deletes the provided CommandPublishingBlockList object from database.

    Args:
        blocked_command: a CommandPublishingBlockList object
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
    """Deletes the CommandPublishingBlockList object with corresponding id from database.

    Args:
        command_publishing_id: a string of an id used to get CommandPublishingBlockList object from database
    """
    CommandPublishingBlockList.objects.filter(id=command_publishing_id).delete()
