import pytest

from pr_agent.dashboard.actions import parse_repo


def test_repo_form_accepts_owner_and_name():
    assert parse_repo(" eclouddev/hlzs_web ") == ("eclouddev", "hlzs_web")


@pytest.mark.parametrize("value", ["", "owner", "owner/name?x=1", "../repo", "owner/name/extra"])
def test_repo_form_rejects_values_that_could_escape_the_repository(value):
    with pytest.raises(ValueError, match="owner/repo"):
        parse_repo(value)
