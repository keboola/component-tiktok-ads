from typing import List, Generator, Dict
from keboola.http_client import HttpClient

SANDBOX_URL = "https://sandbox-ads.tiktok.com/open_api/"
PRODUCTION_URL = "https://business-api.tiktok.com/open_api/"
DEFAULT_API_VERSION = "v1.3/"
INTEGRATED_REPORTS_ENDPOINT = "report/integrated/get"

OK_MESSAGE = "OK"


class TikTokClientException(Exception):
    pass


class TikTokClient(HttpClient):
    def __init__(self, access_token, sandbox=False):
        base_url = "".join([PRODUCTION_URL, DEFAULT_API_VERSION])
        if sandbox:
            base_url = "".join([SANDBOX_URL, DEFAULT_API_VERSION])

        auth_header = {"Access-Token": access_token, 'Content-Type': 'application/json'}

        super().__init__(base_url, auth_header=auth_header)

    def get_integrated_report(self, advertiser_id: str, report_type: str, dimensions: List[str], date_from: str,
                              date_to: str, filters: List[Dict] = None, service_type: str = None,
                              data_level: str = None, metrics: List[str] = None) -> Generator:
        params = {"advertiser_id": advertiser_id,
                  "report_type": report_type,
                  "start_date": date_from,
                  "end_date": date_to,
                  "dimensions": self._get_string_of_list(dimensions)}

        if data_level and data_level != "NOT_DEFINED":
            params["data_level"] = data_level
        if metrics:
            params["metrics"] = self._get_string_of_list(metrics)
        if filters:
            params["filtering"] = filters
        if service_type:
            params["service_type"] = service_type
        return self._paginate(params)

    def _paginate(self, params: Dict) -> Generator:
        report_data: Dict = self.get(endpoint_path=INTEGRATED_REPORTS_ENDPOINT, params=params)  # noqa
        if report_data.get("message") != OK_MESSAGE:
            raise TikTokClientException(report_data.get("message"))
        page_info = report_data.get("data").get("page_info")
        total_pages = page_info.get("total_page")
        yield report_data.get("data").get("list")
        for page_num in range(2, total_pages + 1):
            params["page"] = page_num
            report_data: Dict = self.get(endpoint_path=INTEGRATED_REPORTS_ENDPOINT, params=params)  # noqa
            if report_data.get("message") != OK_MESSAGE:
                raise TikTokClientException(report_data.get("message"))
            yield report_data.get("data").get("list")

    @staticmethod
    def _get_string_of_list(list_to_convert: List[str]) -> str:
        quoted_word_list = ",".join(f"\"{word}\"" for word in list_to_convert)
        return f"[{quoted_word_list}]"
