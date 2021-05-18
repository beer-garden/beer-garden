import pytest

try:
    from helper import wait_for_response
    from helper.assertion import assert_successful_request, assert_validation_error
except:
    from ...helper import wait_for_response
    from ...helper.assertion import assert_successful_request, assert_validation_error


@pytest.fixture(scope="class")
def system_spec():
    return {"system": "dynamic", "system_version": "3.0.0.dev0", "instance_name": "d1"}


@pytest.mark.usefixtures("easy_client", "request_generator")
class TestDynamic(object):
    def test_say_specific_in_choice(self):
        request = self.request_generator.generate_request(
            command="say_specific", parameters={"message": "a"}
        )
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="a")

    def test_say_specific_not_in_choice(self):
        request = self.request_generator.generate_request(
            command="say_specific", parameters={"message": "NOT_IN_CHOICES"}
        )
        assert_validation_error(
            self, self.easy_client, request, regex="not a valid choice"
        )

    def test_say_specific_from_command_in_choice(self):
        request = self.request_generator.generate_request(
            command="say_specific_from_command", parameters={"message": "a"}
        )
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="a")

    def test_say_specific_from_command_not_in_choice(self):
        request = self.request_generator.generate_request(
            command="say_specific_from_command",
            parameters={"message": "NOT_IN_CHOICES"},
        )
        assert_validation_error(
            self, self.easy_client, request, regex="not a valid choice"
        )

    def test_say_specific_from_command_nullable_message(self):
        request = self.request_generator.generate_request(
            command="say_specific_from_command_nullable", parameters={"message": None}
        )
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="null")

    def test_say_specific_from_command_nullable_not_in_choice(self):
        request = self.request_generator.generate_request(
            command="say_specific_from_command_nullable",
            parameters={"message": "NOT_IN_CHOICES"},
        )
        assert_validation_error(
            self, self.easy_client, request, regex="not a valid choice"
        )

    @pytest.mark.skip("Skipping until we find a URL to demonstrate the capability.")
    def test_say_specific_from_url_good_choice(self):
        request = self.request_generator.generate_request(
            command="say_specific_from_url", parameters={"message": "Kentucky"}
        )
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="Kentucky")

    @pytest.mark.skip("Skipping until we find a URL to demonstrate the capability.")
    def test_say_specific_from_url_bad_choice(self):
        request = self.request_generator.generate_request(
            command="say_specific_from_url", parameters={"message": "NOT_IN_CHOICES"}
        )
        assert_validation_error(
            self, self.easy_client, request, regex="not a valid choice"
        )

    @pytest.mark.skip("Skipping until we find a URL to demonstrate the capability.")
    def test_say_specific_from_url_nullable(self):
        request = self.request_generator.generate_request(
            command="say_specific_from_url_nullable", parameters={"message": None}
        )
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="null")

    def test_say_specific_non_strict_out_of_choice(self):
        request = self.request_generator.generate_request(
            command="say_specific_non_strict_typeahead",
            parameters={"message": "NOT_IN_CHOICE"},
        )
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="NOT_IN_CHOICE")
