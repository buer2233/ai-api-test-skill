# -*- coding: utf-8 -*-
# Author: dengwanpeng

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.scan_page_api import _parse_file
from skill_utils.api_path_match import api_path_matches


def _write_sample(tmp_path, text):
    sample = tmp_path / "sample_api.py"
    sample.write_text(text, encoding="utf-8")
    return str(sample)


def test_scan_single_quote_format_and_metadata(tmp_path):
    path = _write_sample(tmp_path, '''
class EsbApi:
    def action_getLightActionFLowList(self, ETEAMSID, **kwargs):
        """
        esb中心-动作流-新建动作流-根据模块id获取动作流模板
        :param ETEAMSID:
        :return:
        """
        # Author: liuxin
        # Create Date: 2025-08-13
        url = 'https://{0}/api/bs/esb/setting/flow/design/getLightActionFLowList'.format(self.base_url)
        response = requests.request("GET", url)
        return response.json()
''')

    records = _parse_file(path)

    assert len(records) == 1
    assert records[0]["pure_path"] == "/api/bs/esb/setting/flow/design/getLightActionFLowList"
    assert records[0]["api_desc"] == "esb中心-动作流-新建动作流-根据模块id获取动作流模板"
    assert records[0]["author"] == "liuxin"
    assert records[0]["create_date"] == "2025-08-13"
    assert records[0]["http_method"] == "GET"


def test_scan_f_string_post_and_desc_prefix(tmp_path):
    path = _write_sample(tmp_path, '''
class DwApi:
    def getDatasetAndDataGroupsByGroupIdAndPage_dataDevelopmentGroup(self, ETEAMSID):
        """
        desc: 数据开发-查询所有数据开发数据集 以及文件夹-不分页
        entrace: 数据开发->分组点击查询
        """
        # Author: qiumingwu
        # Create Date: 2023-09-19
        url = f'https://{self.base_url}/api/dw/dataDevelopmentGroup/getDatasetAndDataGroupsByGroupIdAndPage'
        response = requests.request("POST", url)
        return response.json()
''')

    records = _parse_file(path)

    assert records[0]["pure_path"] == "/api/dw/dataDevelopmentGroup/getDatasetAndDataGroupsByGroupIdAndPage"
    assert records[0]["api_desc"] == "数据开发-查询所有数据开发数据集 以及文件夹-不分页"
    assert records[0]["api_name"] == "getDatasetAndDataGroupsByGroupIdAndPage_dataDevelopmentGroup"
    assert records[0]["http_method"] == "POST"


def test_api_path_variable_rule_matches_middle_placeholder():
    assert api_path_matches("/api/inc/{1}data/cloudTitle/queryList", "/api/inc/foo/data/cloudTitle/queryList")
    assert api_path_matches("/api/inc/{1}data/cloudTitle/queryList", "/api/inc/data/cloudTitle/queryList")
    assert not api_path_matches("/api/inc/{1}data/cloudTitle/queryList", "/api/inc/foo/data/cloudTitle/queryList/extra")
