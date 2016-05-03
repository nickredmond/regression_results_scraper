import datetime

class Logger:
	DEFAULT_FILENAME='application.log'
	NEWLINE = '\n'

	def __init__(self, filename=DEFAULT_FILENAME, header=None):
		self.filename = filename
		self.lines = []
		if header:
			self.lines.append(self._header_for(header))

	def log_info(self, message):
		line = '[INFO]: ' + message + Logger.NEWLINE
		self.lines.append(line)

	def dump(self):
		file = open(self.filename, 'a')
		file.writelines(self.lines)
		file.close()
		print('Dumped logs to \'' + self.filename + '\'')

	def _header_for(self, header):
		return '--- ' + header + ' > ' + str(datetime.datetime.now()) + Logger.NEWLINE