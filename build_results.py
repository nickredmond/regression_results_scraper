import json
import urllib.request
from urllib.error import HTTPError
import re

from reporting_ui import ProgressBar, ReportingStatus

class JenkinsClient:
	@classmethod
	def json_response_from_request(cls, base_url, view_name, job_name, build_number, is_test_report=False):
		view = view_name.replace(' ', '%20')
		job = job_name.replace(' ', '%20')
		build_id = 'lastBuild' if int(build_number) == -1 else str(build_number)
		response = urllib.request.urlopen(base_url + '/view/' + view + '/job/' + job + '/' + build_id + 
			('/testReport' if is_test_report else '') + '/api/json')
		str_response = response.read().decode('utf-8')
		return json.loads(str_response)

	@classmethod
	def latest_build_id(cls, base_url, view_name, job_name):
		data = cls.json_response_from_request(base_url, view_name, job_name, -1)
		return int(data['id'])

	@classmethod
	def construct_test_results_for_build(cls, job_config, build_number, is_rerun=False, logger=None):
		result = { 'failure_links': [] }
		application = None
		job = job_config.job(is_rerun)

		try:
			data = JenkinsClient.json_response_from_request(job_config.base_url, job_config.view_name, job, build_number, True)
			for case in data['suites'][0]['cases']:
				class_name_parts = case['className'].split('.')
				for parser in job_config.results_parsers:
					result = parser.handle_test_case(job_config, case, class_name_parts, job, build_number, result)
				
			result['number_passing'] = data['passCount']
			result['number_failing'] = data['failCount']

			for parser in job_config.results_parsers:
				if callable(getattr(parser, 'parse_application_title', None)):
					result = parser.parse_application_title(job_config, job, build_number, result)
		except HTTPError:
			logger.log_info('No such build number \'' + str(build_number) + '\' for job \'' + job + '\'; Skipping...')
			result = None

		return result

class TestResultsParser:
	@classmethod
	def handle_test_case(cls, job_config, case, class_name_parts, job, build_number, result):
		raise Exception('Cannot implement TestResultsParser')

	@classmethod
	def is_application_parsable(cls, application, class_name_parts, job_config):
		return (len(class_name_parts) > job_config.application_classname_index)

	@classmethod
	def parse_failure_url(cls, job_config, case, class_name_parts, job, build_number):
		url = None
		if case['status'] in ['FAILED', 'REGRESSION']:
			class_name = ''
			for i in range(0, len(class_name_parts) - 1):
				class_name += class_name_parts[i] + '.'
			url = (job_config.base_url + '/view/' + job_config.view_name + '/job/' + job + '/' + str(build_number) + '/testReport/junit/' + class_name[:-1] + '/' + 
				class_name_parts[-1] + '/' + case['name'])
		return url

	@classmethod
	def construct_failure_link_value(cls, job_config, case_name, class_name_parts):
		link_value = case_name
		if getattr(job_config, 'test_filename_index', None) and len(class_name_parts) > job_config.test_filename_index:
			link_value = class_name_parts[job_config.test_filename_index] + '.' + link_value
		return link_value

class ApplicationNameParser(TestResultsParser):
	@classmethod
	def handle_test_case(cls, job_config, case, class_name_parts, job, build_number, result):
		modified_result = result
		if 'application' not in modified_result:
			modified_result['application'] = None
		if cls.is_application_parsable(modified_result['application'], class_name_parts, job_config): 
			application = class_name_parts[job_config.application_classname_index]
			if job_config.application_name_delimiter and job_config.application_name_delimiter in application:
				application = application.split(job_config.application_name_delimiter)[1]
			modified_result['application'] = application

		failure_url = cls.parse_failure_url(job_config, case, class_name_parts, job, build_number)
		link_value = cls.construct_failure_link_value(job_config, case['name'], class_name_parts)
		if failure_url:
			modified_result['failure_links'].append({'value': link_value, 'url': failure_url})
		return modified_result	

	@classmethod
	def parse_application_title(cls, job_config, job, build_number, result):
		modified_result = result
		data = JenkinsClient.json_response_from_request(job_config.base_url, job_config.view_name, job, build_number)
		parameters = None
		if 'parameters' in data['actions'][0]:
			parameters = data['actions'][0]['parameters']
		elif 'parameters' in data['actions'][1]:
			parameters = data['actions'][1]['parameters']
		else:
			raise Exception('Could not find build parameters in JSON response')

		application = modified_result['application']
		del modified_result['application']
		index = 0
		while not application:
			if index >= len(parameters):
				application = 'N/A'
			else:
				if parameters[index]['name'] == 'APPLICATION':
					application = parameters[index]['value']
			index += 1

		modified_result['app_title'] = job_config.app_title_mappings[application] if application in job_config.app_title_mappings else 'Unknown Application'	
		return modified_result

class TestCaseNamesParser(TestResultsParser):
	@classmethod
	def handle_test_case(cls, job_config, case, class_name_parts, job, build_number, result):
		modified_result = result
		if 'test_cases' not in modified_result:
			modified_result['test_cases'] = []
		is_passing = (case['status'] not in ['FAILED', 'REGRESSION'])

		next_case = { 'name': case['name'], 'is_passing': is_passing, 'failure_link': None }
		failure_url = cls.parse_failure_url(job_config, case, class_name_parts, job, build_number)
		if failure_url:
			failure_link = cls.construct_failure_link_value(job_config, case['name'], class_name_parts)
			next_case['failure_link'] = { 'value': failure_link, 'url': failure_url }
		modified_result['test_cases'].append(next_case)
		return modified_result

build_history_reporting_length = 30

class BuildResultsService:
	DEFAULT_CONFIG_LOCATION = "./"
	def __init__(self, job_config, logger):
		self.job_config = job_config
		self.logger = logger
		self.reporting_status = ReportingStatus(0, 1)
		self.progress_bar = None

	def construct_build_number_range(self, is_rerun=False):
		last_build_number = JenkinsClient.latest_build_id(self.job_config.base_url, self.job_config.view_name, 
			self.job_config.job(is_rerun))
		return range(last_build_number - build_history_reporting_length, last_build_number + 1)

	def compose_rerun_regression_results(self):
		build_results = []

		build_info = {}
		job_build_range = self.construct_build_number_range()
		rerun_build_range = self.construct_build_number_range(True)
		build_info['starting_number'] = job_build_range[0]
		total_builds = len(job_build_range) + len(rerun_build_range)
		build_info['ending_number'] = build_info['starting_number'] + total_builds
		build_info['current_number'] = build_info['starting_number']
		self._start_progress_bar(build_info=build_info)

		for number in job_build_range:
			next_result = JenkinsClient.construct_test_results_for_build(self.job_config, number, logger=self.logger)
			if next_result:
				if next_result['app_title'] in [result['app_title'] for result in build_results]:
					build_results = list(filter(lambda result: result['app_title'] != next_result['app_title'], build_results))
				build_results.append(next_result)
			self.reporting_status.current_build_number += 1
		self.reporting_status.current_build_number += 1

		rerun_results = []
		for number in self.construct_build_number_range(True):
			next_result = JenkinsClient.construct_test_results_for_build(self.job_config, number, True, logger=self.logger)
			if next_result:
				if next_result['app_title'] in [result['app_title'] for result in rerun_results]:
					rerun_results = list(filter(lambda result: result['app_title'] != next_result['app_title'], rerun_results))
				rerun_results.append(next_result)
			self.reporting_status.current_build_number += 1
		self.reporting_status.current_build_number += 1
		self.progress_bar.join()

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

	def compose_single_job_regression_results(self, app_title):
		data = JenkinsClient.json_response_from_request(self.job_config.base_url, self.job_config.view_name, 
			self.job_config.job_name, -1)

		last_build_number = int(data['id'])
		case_names = []
		status_count = 0
		passing_count = 0
		failing_count = 0
		failure_links = []

		tests = []

		results_service = BuildResultsService(self.job_config, self.logger)
		for build_number in results_service.construct_build_number_range():
			new_results = JenkinsClient.construct_test_results_for_build(self.job_config, build_number, logger=self.logger)
			if new_results:
				for case in new_results['test_cases']:
					case_name_tokens = [case['name']]
					if getattr(self.job_config, 'test_name_delimiter', None):
						case_name_tokens = re.compile(self.job_config.test_name_delimiter).split(case['name'])
					case_name = case_name_tokens[1] if len(case_name_tokens) > 1 else case_name_tokens[0]
					if case_name in [test['case_name'] for test in tests]:
						tests = list(filter(lambda test: test['case_name'] != case_name, tests))

					# failure_value = TestResultsParser.construct_failure_link_value(self.job_config, case['name'])
					failure_link = case['failure_link'] #{ 'value': case_name, 'url': case['failure_url'] } if case['failure_url'] else None
					new_test = { 
						'case_name': case_name, 
						'is_passing': case['is_passing'], 
						'failure_link': failure_link
					}
					tests.append(new_test)

		passing_count = len(list(filter(lambda test: test['is_passing'], tests)))
		failing_count = len(list(filter(lambda test: not test['is_passing'], tests)))
		failure_links = [test['failure_link'] for test in tests if test['failure_link']]
		return {
			'app_title': app_title,
			'number_passing': passing_count,
			'number_failing': failing_count,
			'failure_links': failure_links
		}

	def _start_progress_bar(self, is_rerun=False, build_info=None):
		if build_info:
			self.reporting_status.starting_build_number = build_info['starting_number']
			self.reporting_status.ending_build_number = build_info['ending_number']
			self.reporting_status.current_build_number = build_info['current_number']
		else:
			self._reset_reporting_status()
		self.progress_bar = ProgressBar(self.reporting_status, self.job_config.job_name)
		self.progress_bar.start()

	def stop_execution(self):
		self.progress_bar.stop_execution()

	def _reset_reporting_status(self):
		self.reporting_status.starting_build_number = 0
		self.reporting_status.ending_build_number = 1
		self.reporting_status.current_build_number = 0