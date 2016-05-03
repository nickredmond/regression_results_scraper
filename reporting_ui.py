import threading
import sys
import time

class ProgressBar(threading.Thread):
	DEFAULT_FPS = 20
	PROGRESS_ICON = '#'
	NO_PROGRESS_ICON = '-'

	def __init__(self, reporting_status, job_name, bar_width=20, fps=DEFAULT_FPS):
		threading.Thread.__init__(self)
		self.reporting_status = reporting_status
		self.bar_width = bar_width
		self.fps = fps
		self.job_name = job_name
		self.manual_progression = 0.0

	def progress(self, percentage):
		self.manual_progression += percentage

	def run(self):
		percent_complete = self._percent_complete()
		while percent_complete < 1.0:
			# print('really: ' + str(self.reporting_status.current_build_number))
			bar_value = self.job_name + '> ['
			# sys.stdout.write("\r{0}>".format())
			number_bars = int(percent_complete * self.bar_width)
			for i in range(0, number_bars):
				# sys.stdout.write("\r{0}>".format(ProgressBar.PROGRESS_ICON))
				bar_value += ProgressBar.PROGRESS_ICON
			for i in range(0, (self.bar_width - number_bars)):
				# sys.stdout.write("\r{0}>".format(ProgressBar.NO_PROGRESS_ICON))
				bar_value += ProgressBar.NO_PROGRESS_ICON
			percent_value = percent_complete * 100
			# sys.stdout.write("\r{0}>".format(']' + str(round(percent_value, 2)) + '%'))
			bar_value += '] ' + str(round(percent_value, 2)) + '%'
			sys.stdout.write("\r{0}".format(bar_value))
			sys.stdout.flush()

			percent_complete = self._percent_complete()
			time.sleep(1.0 / self.fps)
			# print('percentage is ' + str(percent_value))
		bar_value = self.job_name + '> [' + (ProgressBar.PROGRESS_ICON * self.bar_width) + '] 100.00%'
		sys.stdout.write("\r{0}".format(bar_value))
		sys.stdout.flush()
		print('')

	def _percent_complete(self):
		# reporting_status = self.results_service.reporting_status()
		starting_build_number = self.reporting_status.starting_build_number
		actual_percent_complete = (float(self.reporting_status.current_build_number - starting_build_number) /
			float(self.reporting_status.ending_build_number - starting_build_number))
		percent_complete = (1 - self.manual_progression) * actual_percent_complete
		return percent_complete

class ReportingStatus:
	def __init__(self, starting_build_number, ending_build_number):
		self.starting_build_number = starting_build_number
		self.ending_build_number = ending_build_number
		self.current_build_number = starting_build_number