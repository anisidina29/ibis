# Copyright 2014 Cloudera Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ibis.config as cf

cf.register_option('interactive', False, validator=cf.is_bool)
cf.register_option('verbose', False, validator=cf.is_bool)


def to_stdout(x):
    print(x)


cf.register_option('verbose_log', to_stdout)


sql_default_limit_doc = """
Number of rows to be retrieved for an unlimited table expression
"""


with cf.config_prefix('sql'):
    cf.register_option('default_limit', 10000, sql_default_limit_doc)
