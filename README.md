TikTok Ads Extractor
=============

TikTok is a video-sharing focused social networking service.

This component enables users to extract integrated TikTok Ad reports into Keboola

**Table of contents:**

[TOC]


Configuration
=============

## Row Configuration
 - Advertiser ID (advertiser_id) - [REQ] Specifies ad account for which the report will be downloaded. Multiple ad accounts should be input as a comma separated list. If left empty all ad accounts will be downloaded.
 - Report Settings (report_settings) - [REQ] report settings is a dictionary containing the following items:
   - Report type (report_type) - [REQ] Select one of the available report types described in the <a href=https://ads.tiktok.com/gateway/docs/index?identify_key=2b9b4278e47b275f36e7c39a4af4ba067d088e031d5f5fe45d381559ac89ba48&language=ENGLISH&doc_id=1701890951192578'>documentation</a>
   - Service type (service_type) - [REQ] Select one of the service types described in the <a href='https://ads.tiktok.com/marketing_api/docs?id=1740302848100353'>documentation</a>
   - Data Level (data_level) - [OPT] Select one of the data level types described in the <a href='https://ads.tiktok.com/marketing_api/docs?id=1740302848100353'>documentation</a>. Use NOT_DEFINED if you do not need the data level, e.g. with the report type PLAYABLE_MATERIAL
   - Dimensions (dimensions) - [REQ] Comma separated list of dimensions to use for the report, find supported dimensions for specific report types in the <a href='https://ads.tiktok.com/marketing_api/docs?id=1738864835805186'>documentation</a>
   - Metrics (metrics) - [REQ] Comma separated list of metrics to use for the report, find supported metrics for specific report types in the <a href='https://ads.tiktok.com/marketing_api/docs?id=1738864835805186'>documentation</a>
   - Date From (date_from) - [REQ] Start date of the report. Either date in YYYY-MM-DD format or dateparser string i.e. 5 days ago, 1 month ago, yesterday, etc.
   - Date to (date_to) - [REQ] End date of the report. Either date in YYYY-MM-DD format or dateparser string i.e. 5 days ago, 1 month ago, yesterday, etc.
 - Destination (destination) - [REQ] destination is a dictionary containing the following items:
   - Storage Table Name (output_table_name) - [REQ] Name of the table stored in Storage.
   - Incremental Load (incremental) - [REQ] If incremental load is turned on, the table will be updated instead of rewritten. Tables with a primary key will have rows updated, tables without a primary key will have rows appended.


Sample Configuration
=============
```json
{
    "parameters": {
        "#access_token": "SECRET_VALUE",
        "destination": {
            "incremental": true,
            "output_table_name": "basic report"
        },
        "advertiser_id": "",
        "report_settings": {
            "data_level": "AUCTION_CAMPAIGN",
            "metrics": "spend,cpc,cpm,impressions,clicks,ctr,reach,cost_per_1000_reached,conversion,cost_per_conversion,conversion_rate,real_time_conversion,real_time_cost_per_conversion,real_time_conversion_rate,result,cost_per_result,result_rate,real_time_result,real_time_cost_per_result,real_time_result_rate,secondary_goal_result,cost_per_secondary_goal_result,secondary_goal_result_rate",
            "date_from": "2 weeks ago",
            "date_to": "now",
            "dimensions": "campaign_id, stat_time_day",
            "report_type": "BASIC",
            "service_type": "AUCTION"
        }
    },
    "action": "run",
    "authorization": {
        "oauth_api": {
            "id": "OAUTH_API_ID",
            "credentials": {
                "id": "main",
                "authorizedFor": "Myself",
                "creator": {
                    "id": "1234",
                    "description": "me@keboola.com"
                },
                "created": "2016-01-31 00:13:30",
                "#data": "{\"data\": {\"access_token\" : \"SECRET_VALUE\",\"advertiser_ids\":[SECRET_VALUE]}}",
                "oauthVersion": "2.0",
                "appKey": "SECRET_VALUE",
                "#appSecret": "SECRET_VALUE"
            }
        }
    }
}
```


Development
-----------

If required, change local data folder (the `CUSTOM_FOLDER` placeholder) path to your custom path in
the `docker-compose.yml` file:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    volumes:
      - ./:/code
      - ./CUSTOM_FOLDER:/data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Clone this repository, init the workspace and run the component with following command:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
docker-compose build
docker-compose run --rm dev
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run the test suite and lint check using this command:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
docker-compose run --rm test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Integration
===========

For information about deployment and integration with KBC, please refer to the
[deployment section of developers documentation](https://developers.keboola.com/extend/component/deployment/)