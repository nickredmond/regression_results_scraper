from openpyxl import Workbook

from build_results import BuildResultsService
from config import JobReportingConfig
from excel_reporting import WorkbookManager

excel_manager = WorkbookManager(Workbook())

gl_regression_service = BuildResultsService(JobReportingConfig.gl_regression_config())
gl_regression_results = gl_regression_service.compose_rerun_regression_results()
excel_manager.write_results_to_worksheet(gl_regression_results, 'GL Regression')

gl1000r_service = BuildResultsService(JobReportingConfig.gl1000r_regression_config())
gl1000r_results = gl1000r_service.compose_rerun_regression_results()
excel_manager.write_results_to_worksheet(gl1000r_results, 'GL1000R', True)

nav_results = []

nav_infos = [
	{ 'config': JobReportingConfig.navigation_cs_bo_in_config(), 'app_title': 'CS/BO/IN' },
	{ 'config': JobReportingConfig.navigation_gl_py_config(), 'app_title': 'GL/PY' },
	{ 'config': JobReportingConfig.navigation_pd_config(), 'app_title': 'PD' },
	{ 'config': JobReportingConfig.navigation_sd_config(), 'app_title': 'SD' },
	{ 'config': JobReportingConfig.navigation_se_dg_dr_ex_pm_config(), 'app_title': 'SE/DG/DR/EX/PM' }
]
for info in nav_infos:
	nav_service = BuildResultsService(info['config'])
	results = nav_service.compose_single_job_regression_results(info['app_title'])
	nav_results.append(results)
excel_manager.write_results_to_worksheet(nav_results, 'Navigation', True)

excel_manager.save_workbook()


