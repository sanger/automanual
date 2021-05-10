import pytest

from main import build_xml_document, get_config, past_tense, qc_status, url_for_action


@pytest.fixture
def config():
    return get_config()


def test_get_config(config):
    assert set(config._fields) == set(("ss", "mlwh"))
    assert set(config.ss._fields) == set(("db_host", "db_port", "db_user", "db_password", "db_dbname", "url_host"))
    assert set(config.mlwh._fields) == set(("db_host", "db_port", "db_user", "db_password", "db_dbname"))


def test_qc_status():
    assert qc_status(None) == "pass"
    assert qc_status(1) == "pass"
    assert qc_status(0) == "fail"


def test_past_tense():
    assert past_tense("fail") == "failed"
    assert past_tense("pass") == "passed"


def test_build_xml_document():
    asset_id = "123"
    status = "pass"
    xml_document = build_xml_document(asset_id, status)
    assert "qc_information" in xml_document
    assert "message" in xml_document
    assert f"Asset {asset_id} {past_tense(status)} manual qc" in xml_document


def test_url_for_action(config):
    asset_id = "123"
    status = "pass"
    url = url_for_action(config, asset_id, status)
    assert url == f"http://{config.ss.url_host}/npg_actions/assets/{asset_id}/{status}_qc_state"
