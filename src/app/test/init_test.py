from mock import Mock, call

import beer_garden


class TestProgressiveBackoff(object):
    def test_increments(self):
        beer_garden.logger = Mock()
        stop_mock = Mock(stopped=Mock(return_value=False))
        func_mock = Mock(side_effect=[False, False, False, True])

        beer_garden.progressive_backoff(func_mock, stop_mock, "test_func")
        stop_mock.wait.assert_has_calls([call(0.1), call(0.2), call(0.4)])

    def test_max_timeout(self):
        beer_garden.logger = Mock()
        stop_mock = Mock(stopped=Mock(return_value=False))

        side_effect = [False] * 15
        side_effect[-1] = True
        func_mock = Mock(side_effect=side_effect)

        beer_garden.progressive_backoff(func_mock, stop_mock, "test_func")
        max_val = max([mock_call[0][0] for mock_call in stop_mock.wait.call_args_list])
        assert max_val == 30
