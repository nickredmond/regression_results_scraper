from openpyxl import Workbook

from build_results import BuildResultsService
from config import JobReportingConfigManager
from excel_reporting import WorkbookManager
from reporting_ui import ProgressBar, ReportingStatus

config_manager = JobReportingConfigManager()
config_manager.read_config_from_file()
excel_manager = WorkbookManager(Workbook(), config_manager.percentage_formatting)

is_rerun = False
for config in config_manager.rerun_job_configs:
	build_service = BuildResultsService(config)
	results = build_service.compose_rerun_regression_results()
	excel_manager.write_results_to_worksheet(results, config.sheet_title, is_rerun)
	is_rerun = True
for config in config_manager.job_group_configs:
	build_service = BuildResultsService(config)
	group_results = []

	reporting_status = ReportingStatus(0, len(config.job_application_mappings))
	progress_bar = ProgressBar(reporting_status, config.view_name)
	progress_bar.start()
	for app_title in config.job_application_mappings:
		job_config = config.config_for(app_title)
		build_service = BuildResultsService(job_config)
		results = build_service.compose_single_job_regression_results(app_title)
		group_results.append(results)
		reporting_status.current_build_number += 1
	reporting_status.current_build_number += 1
	progress_bar.join()
	excel_manager.write_results_to_worksheet(group_results, config.sheet_title, is_rerun)
	is_rerun = True

excel_manager.save_workbook()