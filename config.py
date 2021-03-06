import xml.etree.ElementTree as ET
import copy

from build_results import ApplicationNameParser, TestCaseNamesParser

class JobReportingConfigManager:
	DEFAULT_CONFIG_FILENAME = 'reporting_config.xml'

	def __init__(self, config_filename=None):
		self.config_filename = config_filename or JobReportingConfigManager.DEFAULT_CONFIG_FILENAME
		self.job_group_configs = []
		self.rerun_job_configs = []

	def get_results_parser(self, xml_node):
		parser_name = xml_node.find('results_parser').text
		parser_module = __import__('build_results')
		return getattr(parser_module, parser_name)

	def read_config_from_file(self):
		tree = ET.parse(self.config_filename)
		root = tree.getroot()
		base_url = root.find('base_url').text
		build_history_reporting_length = int(root.find('build_history_reporting_length').text)

		for job_config in root.findall('job_config'):
			view_name = job_config.find('view_name').text
			job_name = job_config.find('job_name').text
			classname_index = int(job_config.find('classname_index').text)
			test_filename_index = int(job_config.find('test_filename_index').text)
			sheet_title = job_config.find('sheet_title').text
			rerun_name = job_config.find('rerun_name')
			if rerun_name is not None:
				rerun_name = rerun_name.text
			application_delimiter = job_config.find('application_delimiter')
			if application_delimiter is not None:
				application_delimiter = application_delimiter.text
			config_obj = RerunJobReportingConfig(view_name, sheet_title, job_name, rerun_name, classname_index, test_filename_index, 
				application_delimiter)
			for mapping in job_config.find('app_title_mappings').findall('mapping'):
				config_obj.add_app_title_mapping(mapping.get('app_key'), mapping.get('title'))
			exceptions_list = job_config.find('classname_index_exceptions')
			if not (exceptions_list is None or exceptions_list.findall('exception') is None):
				for index_exception in exceptions_list.findall('exception'):
					index = index_exception.find('index').text
					classname = index_exception.find('classname').text
					application = index_exception.find('application').text
					config_obj.add_classname_index_exception(index, classname, application)
			config_obj.base_url = base_url
			config_obj.build_history_reporting_length = build_history_reporting_length
			config_obj.add_results_parser(self.get_results_parser(job_config))
			self.rerun_job_configs.append(config_obj)

		for job_group in root.findall('job_config_group'):
			view_name = job_group.get('view_name')
			combined_view_name = job_group.get('combined_view_name')
			classname_index = int(self._parse_node_text(job_group, 'classname_index') or -1)
			test_name_delimiter = self._parse_node_text(job_group, 'test_name_delimiter')
			sheet_title = job_group.find('sheet_title').text
			test_filename_index = job_group.find('test_filename_index')
			if test_filename_index is not None:
				test_filename_index = int(test_filename_index.text)

			config_title = (view_name or combined_view_name)
			job_group_config = JobGroupReportingConfig(config_title, sheet_title, classname_index, test_name_delimiter,
				test_filename_index)

			for job_config in job_group.findall('job_config'):
				app_title = job_config.find('app_title').text
				job_name = job_config.find('job_name').text
				if view_name is None:
					view_name = self._parse_node_text(job_config, 'view_name')
				job_group_config.add_job_config(app_title, job_name, view_name)
			job_group_config.base_url = base_url
			job_group_config.build_history_reporting_length = build_history_reporting_length
			job_group_config.add_results_parser(self.get_results_parser(job_group))
			self.job_group_configs.append(job_group_config)

		self.percentage_formatting = {}
		formatting_node = root.find('percentage_formatting')
		for frmt in formatting_node.findall('format'):
			next_format = {}
			next_format['font_color'] = frmt.find('font_color').text
			next_format['fill_color'] = frmt.find('fill_color').text
			next_format['range'] = self._parse_format_range(frmt)
			self.percentage_formatting[frmt.get('type')] = next_format

	def _parse_node_text(self, root_node, node_name):
		node = root_node.find(node_name)
		return node.text if node is not None else None

	def _parse_format_range(self, frmt):
		frmt_range = frmt.find('range')
		format_range = { 'operator': frmt_range.get('operator') }
		range_value = frmt_range.get('value')
		if range_value is not None:
			format_range['value'] = [float(range_value)]
		else:
			min_node = frmt_range.find('min')
			max_node = frmt_range.find('max')
			if min_node is not None and max_node is not None:
				format_range['value'] = [float(min_node.text), float(max_node.text)]
			else:
				raise Exception('Error! Invalid percentage formatting XML.')
		return format_range

class JobApplicationConfig:
	def __init__(self, app_title, job_name):
		self.app_title = app_title
		self.job_name = job_name

class JobReportingConfig:
	def __init__(self, view_name, sheet_title, classname_index):
		self.view_name = view_name
		self.sheet_title = sheet_title
		self.application_classname_index = classname_index
		self.base_url = None
		self.build_history_reporting_length = 0
		self.results_parsers = []

	def add_results_parser(self, parser):
		self.results_parsers.append(parser)

	def is_rerun_defined(self):
		return getattr(self, 'rerun_name', None) and (self.rerun_name is not None)

	def job(self, is_rerun):
		job = None
		if is_rerun and self.is_rerun_defined():
			job = self.rerun_name
		else:
			job = self.job_name
		return job

	def __str__(self):
		return '\{{ view_name: {}, sheet_title: {}, classname_index: {} }}'.format(self.view_name, self.sheet_title, self.application_classname_index)

class JobGroupReportingConfig(JobReportingConfig):
	def __init__(self, view_name, sheet_title, classname_index, test_name_delimiter, test_filename_index=None):
		super(JobGroupReportingConfig, self).__init__(view_name, sheet_title, classname_index)
		self.test_name_delimiter = test_name_delimiter
		self.test_filename_index = test_filename_index
		self.job_application_mappings = {}

	def add_job_config(self, app_title, job_name, view_name=None):
		self.job_application_mappings[app_title] = { 'job': job_name, 'view': view_name }

	def config_for(self, app_title):
		config = copy.deepcopy(self)
		config.job_name = self.job_application_mappings[app_title]['job']
		config.view_name = self.job_application_mappings[app_title]['view'] 
		return config

class RerunJobReportingConfig(JobReportingConfig):
	def __init__(self, view_name, sheet_title, job_name, rerun_name, classname_index, test_filename_index, application_delimiter=None):
		super(RerunJobReportingConfig, self).__init__(view_name, sheet_title, classname_index)
		self.job_name = job_name
		self.rerun_name = rerun_name
		self.application_name_delimiter = application_delimiter
		self.app_title_mappings = {}
		self.test_filename_index = test_filename_index
		self.classname_index_exceptions = []

	def add_app_title_mapping(self, app_key, title):
		self.app_title_mappings[app_key] = title

	def add_classname_index_exception(self, index, classname, application):
		self.classname_index_exceptions.append({
			'index': index,
			'classname': classname,
			'application': application
		})