class JobReportingConfig:
	DEFAULT_BASE_URL = 'http://172.31.8.12:8080'

	def __init__(self, view_name, job_name, rerun_name, classname_index, filepath_range, application_delimiter=None, 
		test_name_delimiter=None, base_url=None):
		self.view_name = view_name
		self.job_name = job_name
		self.rerun_name = rerun_name
		self.application_classname_index = classname_index
		self.application_name_delimiter = application_delimiter
		self.app_title_mappings = {}
		self.results_parsers = []
		self.base_url = base_url if base_url else JobReportingConfig.DEFAULT_BASE_URL
		self.test_name_delimiter = test_name_delimiter
		self.filepath_start_index = filepath_range[0]
		self.filepath_end_index = filepath_range[1]

	def add_app_title_mapping(self, app_key, title):
		self.app_title_mappings[app_key] = title

	def add_results_parser(self, parser):
		self.results_parsers.append(parser)

	def job(self, is_rerun):
		return self.rerun_name if is_rerun else self.job_name

	@classmethod
	def gl_regression_config(cls):
		config = JobReportingConfig('GL Regression', 'GL Regression Build', 'GL Regression Test Fail', 7, (3, 7))
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
		config.add_results_parser(ApplicationNameParser)
		return config

	@classmethod
	def gl1000r_regression_config(cls):
		config = JobReportingConfig('GL Regression', 'GL1000R_REGRESSION_TEST', 'GL1000R Rerun Test Failures', 
			8, (3, 8), 'GL1000_')
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
		config.add_results_parser(ApplicationNameParser)
		return config

	@classmethod
	def navigation_config(cls, job_name):
		config = JobReportingConfig('Navigations', job_name, None, 7, (3, 6), test_name_delimiter='_nav[0-9]+_[0-9]+_navigation_')
		config.add_results_parser(TestCaseNamesParser)
		return config

	@classmethod
	def navigation_cs_bo_in_config(cls):
		return cls.navigation_config('navigation CS BO IN2')

	@classmethod
	def navigation_gl_py_config(cls):
		return cls.navigation_config('navigation GL PY')

	@classmethod
	def navigation_pd_config(cls):
		return cls.navigation_config('navigation PD')

	@classmethod
	def navigation_sd_config(cls):
		return cls.navigation_config('navigation SD')

	@classmethod
	def navigation_se_dg_dr_ex_pm_config(cls):
		return cls.navigation_config('navigation SE DG DR EX PM')