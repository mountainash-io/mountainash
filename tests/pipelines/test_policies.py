from mountainash.pipelines.core.policies import EmptyPolicy, RetryConfig


def test_empty_policy_values():
    assert EmptyPolicy.WARN.value == "warn"
    assert EmptyPolicy.FAIL.value == "fail"
    assert EmptyPolicy.SILENT.value == "silent"


def test_retry_config_defaults():
    rc = RetryConfig()
    assert rc.max_attempts == 3
    assert rc.backoff_rate == 2.0
    assert rc.initial_delay_seconds == 1.0


def test_retry_config_custom():
    rc = RetryConfig(max_attempts=5, backoff_rate=1.5, initial_delay_seconds=0.5)
    assert rc.max_attempts == 5
    assert rc.backoff_rate == 1.5
    assert rc.initial_delay_seconds == 0.5


def test_retry_config_is_frozen():
    rc = RetryConfig()
    try:
        rc.max_attempts = 10
        assert False, "Should raise"
    except AttributeError:
        pass
