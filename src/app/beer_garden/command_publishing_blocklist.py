from beer_garden.db.mongo.models import CommandPublishingBlockList


def command_publishing_block_list_adds(command):
    blocked_command = CommandPublishingBlockList(**command)
    blocked_command.save()
    return blocked_command


def command_publishing_block_list_remove(command_publishing_id):
    blocked_command = CommandPublishingBlockList.objects.get(id=command_publishing_id)
    blocked_command.delete()


def command_publishing_block_list_get():
    response = {"command_publishing_block_list": []}
    command_block_list = CommandPublishingBlockList.objects.all()
    for data in command_block_list:
        data = data._data
        data["id"] = data["id"].__str__()
        response["command_publishing_block_list"].append(data)
    return response
