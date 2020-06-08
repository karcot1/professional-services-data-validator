# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Output validation report to BigQuery tables"""


class BigQueryResultHandler(object):
    """Write results of data validation to BigQuery.

    Arguments:
        bigquery_client (google.cloud.bigquery.client.Client):
            BigQuery client for uploading results.
        table_id (str):
            Fully-qualified table ID (``project-id.dataset.table``) of
            destination table for results.
    """

    def __init__(self, bigquery_client):
        self._bigquery_client = bigquery_client

    def execute(self, config, result_df):
        self._bigquery_client.insert_rows_from_dataframe(result_df)

        return result_df