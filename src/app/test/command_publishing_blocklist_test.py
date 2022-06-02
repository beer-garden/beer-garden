import pytest
from brewtils.models import Events

from beer_garden.api.http import CommandPublishingBlocklistSchema
from beer_garden.command_publishing_blocklist import handle_event
from beer_garden.db.mongo.models import CommandPublishingBlocklist, Event, Garden

garden_name = "somechildgarden"
system_name = "somesystem"
command_name = "somecommand"


@pytest.fixture
def blocklist():
    blocklist = CommandPublishingBlocklist(
        namespace=garden_name,
        system=system_name,
        command=command_name,
        status="ADD_REQUESTED",
    )
    blocklist.save()

    yield blocklist
    blocklist.delete()


@pytest.fixture
def garden():
    garden = Garden(name=garden_name)
    garden.save()

    yield garden
    garden.delete()


@pytest.fixture
def blocklist_cleanup():
    yield
    CommandPublishingBlocklist.drop_collection()


class TestCommandPublishingBlocklist:
    @pytest.mark.gen_test
    def test_handle_event(self, garden, blocklist, blocklist_cleanup):
        temp_blocked_command = CommandPublishingBlocklist(
            namespace=garden.name,
            system=system_name,
            command="should_get_added",
            status="CONFIRMED",
        )
        temp_blocked_command.save()
        event = Event(
            garden=garden.name,
            name=Events.COMMAND_PUBLISHING_BLOCKLIST_SYNC.name,
            metadata={
                "command_publishing_blocklist": CommandPublishingBlocklistSchema(
                    many=True
                )
                .dump(CommandPublishingBlocklist.objects.all())
                .data
            },
        )
        event.metadata["command_publishing_blocklist"][0]["status"] = "CONFIRMED"
        temp_blocked_command.delete()
        CommandPublishingBlocklist(
            namespace=garden.name,
            system=system_name,
            command="should_get_removed",
            status="REMOVE_REQUESTED",
        ).save()
        handle_event(event)

        blocked_commands = CommandPublishingBlocklist.objects.all().values_list(
            "command", "status"
        )
        assert len(blocked_commands) == 2
        assert ("somecommand", "CONFIRMED") in blocked_commands
        assert ("should_get_added", "CONFIRMED") in blocked_commands
        assert ("should_get_removed", "REMOVE_REQUESTED") not in blocked_commands
