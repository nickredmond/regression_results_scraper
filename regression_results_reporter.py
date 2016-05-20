from openpyxl import Workbook

from build_results import BuildResultsService
from config import JobReportingConfigManager
from excel_reporting import WorkbookManager
from reporting_ui import ProgressBar, ReportingStatus
from utils import Logger, CommandArgumentsParser

config_filename = CommandArgumentsParser.get_argument('config-filename', 'c')
if config_filename and config_filename is True:
	print('INFO: Did not specify any config filename value, so the default will be used.')
	config_filename = None

config_manager = JobReportingConfigManager(config_filename)
config_manager.read_config_from_file()
excel_manager = WorkbookManager(Workbook(), config_manager.percentage_formatting)
logger = Logger(header='Regression Results Report')

def compose_overall_result(config, test_results):
	return {
		'app_title': config.sheet_title,
		'number_passing': sum(result['number_passing'] for result in test_results),
		'number_failing': sum(result['number_failing'] for result in test_results),
		'failure_links': None
	}

is_rerun = False
overall_results = []
for config in config_manager.rerun_job_configs:
	build_service = BuildResultsService(config, logger)
	try:
		results = build_service.compose_rerun_regression_results()
		overall_result = compose_overall_result(config, results)
		overall_results.append(overall_result)

		excel_manager.write_results_to_worksheet(results, config.sheet_title, is_rerun)
		is_rerun = True
	except:
		build_service.stop_execution()
		raise
for config in config_manager.job_group_configs:
	build_service = BuildResultsService(config, logger)
	group_results = []

	reporting_status = ReportingStatus(0, len(config.job_application_mappings))
	progress_bar = ProgressBar(reporting_status, config.view_name)
	progress_bar.start()
	try:
		for app_title in config.job_application_mappings:
			job_config = config.config_for(app_title)
			build_service = BuildResultsService(job_config, logger)
			results = build_service.compose_single_job_regression_results(app_title)
			group_results.append(results)
			reporting_status.current_build_number += 1
		reporting_status.current_build_number += 1
		progress_bar.join()
		overall_result = compose_overall_result(config, group_results)
		overall_results.append(overall_result)

		excel_manager.write_results_to_worksheet(group_results, config.sheet_title, is_rerun)
	except:
		progress_bar.stop_execution()
		raise
	is_rerun = True

excel_manager.write_results_to_worksheet(overall_results, 'Regression Results', True, table_name='Module',
	table_title='Overall Automated Regression Results', is_failures_reported=False, is_main_sheet=True)
excel_manager.save_workbook()
logger.dump()