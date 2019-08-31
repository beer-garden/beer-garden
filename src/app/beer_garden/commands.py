from beer_garden.bg_utils.mongo.models import Command


def get_command(command_id):
    return Command.objects.get(id=command_id)


def get_commands():
    return Command.objects.all()
