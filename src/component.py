import csv
import string
import logging
import dateparser
import warnings
import datetime
import re
import os
from typing import Tuple, List, Dict
from tiktok import TikTokClient, TikTokClientException
from keboola.utils.helpers import comma_separated_values_to_list

from keboola.component.base import ComponentBase
from keboola.component.exceptions import UserException
from keboola.component.dao import TableDefinition

KEY_ACCESS_TOKEN = "#access_token"

KEY_ADVERTISER_ID = "advertiser_id"

KEY_REPORT_SETTINGS = "report_settings"
KEY_REPORT_SETTINGS_DATE_FROM = "date_from"
KEY_REPORT_SETTINGS_DATE_TO = "date_to"
KEY_REPORT_SETTINGS_METRICS = "metrics"
KEY_REPORT_SETTINGS_DIMENSIONS = "dimensions"
KEY_REPORT_SETTINGS_REPORT_TYPE = "report_type"
KEY_REPORT_SETTINGS_SERVICE_TYPE = "service_type"
KEY_REPORT_SETTINGS_DATA_LEVEL = "data_level"

KEY_REPORT_SETTINGS_FILTER = "filters"

KEY_DESTINATION = "destination"
KEY_DESTINATION_INCREMENTAL = "incremental"
KEY_DESTINATION_OUTPUT_TABLE_NAME = "output_table_name"

REQUIRED_PARAMETERS = [KEY_REPORT_SETTINGS, KEY_DESTINATION]
REQUIRED_REPORT_SETTINGS_PARAMETERS = [KEY_REPORT_SETTINGS_DATE_FROM, KEY_REPORT_SETTINGS_DATE_TO,
                                       KEY_REPORT_SETTINGS_DIMENSIONS, KEY_REPORT_SETTINGS_REPORT_TYPE,
                                       KEY_REPORT_SETTINGS_SERVICE_TYPE, KEY_REPORT_SETTINGS_METRICS]
REQUIRED_DESTINATION_PARAMETERS = [KEY_DESTINATION_INCREMENTAL, KEY_DESTINATION_OUTPUT_TABLE_NAME]
REQUIRED_IMAGE_PARS = []

KEY_DATE_FORMAT = "%Y-%m-%d"

warnings.filterwarnings(
    "ignore",
    message="The localize method is no longer necessary, as this time zone supports the fold attribute",
)


class Component(ComponentBase):

    def __init__(self):
        super().__init__()

    def run(self):
        self.validate_configuration_parameters(REQUIRED_PARAMETERS)
        self.validate_image_parameters(REQUIRED_IMAGE_PARS)

        self._validate_parameters(self.configuration.parameters.get(KEY_REPORT_SETTINGS),
                                  REQUIRED_REPORT_SETTINGS_PARAMETERS, 'config parameters')
        self._validate_parameters(self.configuration.parameters.get(KEY_DESTINATION),
                                  REQUIRED_DESTINATION_PARAMETERS, 'config parameters')
        self._add_last_run_to_state()

        params = self.configuration.parameters

        access_token = params.get(KEY_ACCESS_TOKEN)
        if not access_token:
            access_token = self._get_access_token()

        tiktok_client = TikTokClient(access_token, sandbox=False)

        destination = params.get(KEY_DESTINATION)
        destination_incremental = destination.get(KEY_DESTINATION_INCREMENTAL)
        outfile_name = self._normalize_table_name(destination.get(KEY_DESTINATION_OUTPUT_TABLE_NAME))

        columns, primary_keys = self._get_columns_and_keys()

        if destination_incremental and not ("stat_time_day" in columns or "stat_time_hour" in columns):
            logging.warning("You are using incremental mode, but are not using any dimension for time/date, "
                            "therefore you are overwriting data in the source."
                            " And you will not know the range of the data. We encourage you to use stat_time_day "
                            "in the dimensions if possible")

        table = self.create_out_table_definition(outfile_name,
                                                 columns=columns,
                                                 primary_key=primary_keys,
                                                 incremental=destination_incremental,
                                                 is_sliced=True)
        self.create_sliced_file(table.full_path)

        self._fetch_and_save_all_report_data(tiktok_client, table)
        self.write_manifest(table)

    def _fetch_and_save_all_report_data(self, tiktok_client: TikTokClient, table: TableDefinition) -> None:
        params = self.configuration.parameters
        advertiser_ids = self._get_advertiser_ids()
        report_settings = params.get(KEY_REPORT_SETTINGS)
        filters = report_settings.get(KEY_REPORT_SETTINGS_FILTER)
        report_type = report_settings.get(KEY_REPORT_SETTINGS_REPORT_TYPE)
        service_type = report_settings.get(KEY_REPORT_SETTINGS_SERVICE_TYPE)
        data_level = report_settings.get(KEY_REPORT_SETTINGS_DATA_LEVEL)

        date_from, date_to = self._get_report_date_range()

        metrics = comma_separated_values_to_list(report_settings.get(KEY_REPORT_SETTINGS_METRICS))
        dimensions = comma_separated_values_to_list(report_settings.get(KEY_REPORT_SETTINGS_DIMENSIONS))

        logging.info(f"Fetching Data for Advertisers : {advertiser_ids}")

        for advertiser_id in advertiser_ids:
            logging.info(f"Fetching Data for Advertiser : {advertiser_id}")
            self._fetch_and_save_report_data(tiktok_client, table, str(advertiser_id), report_type, dimensions,
                                             date_from, date_to, filters, service_type, data_level, metrics)

    @staticmethod
    def _fetch_and_save_report_data(tiktok_client: TikTokClient, table: TableDefinition, advertiser_id: str,
                                    report_type: str, dimensions: List[str], date_from: str,
                                    date_to: str, filters: List[Dict], service_type: str, data_level: str,
                                    metrics: List[str]) -> None:

        with open(f"{table.full_path}/{advertiser_id}.csv", 'w') as f:
            dict_writer = csv.DictWriter(f, fieldnames=table.columns)
            try:
                for i, page in enumerate(tiktok_client.get_integrated_report(advertiser_id,
                                                                             report_type,
                                                                             dimensions,
                                                                             date_from,
                                                                             date_to,
                                                                             filters=filters,
                                                                             service_type=service_type,
                                                                             data_level=data_level,
                                                                             metrics=metrics)):
                    if i % 100 == 0:
                        logging.info(f"Fetching page {i} for advertiser {advertiser_id}")
                    for datum in page:
                        dict_writer.writerow({**datum["dimensions"],
                                              **datum["metrics"],
                                              **{"ex_advertiser_id": advertiser_id}})
            except TikTokClientException as tiktok_exc:
                raise UserException(tiktok_exc) from tiktok_exc

    def _get_columns_and_keys(self) -> Tuple[List[str], List[str]]:
        params = self.configuration.parameters
        report_settings = params.get(KEY_REPORT_SETTINGS)
        metrics = comma_separated_values_to_list(report_settings.get(KEY_REPORT_SETTINGS_METRICS))
        dimensions = comma_separated_values_to_list(report_settings.get(KEY_REPORT_SETTINGS_DIMENSIONS))
        columns = ["ex_advertiser_id"] + dimensions + metrics
        primary_key = ["ex_advertiser_id"] + dimensions
        return columns, primary_key

    def _get_access_token(self) -> str:
        try:
            return self.configuration.oauth_credentials["data"]['data']["access_token"]
        except (KeyError, TypeError) as err:
            raise UserException("Configuration is improperly authorized, "
                                "could not get access token from OAuth Credentials. Response from TikTok : "
                                f"{self.configuration.oauth_credentials['data']['data'].get('message')}") from err

    def _get_advertiser_ids(self) -> List[str]:
        params = self.configuration.parameters
        advertiser_ids = comma_separated_values_to_list(params.get(KEY_ADVERTISER_ID, ""))
        if not advertiser_ids:
            try:
                return self.configuration.oauth_credentials["data"]["data"]["advertiser_ids"]
            except (KeyError, TypeError) as err:
                raise UserException(
                    f"Configuration is improperly authorized, could not get advertiser ids from OAuth Credentials."
                    " Response from TikTok : "
                    f"{self.configuration.oauth_credentials['data']['data'].get('message')}") from err
        if not advertiser_ids:
            advertiser_ids = []
        return advertiser_ids

    @staticmethod
    def _normalize_table_name(user_defined_name: str) -> str:
        permitted_chars = string.digits + string.ascii_letters + '_' + "-"
        user_defined_name = user_defined_name.replace(".csv", "")
        cleaned_name = re.sub(f"[^{permitted_chars}]", "", user_defined_name)
        return f"{cleaned_name}.csv"

    def _get_report_date_range(self) -> Tuple[str, str]:

        params = self.configuration.parameters
        report_settings = params.get(KEY_REPORT_SETTINGS)
        date_from_str = report_settings.get(KEY_REPORT_SETTINGS_DATE_FROM)
        date_to_str = report_settings.get(KEY_REPORT_SETTINGS_DATE_TO)

        date_from = self._parse_date(date_from_str)
        date_to = self._parse_date(date_to_str)
        return date_from, date_to

    def _parse_date(self, date_to_parse: str) -> str:
        if date_to_parse.lower() in {"last", "lastrun", "last run"}:
            state = self.get_state_file()
            return state.get("last_run", "1997-01-01")
        try:
            parsed_date = dateparser.parse(date_to_parse).date().strftime(KEY_DATE_FORMAT)
        except (AttributeError, TypeError) as err:
            raise UserException(f"Failed to parse date {date_to_parse}") from err
        return parsed_date

    def _add_last_run_to_state(self) -> None:
        state = self.get_state_file()
        state["last_run"] = datetime.date.today().strftime(KEY_DATE_FORMAT)
        self.write_state_file(state)

    @staticmethod
    def create_sliced_file(outfile_name):
        if not os.path.exists(outfile_name):
            os.makedirs(outfile_name)


if __name__ == "__main__":
    try:
        comp = Component()
        comp.execute_action()
    except UserException as exc:
        logging.exception(exc)
        exit(1)
    except Exception as exc:
        logging.exception(exc)
        exit(2)
