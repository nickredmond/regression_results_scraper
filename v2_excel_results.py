import json
import urllib.request
from urllib.error import HTTPError
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Border, Side
from openpyxl.formatting.rule import CellIsRule
import sys, re
import os.path
from enum import Enum

from build_results import BuildResultsService

reporting_config = JobReportingConfig.gl_regression_config() 
gl_regression_results = compose_rerun_regression_results(reporting_config)
reporting_config = JobReportingConfig.gl1000r_regression_config()
gl1000r_results = compose_rerun_regression_results(reporting_config)

wb = Workbook()

write_results_to_worksheet(wb, 'GL Regression', gl_regression_results)
write_results_to_worksheet(wb, 'GL1000R', gl1000r_results, True)

# NEW
nav_results = []

nav_infos = [
	{ 'config': JobReportingConfig.navigation_cs_bo_in_config(), 'app_title': 'CS/BO/IN' },
	{ 'config': JobReportingConfig.navigation_gl_py_config(), 'app_title': 'GL/PY' },
	{ 'config': JobReportingConfig.navigation_pd_config(), 'app_title': 'PD' },
	{ 'config': JobReportingConfig.navigation_sd_config(), 'app_title': 'SD' },
	{ 'config': JobReportingConfig.navigation_se_dg_dr_ex_pm_config(), 'app_title': 'SE/DG/DR/EX/PM' }
]
for info in nav_infos:
	results = compose_single_job_regression_results(info['config'], info['app_title'])
	nav_results.append(results)

write_results_to_worksheet(wb, 'Navigation', nav_results, True)
# ENDNEW

