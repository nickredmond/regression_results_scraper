import datetime
import sys

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

class CommandArgumentsParser:
	SHORT_NAME_PREFIX = '-'
	FULL_NAME_PREFIX = '--'
	ARGUMENT_VALUE_DELIMITER = '='

	@staticmethod
	def get_argument(argument_name, short_name):
		argument = None
		index = 0
		sys_arguments = sys.argv
		while (not argument) and index < len(sys_arguments):
			next_arg = sys_arguments[index]
			if (next_arg.startswith(CommandArgumentsParser.SHORT_NAME_PREFIX + short_name) or 
					next_arg.startswith(CommandArgumentsParser.FULL_NAME_PREFIX + argument_name)):
				argument, index = CommandArgumentsParser._parse_argument(sys_arguments, index)
			else:
				index += 1
		return argument

	@staticmethod
	def _parse_argument(sys_arguments, current_index):
		argument = None
		index = current_index
		current_argument = sys_arguments[current_index]
		if CommandArgumentsParser.ARGUMENT_VALUE_DELIMITER in current_argument:
			argument = current_argument.split(CommandArgumentsParser.ARGUMENT_VALUE_DELIMITER)[1]
			index += 1
		elif current_index < len(sys_arguments) - 1 and not CommandArgumentsParser._is_next_argument_named(sys_arguments, current_index):
			argument = sys_arguments[current_index + 1]
			index += 2
		else:
			argument = True
			index += 1
		return argument, index


	@staticmethod
	def _is_next_argument_named(sys_arguments, current_index):
		next_arg = sys_arguments[current_index + 1]
		return (next_arg.startswith(CommandArgumentsParser.SHORT_NAME_PREFIX) or next_arg.startswith(CommandArgumentsParser.FULL_NAME_PREFIX))