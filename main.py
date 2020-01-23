import http
import logging
import os
import traceback
import xml.etree.ElementTree as ET
from collections import namedtuple

import mysql.connector
import requests
from apscheduler.schedulers.blocking import BlockingScheduler

FORMAT = '%(asctime)-15s %(name)s:%(lineno)s %(levelname)s:%(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

SS = 'ss'
MLWH = 'mlwh'


def get_config():
    """
    Get the required config parameters
    """
    required_config = (
        'MLWH_DB_HOST', 'MLWH_DB_PORT', 'MLWH_DB_USER', 'MLWH_DB_PASSWORD', 'MLWH_DB_DBNAME',
        'SS_DB_HOST', 'SS_DB_PORT', 'SS_DB_USER', 'SS_DB_PASSWORD', 'SS_DB_DBNAME', 'SS_URL_HOST')

    for config in required_config:
        if not os.getenv(config):
            raise Exception(f'A required config is missing: {config}')

    ss_config_keys = list(filter(lambda x: 'SS_' in x, required_config))
    mlwh_config_keys = list(filter(lambda x: 'MLWH_' in x, required_config))

    Config = namedtuple('Config', [SS, MLWH])

    SsConfig = namedtuple(
        'SsConfig',
        [conf[conf.find('_') + 1:].lower() for conf in ss_config_keys])
    MlwhConfig = namedtuple(
        'MlwhConfig',
        [conf[conf.find('_') + 1:].lower() for conf in mlwh_config_keys])

    ss_dict = {item[item.find('_') + 1:].lower(): os.getenv(item) for item in ss_config_keys}
    mlwh_dict = {item[item.find('_') + 1:].lower(): os.getenv(item) for item in mlwh_config_keys}

    ss_config = SsConfig(**ss_dict)
    mlwh_config = MlwhConfig(**mlwh_dict)

    config = Config(**{SS: ss_config, MLWH: mlwh_config})

    logger.debug(config)

    return config


def connect_to_db(config, db):
    """
    Connects to the given database using the MySQL connector.
    """
    db_config = getattr(config, db)

    connection = mysql.connector.connect(
        user=db_config.db_user,
        password=db_config.db_password,
        host=db_config.db_host,
        port=db_config.db_port,
        database=db_config.db_dbname
    )
    cursor = connection.cursor()

    return connection, cursor


def past_tense(status):
    """Get the past tense of the words pass and fail ONLY
    """
    return status + 'ed'


def qc_status(qc_seq):
    """Simple rule to determine the QC status using the 'qc_seq' field
    """
    if qc_seq in (None, 1):
        return 'pass'

    return 'fail'


def build_xml_document(asset_id, status):
    """Build a XML document used to send with the POST request to SS
    """
    qc_information_tag = ET.Element('qc_information')
    message_tag = ET.SubElement(qc_information_tag, 'message')

    message_tag.text = f'Asset {asset_id} {past_tense(status)} manual qc'

    xml_doc_string = ET.tostring(qc_information_tag,
                                 encoding='unicode',
                                 method='xml',
                                 xml_declaration=True)
    logger.debug(xml_doc_string)

    return xml_doc_string


def url_for_action(config, asset_id, status):
    """Get the URL required for the status update
    """
    url = f'http://{config.ss.url_host}/npg_actions/assets/{asset_id}/{status}_qc_state'

    logger.debug(f'URL: {url}')

    return url


def send_npg_action(config, asset_id, status):
    """Send an HTTP POST request to the SS endpoint provided for NPG
    """
    xml_document = build_xml_document(asset_id, status)
    logger.info(f'Sending {status} for asset {asset_id}')

    headers = {'Content-Type': 'application/xml'}
    url = url_for_action(config, asset_id, status)
    response = requests.post(url, data=xml_document, headers=headers)

    if response.status_code != http.HTTPStatus.OK:
        raise Exception(f'Error while processing {url}')


def get_lanes_info(config):
    """Get the information about the lanes from SS
    """
    lanes_info = []
    connection, cursor = connect_to_db(config, SS)

    with open('ss_script.sql') as f:
        cursor.execute(f.read())

    for (target_asset_id, position, batch_id) in cursor:
        record = {
            'target_asset_id': target_asset_id,
            'position': position,
            'batch_id': batch_id
        }
        lanes_info.append(record)

    logger.info(f'Lanes to process: {len(lanes_info)}')

    cursor.close()
    connection.close()

    return lanes_info


def find_and_complete(config, lanes_info):
    """Find the run in MLWH and send PASS or FAIL to SS
    """
    connection, cursor = connect_to_db(config, MLWH)

    with open('mlwh_script.sql') as f:
        mlwh_query_template = f.read()

    for lane in lanes_info:
        logger.info(f'{"-" * 80}')
        logger.info(f'lane info: {lane}')

        mlwh_query = mlwh_query_template
        for r in (('__BATCH_ID__', str(lane['batch_id'])), ('__POSITION__', str(lane['position']))):
            mlwh_query = mlwh_query.replace(*r)

        cursor.execute(mlwh_query)

        for (id_run, position, qc_seq) in cursor:
            logger.debug(f'id_run: {id_run}, position: {position}, qc_seq: {qc_seq}')
            send_npg_action(config, lane['target_asset_id'], qc_status(qc_seq))

    cursor.close()
    connection.close()


def magic(config):
    try:
        lanes_info = get_lanes_info(config)
        find_and_complete(config, lanes_info)
        logger.info('DONE')
    except (Exception, mysql.connector.Error) as error:
        logging.error(traceback.print_exc())
        logging.error(error)


def main():
    scheduler = BlockingScheduler()
    try:
        config = get_config()
        scheduler.add_job(magic, 'interval', (config, ), hours=12)
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == '__main__':
    main()
