import json
import urllib.request
from urllib.error import HTTPError
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Border, Side
from openpyxl.formatting.rule import CellIsRule
import sys, re
import os.path

def json_response_from_request(base_url, view_name, job_name, build_number, is_test_report=False):
	view = view_name.replace(' ', '%20')
	job = job_name.replace(' ', '%20')
	response = urllib.request.urlopen(base_url + '/view/' + view + '/job/' + job + '/' + str(build_number) + 
		('/testReport' if is_test_report else '') + '/api/json')
	str_response = response.read().decode('utf-8')
	return json.loads(str_response)

def fill_from_hex_value(hex_value):
	return PatternFill(start_color=hex_value, end_color=hex_value, fill_type='solid')

def paint_cell(ws, row, col, text, fillColor=None, is_bold=False, font_size=12, border=None, is_percent=False, font_color='000000'):
	cell_location = chr(col) + str(row)
	ws[cell_location] = text
	if fillColor:
		ws[cell_location].fill = fill_from_hex_value(fillColor)
	if border:
		ws[cell_location].border = border
	if is_percent:
		ws[cell_location].number_format = '0%'
	ws[cell_location].font = Font(bold=is_bold, size=font_size, color=font_color)

def paint_hyperlink(ws, row, col, link):
	cell_location = chr(col) + str(row)
	ws[cell_location] = link['value']
	ws[cell_location].hyperlink = link['url']
	ws[cell_location].font = Font(underline='single', color='0563C1')

class ResultsTable:
	STARTING_ROW = 2
	STARTING_COL = 66
	BORDER = Border(left=Side(style='thin',color='000000'),
		right=Side(style='thin',color='000000'),
		top=Side(style='thin',color='000000'),
		bottom=Side(style='thin',color='000000'))

	def __init__(self, job_name):
		self.job_name = job_name
		self.results = []

	@classmethod
	def add_status_formatting_to_range(cls, ws, format_range):
		ws.conditional_formatting.add(format_range, CellIsRule(operator='equal', formula=[1.0], fill=fill_from_hex_value('C6EFCE'), font=Font(color='006100')))
		ws.conditional_formatting.add(format_range, CellIsRule(operator='between', formula=[0.75, 1.0], fill=fill_from_hex_value('FFEB9C'), font=Font(color='9C6500')))
		ws.conditional_formatting.add(format_range, CellIsRule(operator='lessThan', formula=[0.75], fill=fill_from_hex_value('FFC7CE'), font=Font(color='9C0006')))

	def add_result(self, app_name, passCount, failCount):
		self.results.append({'app_name': app_name, 'passCount': passCount, 'failCount': failCount})

	def write_results(self, worksheet):
		headerFill = 'A9D08E'
		totalFill = 'E7E6E6'

		percent_col = chr(ResultsTable.STARTING_COL + 4)
		avg_col = chr(ResultsTable.STARTING_COL + 5)
		ending_row = str(ResultsTable.STARTING_ROW + len(self.results) + 1)
		format_range = percent_col + str(ResultsTable.STARTING_ROW + 1) + ':' + percent_col + ending_row 
		ResultsTable.add_status_formatting_to_range(worksheet, format_range)

		row = ResultsTable.STARTING_ROW
		col = ResultsTable.STARTING_COL
		worksheet.column_dimensions[chr(col)].width = 35
		paint_cell(worksheet, row, col, self.job_name, fillColor=headerFill, font_size=14, border=ResultsTable.BORDER)
		col += 1
		paint_cell(worksheet, row, col, 'Total', fillColor=headerFill, font_size=14, border=ResultsTable.BORDER)
		col += 1
		paint_cell(worksheet, row, col, 'Passing', fillColor=headerFill, font_size=14, border=ResultsTable.BORDER)
		col += 1
		paint_cell(worksheet, row, col, 'Failing', fillColor=headerFill, font_size=14, border=ResultsTable.BORDER)
		col += 1
		worksheet.column_dimensions[chr(col)].width = 20
		paint_cell(worksheet, row, col, 'Percent Passing', fillColor=headerFill, font_size=14, border=ResultsTable.BORDER)

		col = ResultsTable.STARTING_COL
		row += 1
		starting_row = row
		for result in self.results:
			total_number_tests = float(result['passCount']) + float(result['failCount'])
			paint_cell(worksheet, row, col, result['app_name'], font_size=14, border=ResultsTable.BORDER)
			col += 1
			paint_cell(worksheet, row, col, (total_number_tests), border=ResultsTable.BORDER)
			col += 1
			paint_cell(worksheet, row, col, result['passCount'], border=ResultsTable.BORDER)
			col += 1
			paint_cell(worksheet, row, col, result['failCount'], border=ResultsTable.BORDER)
			col += 1
			paint_cell(worksheet, row, col, (result['passCount'] / total_number_tests), border=ResultsTable.BORDER, is_percent=True)
			row += 1
			col = ResultsTable.STARTING_COL

		totalFill = 'E7E6E6'
		paint_cell(worksheet, row, col, 'TOTAL', fillColor=totalFill, is_bold=True, border=ResultsTable.BORDER)
		for i in range(0,3):
			col += 1
			cell_range = chr(col) + str(starting_row) + ':' + chr(col) + str(row-1)
			paint_cell(worksheet, row, col, '=SUM(' + cell_range + ')', fillColor=totalFill, is_bold=True, border=ResultsTable.BORDER)
		percentage_passed_formula = '=' + chr(col-1) + str(row) + '/' + chr(col-2) + str(row)
		paint_cell(worksheet, row, col+1, percentage_passed_formula, border=ResultsTable.BORDER, is_percent=True)

		formula_range = chr(col+1) + str(starting_row) + ':' + chr(col+1) + str(row-1)
		avg_passed_formula = '=AVERAGE(' + formula_range + ')'
		stdev_passed_formula = '=STDEV.P(' + formula_range + ')'
		paint_cell(worksheet, row-1, col+2, 'Avg. % Pass', fillColor='000000', font_color='FFFFFF', is_bold=True)
		# paint_cell(ws, row-1, col+3, 'STDEV % Pass', fillColor='000000', font_color='FFFFFF', is_bold=True)
		paint_cell(worksheet, row, col+2, avg_passed_formula, border=ResultsTable.BORDER, is_percent=True)
		ResultsTable.add_status_formatting_to_range(worksheet, (chr(col+2) + str(row) + ':' + chr(col+2) +str(row)))
		# paint_cell(ws, row, col+3, stdev_passed_formula, border=ResultsTable.BORDER, fillColor=totalFill)
		worksheet.column_dimensions[chr(col+2)].width = 15

		return row + 1

class FailureList:
	COLUMN = ResultsTable.STARTING_COL

	def __init__(self, app_name, failures):
		self.app_name = app_name
		self.failures = failures

	def write_results(self, worksheet, row_number):
		paint_cell(worksheet, row_number, FailureList.COLUMN, self.app_name)
		row = row_number + 1
		for link in self.failures:
			paint_hyperlink(worksheet, row, FailureList.COLUMN, link)
			row += 1
		return row
 
def construct_test_results_for_build(job_config, build_number, is_rerun=False):
	failure_links = []
	result = None
	application = None
	job = job_config.rerun_name if is_rerun else job_config.job_name

	try:
		data = json_response_from_request(job_config.base_url, job_config.view_name, job, build_number, True)
		for case in data['suites'][0]['cases']:
			class_name_parts = case['className'].split('.')
			if not application and len(class_name_parts) > job_config.application_classname_index:
				application = class_name_parts[job_config.application_classname_index]
				if job_config.application_name_delimiter and job_config.application_name_delimiter in application:
					application = application.split(job_config.application_name_delimiter)[1]
			if case['status'] in ['FAILED', 'REGRESSION']:
				class_name = ''
				for i in range(0, len(class_name_parts) - 1):
					class_name += class_name_parts[i] + '.'
				url = (job_config.base_url + '/view/' + job_config.view_name + '/job/' + job + '/' + str(build_number) + '/testReport/junit/' + class_name[:-1] + '/' + 
					class_name_parts[-1] + '/' + case['name'])
				failure_links.append({'value': case['name'], 'url': url})
		number_passing = data['passCount']
		number_failing = data['failCount']

		data = json_response_from_request(job_config.base_url, job_config.view_name, job, build_number)
		parameters = None
		if 'parameters' in data['actions'][0]:
			parameters = data['actions'][0]['parameters']
		elif 'parameters' in data['actions'][1]:
			parameters = data['actions'][1]['parameters']
		else:
			raise Exception('Could not find build parameters in JSON response')

		index = 0
		while not application:
			if index >= len(parameters):
				application = 'N/A'
			else:
				if parameters[index]['name'] == 'APPLICATION':
					application = parameters[index]['value']
			index += 1

		title = job_config.app_title_mappings[application] if application in job_config.app_title_mappings else 'Unknown Application'
		result = {
			'app_title': title,
			'number_passing': number_passing,
			'number_failing': number_failing,
			'failure_links': failure_links
		}
	except HTTPError:
		print('No such build number \'' + str(build_number) + '\' for job \'' + job + '\'; Skipping...')

	return result

class JobReportingConfig:
	DEFAULT_BASE_URL = 'http://172.31.8.12:8080'

	def __init__(self, view_name, job_name, rerun_name, classname_index, application_delimiter=None, base_url=None):
		self.view_name = view_name
		self.job_name = job_name
		self.rerun_name = rerun_name
		self.application_classname_index = classname_index
		self.application_name_delimiter = application_delimiter
		self.app_title_mappings = {}
		self.base_url = base_url if base_url else JobReportingConfig.DEFAULT_BASE_URL

	def add_app_title_mapping(self, app_key, title):
		self.app_title_mappings[app_key] = title

	@classmethod
	def gl_regression_config(cls):
		config = JobReportingConfig('GL Regression', 'GL Regression Build', 'GL Regression Test Fail', 7)
		config.add_app_title_mapping('accounts_receivable', 'Accounts Receivable')
		config.add_app_title_mapping('accounting_tools', 'Accounting Tools')
		config.add_app_title_mapping('application_environment', 'Application Environment')
		config.add_app_title_mapping('audit_reporting', 'Audit Reporting')
		config.add_app_title_mapping('bank_deposits', 'Bank Deposits')
		config.add_app_title_mapping('cashier', 'Cashier')
		config.add_app_title_mapping('charge_customers', 'Charge Customers')
		config.add_app_title_mapping('chart_of_accounts', 'Chart of Accounts')
		config.add_app_title_mapping('enter_transactions', 'Enter Transactions')
		config.add_app_title_mapping('financial_analysis', 'Financial Analysis')
		config.add_app_title_mapping('gl_customer_contact', 'GL Customer Contact')
		config.add_app_title_mapping('gl_inventory', 'GL Inventory')
		config.add_app_title_mapping('miscellaneous', 'Miscellaneous')
		config.add_app_title_mapping('glptrns', 'GLPTRNS')
		config.add_app_title_mapping('hand_written_checks', 'Hand Written Checks')
		config.add_app_title_mapping('inquiry', 'Inquiry')
		config.add_app_title_mapping('managed_accounts', 'Managed Accounts')
		config.add_app_title_mapping('open_payables', 'Open Payables')
		config.add_app_title_mapping('purchasing', 'Purchasing')
		config.add_app_title_mapping('receipt_cash', 'Receipt Cash')
		config.add_app_title_mapping('reconcile_bank_accounts', 'Reconcile Bank Accounts')
		config.add_app_title_mapping('report_to_outside_parties', 'Report to Outside Parties')
		config.add_app_title_mapping('transaction_analysis', 'Transaction Analysis')
		config.add_app_title_mapping('vendors', 'Vendors')
		config.add_app_title_mapping('write_checks', 'Write Checks')
		config.add_app_title_mapping('dmscore_6420', 'DMSCORE 6420')
		return config

	@classmethod
	def gl1000r_regression_config(cls):
		config = JobReportingConfig('GL Regression', 'GL1000R_REGRESSION_TEST', 'GL1000R Rerun Test Failures', 8, 'GL1000_')
		config.add_app_title_mapping('miscellaneous', 'Miscellaneous')
		config.add_app_title_mapping('line_field', 'Line Number')
		config.add_app_title_mapping('line_number', 'Line Number')
		config.add_app_title_mapping('amount_field', 'Amount')
		config.add_app_title_mapping('amount', 'Amount')
		config.add_app_title_mapping('change_control_number', 'Control Number')
		config.add_app_title_mapping('control_number', 'Control Number')
		config.add_app_title_mapping('change_document_number', 'Document Number')
		config.add_app_title_mapping('document_number', 'Document Number')
		config.add_app_title_mapping('cost_field', 'Cost')
		config.add_app_title_mapping('cost', 'Cost')
		config.add_app_title_mapping('change_journal', 'Journal')
		config.add_app_title_mapping('journal', 'Journal')
		config.add_app_title_mapping('date_field', 'Date')
		config.add_app_title_mapping('date', 'Date')
		config.add_app_title_mapping('test_transactions', 'Transactions')
		config.add_app_title_mapping('transactions', 'Transactions')
		config.add_app_title_mapping('reference_number', 'Reference Number')
		config.add_app_title_mapping('reference', 'Reference Number')
		config.add_app_title_mapping('override_control', 'Override Control')
		config.add_app_title_mapping('change_description', 'Change Description')
		config.add_app_title_mapping('description', 'Change Description')
		config.add_app_title_mapping('change_account', 'Account')
		config.add_app_title_mapping('account', 'Account')
		return config

def compose_rerun_regression_results(job_config, build_numbers, rerun_numbers):
	build_results = []
	for number in build_numbers:
		next_result = construct_test_results_for_build(job_config, number)
		if next_result:
			if next_result['app_title'] in [result['app_title'] for result in build_results]:
				build_results = list(filter(lambda result: result['app_title'] != next_result['app_title'], build_results))
			build_results.append(next_result)

	rerun_results = []
	for number in rerun_numbers:
		next_result = construct_test_results_for_build(job_config, number, True)
		if next_result:
			if next_result['app_title'] in [result['app_title'] for result in rerun_results]:
				rerun_results = list(filter(lambda result: result['app_title'] != next_result['app_title'], rerun_results))
			rerun_results.append(next_result)

	aggregated_results = []
	for result in build_results:
		filtered = list(filter(lambda rerun_result: rerun_result['app_title'] == result['app_title'], rerun_results))
		second = filtered[0] if len(filtered) > 0 else result
		aggregated_results.append({
			'app_title': result['app_title'],
			'number_passing': (result['number_passing'] + result['number_failing']) - second['number_failing'],
			'number_failing': second['number_failing'],
			'failure_links': second['failure_links']
		})
	return aggregated_results

def write_results_to_worksheet(workbook, sheet_name, test_results, is_new_sheet=False):
	worksheet = workbook.create_sheet() if is_new_sheet else workbook.active
	worksheet.title = sheet_name

	table = ResultsTable(sheet_name)
	for result in test_results:
		table.add_result(result['app_title'], result['number_passing'], result['number_failing'])
	next_row = table.write_results(worksheet)

	for result in test_results:
		failures = FailureList(result['app_title'], result['failure_links'])
		next_row = failures.write_results(worksheet, next_row + 1)

def make_build_numbers_from_argument(value):
	numbers = value.split('-')
	builds = []
	if len(numbers) == 2:
		builds = range(int(numbers[0]), int(numbers[1]) + 1)
	else:
		numbers = value.split(',')
		for number in numbers:
			builds.append(number)
	return builds

gl_reg_builds = None
gl_reg_reruns = None
gl1000r_builds = None
gl1000r_reruns = None

for arg in sys.argv[1:]:
	if '=' not in arg:
		raise Exception('Must pass key-value arguments, e.g. view=\'GL Regression\'')
	key, value = arg.split('=')
	if key == 'gl_reg_builds':
		gl_reg_builds = make_build_numbers_from_argument(value)
	elif key == 'gl_reg_reruns':
		gl_reg_reruns = make_build_numbers_from_argument(value)
	elif key == 'gl1000r_builds':
		gl1000r_builds = make_build_numbers_from_argument(value)
	elif key == 'gl1000r_reruns':
		gl1000r_reruns = make_build_numbers_from_argument(value)

if not (gl_reg_builds and gl_reg_reruns and gl1000r_builds and gl1000r_reruns):
	print('Supplying demo values for the report generator...')
	gl_reg_builds = range(268, 294)
	gl_reg_reruns = range(125, 146)
	gl1000r_builds = range(108, 126)
	gl1000r_reruns = range(1, 24)

reporting_config = JobReportingConfig.gl_regression_config() 
gl_regression_results = compose_rerun_regression_results(reporting_config, gl_reg_builds, gl_reg_reruns)
reporting_config = JobReportingConfig.gl1000r_regression_config()
gl1000r_results = compose_rerun_regression_results(reporting_config, gl1000r_builds, gl1000r_reruns)

wb = Workbook()

write_results_to_worksheet(wb, 'GL Regression', gl_regression_results)
write_results_to_worksheet(wb, 'GL1000R', gl1000r_results, True)

default_filename = 'regression_run'
filename = input('Enger filename (\'' + default_filename + '\'): ') or default_filename
extension = '.xlsx'
filename = filename.replace(extension, '')

is_saving = True
if os.path.isfile(filename + extension):
	user_input = input('\'' + filename + extension + '\' already exists. Would you like to overwrite it (Y/N)? ')
	is_saving = (user_input in ['Y', 'y', 'Yes', 'YES', 'yes'])
if is_saving:
	print('Saving \'' + filename + extension + '\'...')
	wb.save(filename='regression_run.xlsx')
	print('Saved')