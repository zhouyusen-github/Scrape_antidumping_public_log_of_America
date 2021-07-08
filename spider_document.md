## Scrape public antidumping data of America
Author: Yusen Zhou, Date：2021-07-07

#### source data
From professor

#### website situation
1. search api: https://www.federalregister.gov/documents/search?conditions%5Bterm%5D={DOCNo}&page={page}
2. notice url: https://www.federalregister.gov/documents/2001/11/01/01-27482/certain-pasta-from-italy-and-turkey-extension-of-final-results-of-antidumping-duty-administrative


#### data introduction
1. notice information with antidumping rate

| database_field_name       | json_field_name | meaning              | database_field_type | example | preprocessing | error_return | allow_null |
| ------------------------- | --------------- | -------------------- | ------------------- | ------- | ------------- | ------------ | ---------- |
| CaseID                    |                 | from uuid            | varchar(50)         |         |               |              | 1          |
| ITCNo                     |                 |                      | varchar(50)         |         |               |              | 1          |
| source_DOCNo              |                 | search Docket Number | varchar(50)         |         |               |              | 1          |
| notice_DOCNo              |                 | notice Docket Number | varchar(50)         |         |               |              | 1          |
| Year                      |                 |                      | varchar(50)         |         |               |              | 1          |
| Month                     |                 |                      | varchar(50)         |         |               |              | 1          |
| Date                      |                 |                      | varchar(50)         |         |               |              | 1          |
| ProducerID                |                 |                      | varchar(50)         |         |               |              | 1          |
| Action                    |                 |                      | varchar(50)         |         |               |              | 1          |
| source_AD_CVD             |                 |                      | varchar(50)         |         |               |              | 1          |
| notice_AD_CVD             |                 |                      | varchar(50)         |         |               |              | 1          |
| Product                   |                 |                      | varchar(50)         |         |               |              | 1          |
| source_Country            |                 |                      | varchar(50)         |         |               |              | 1          |
| notice_Country            |                 |                      | varchar(50)         |         |               |              | 1          |
| source                    |                 | notice_url           | varchar(50)         |         |               |              | 1          |
| fed_reg                   |                 |                      | varchar(50)         |         |               |              | 1          |
| Notes                     |                 |                      | varchar(50)         |         |               |              | 1          |
| have_table                |                 |                      | int                 |         |               |              |            |
| Petitioner_and_AltNm_list |                 |                      | varchar(500)        |         |               |              | 1          |
| HS_list                   |                 |                      | varchar(1000)       |         |               |              | 1          |


2. antidumping rate of specific company

| database_field_name | json_field_name | meaning                    | database_field_type | example | preprocessing | error_return | allow_null |
| ------------------- | --------------- | -------------------------- | ------------------- | ------- | ------------- | ------------ | ---------- |
| RateID              |                 | from uuid                  | varchar(50)         |         |               |              | 1          |
| CaseID              |                 |                            | varchar(50)         |         |               |              | 1          |
| Exporter            |                 |                            | varchar(200)        |         |               |              | 1          |
| ExpAltNm            |                 | Exporter abbr              | varchar(50)         |         |               |              | 1          |
| Producer            |                 |                            | varchar(200)        |         |               |              | 1          |
| PdAltNm             |                 | Producer abbr              | varchar(50)         |         |               |              | 1          |
| CashDeposit         |                 |                            | varchar(50)         |         |               |              | 1          |
| DumpingMargin       |                 |                            | varchar(50)         |         |               |              | 1          |
| SubsidyRate         |                 |                            | varchar(50)         |         |               |              | 1          |
| AD_CVD              |                 | AD_CVD of table not notice | varchar(50)         |         |               |              | 1          |

