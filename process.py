import re
import os
import csv
import datetime
import pytz
import sys
import getopt

# from profilehooks import profile

from printer import mprintln, mprint
from subprocess import check_output

# import cPickle
import IPython

class Records:
	FIELD_ANTENNA = 0
	FIELD_BX = 1
	FIELD_BY = 2
	FIELD_DISTANCE = 3
	FIELD_SEPARATION = 4
	FIELD_TIME = 5
	FIELD_TEMP = 6
	FIELD_TRANSITION = 7

	def __init__(self, timezone, columns, antennas):
		self.timezone = timezone
		self.antennas = antennas
		self.number_of_antennas = 12
		self.antennas_central = [5, 8]
		self.antennas_thigmotactic = [1, 2, 4, 5, 6, 7, 9, 10, 11, 12]

		self.records = [[[]]]
		for n in columns.split("|"):
			self.records[0][0].append(n.strip())

		self.num_of_columns = len(self.records[0][0]) + self.number_of_antennas

		# add titles for antennas, if enabled
		if self.antennas != 'False':
			for n in range(1, self.number_of_antennas + 1):
				self.records[0][0].append("antenna" + str(n))

	def get_records(self):
		return self.records

	def add_record(self, subject, bin_data):
		record = [None] * self.num_of_columns

		record[-self.number_of_antennas:] = self.add_antennas(record, bin_data, self.number_of_antennas)

		for n in range(self.num_of_columns - self.number_of_antennas):
			record[n] = self.fill_column(self.records[0][0][n], subject, bin_data, record)

		# TODO: has to be done this way so far - antennas are necessary for 'thigmotactic' and 'centre-zone'.
		# thus, it needs to be computed first and them removed if disabled
		if self.antennas == 'False':
			record = record[:-self.number_of_antennas]

		self.records[0].append(record)

	def fill_column(self, col, subject, bin_data, record):
		if col == "subject":
			return subject
		elif col == "time":
			local_tz = pytz.timezone(self.timezone)
			return datetime.datetime.fromtimestamp(int(bin_data[0][self.FIELD_TIME]) / 1000.0, local_tz)
		elif col == "temperature":
			return self.get_temperature(bin_data)
		elif col == "transitions":
			return self.get_transitions(bin_data)
		elif col == "distance":
			return self.get_distance(bin_data)
		elif col == "separation":
			return self.get_separation(bin_data)
		elif col == "isolation":
			return self.get_isolation(bin_data)
		elif col == "mobile":
			return self.get_mobile(bin_data)
		elif col == "thigmotactic":
			return self.get_time_of_specific_zones(record[-self.number_of_antennas:], self.antennas_thigmotactic)
		elif col == "centre-zone":
			return self.get_time_of_specific_zones(record[-self.number_of_antennas:], self.antennas_central)

		return None

	def get_temperature(self, data):
		target = self.FIELD_TEMP
		sum_target = 0
		for n in data:
			sum_target += float(n[target])

		avg = sum_target / float(len(data))
		return str(avg)

	def get_transitions(self, data):
		target = self.FIELD_TRANSITION
		sum_transitions = 0
		for n in data:
			if (n[target] == '0x01'):
				sum_transitions += 1

		return sum_transitions

	def get_distance(self, data):
		target = self.FIELD_DISTANCE
		sum_target = 0
		for n in data:
			sum_target += float(n[target])

		return str(sum_target)

	def get_separation(self, data):
		target = self.FIELD_SEPARATION
		sum_target = 0
		for n in data:
			sum_target += float(n[target])

		avg = sum_target / float(len(data))
		return str(avg)

	def get_mobile(self, data):
		target = self.FIELD_DISTANCE
		last_time = int(data[0][self.FIELD_TIME])
		sum_target = 0
		for n in data:
			time_diff = int(n[self.FIELD_TIME]) - last_time
			last_time = int(n[self.FIELD_TIME])
			if(float(n[target]) > 0):
				sum_target += time_diff / 1000.0

		return sum_target

	def get_isolation(self, data):
		target = self.FIELD_SEPARATION
		last_time = int(data[0][self.FIELD_TIME])
		sum_target = 0
		for n in data:
			time_diff = int(n[self.FIELD_TIME]) - last_time
			last_time = int(n[self.FIELD_TIME])
			if(float(n[target]) > 200):
				sum_target += time_diff / 1000.0

		return sum_target

	def add_antennas(self, record, data, size):
		antennas = [0] * size
		last_time = int(data[0][self.FIELD_TIME])
		last_antenna = int(data[0][self.FIELD_ANTENNA])
		for n in data:
			new_time = int(n[self.FIELD_TIME])
			new_antenna = int(n[self.FIELD_ANTENNA])
			if (new_antenna != last_antenna):
				time_diff = new_time - last_time
				antennas[last_antenna - 1] += float(time_diff) / 1000.0

				last_antenna = new_antenna
				last_time = new_time

		return antennas

	def get_time_of_specific_zones(self, antennas, target_antennas):
		sum_value = 0
		for n in target_antennas:
			sum_value += antennas[int(n) - 1]

		return sum_value


class Process:
	FIELD_TIME = 5

	def __init__(self):
		pass

	def save_to_csv(self, fname, subjects):
		mprintln('Saving the data to: ' + fname)

		with open(fname, 'wb') as csvfile:
			writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
			for subject in subjects:
				for record in subject:
					writer.writerow(record)

	def save_processed_data(self, output_dir, processed_data):
		if not os.path.exists(output_dir):
			os.makedirs(output_dir)

		for subject in processed_data:
			self.save_to_csv(output_dir + '/' + subject + '.csv', processed_data[subject].get_records())

	def dump_data(self, hdf5_folder, filename, timezone, subjects={}):
		mprintln('Dumping the data from: ' + filename)
		out_h5ls = check_output([hdf5_folder + 'h5ls', filename + '/subjects'])

		# cache_filenmae = 'obj.save'
		# if os.path.isfile(cache_filenmae):
		# 	f = file(cache_filenmae, 'rb')
		# 	loaded_data = cPickle.load(f)
		# 	f.close()
		# 	return loaded_data

		for n in subjects:
			print n + " - " + str(len(subjects[n]))

		for n in out_h5ls.split('\n'):
			subject = n.split(' ')[0]
			if subject:
				out_h5dump = check_output([hdf5_folder + 'h5dump', '--group=subjects/' + subject, filename])

				if subject not in subjects:
					subjects[subject] = []

				subjects[subject] += self.extract_data(out_h5dump, filename)

				# f = file(cache_filenmae, 'wb')
				# cPickle.dump(subjects, f, protocol=cPickle.HIGHEST_PROTOCOL)
				# f.close()

		for n in subjects:
			print n + " - " + str(len(subjects[n]))

		return subjects

	def extract_data(self, data, filename):
		prog = re.compile('\(\d+\):\s\{[\w\s,.]+\}')
		matches = prog.findall(data)
		formatted_matches = []
		file_time = self.get_time_from_filename(filename)

		for match in matches:
			formatted_match = match.split('\n')[1:-1]
			for n in range(len(formatted_match)):
				formatted_match[n] = formatted_match[n].replace(",", "").strip()

			# handle times
			formatted_match[self.FIELD_TIME] = file_time + int(formatted_match[self.FIELD_TIME])

			formatted_matches.append(formatted_match)

		return formatted_matches

	def process(self, timezone, hdf5_folder, input, output_dir, bin_time, columns, antennas):
		input_files = self.get_hfd5_files(input)

		processed_data = self.process_all(hdf5_folder, columns, antennas, timezone, input_files, bin_time)
		self.save_processed_data(output_dir, processed_data)

		return processed_data

	def process_all(self, hdf5_folder, columns, antennas, timezone, input_files, bin_time):
		mprintln('Processing the data...')
		mprint(str(len(input_files)) + ' file(s) found')

		result = {}

		subjects_data = {}
		for n in range(len(input_files)):
			subjects_data = self.dump_data(hdf5_folder, input_files[n], subjects_data)

			for subject in subjects_data:
				while True:
					binned_data = self.get_binned_record(subjects_data[subject], bin_time)
					if binned_data:
						# remove the records from the list
						subjects_data[subject] = subjects_data[subject][len(binned_data):]

						# add binned data to the result list
						result = self.add_record_to_dictionary(result, timezone, subject, binned_data, columns, antennas)
					else:
						break

		return result

	def add_record_to_dictionary(self, dic, timezone, subject, bin_data, columns, antennas):
		if subject not in dic:
			dic[subject] = Records(timezone, columns, antennas)

		dic[subject].add_record(subject, bin_data)

		return dic

	def get_binned_record(self, data, bin_time):
		arr = []
		t0 = None
		for record in data:
			if t0 is None:
				t0 = int(record[self.FIELD_TIME])

			if int(record[self.FIELD_TIME]) > t0 + bin_time:
				return arr

			arr.append(record)

		return None

	def get_binned_data(self, data, bin_time):
		arr = []
		sub_arr = []
		t0 = None
		for record in data:
			if t0 is None:
				t0 = int(record[self.FIELD_TIME])

			if int(record[self.FIELD_TIME]) > t0 + bin_time:
				arr.append(sub_arr)
				sub_arr = []
				t0 = None

			sub_arr.append(record)

		arr.append(sub_arr)
		return arr

	def get_time_from_filename(self, filename):
		splitted = filename.split('/')
		extracted_time_ms = splitted[len(splitted) - 1].split('_')[0]
		extracted_last_part = splitted[len(splitted) - 1].split('_').pop()
		extracted_experiment_time = int(extracted_last_part.split('.')[0])

		return int(extracted_time_ms) + int(extracted_experiment_time)

	def get_hfd5_files(self, path):
		files = []
		for file in sorted(os.listdir(path)):
			if file.endswith(".hdf5"):
				files.append(path + "/" + file)

		return files

def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hvb:z:f:i:o:c:a:", ["help", "verbose", "bin_time=", "timezone=", "hdf5_folder=", "input=", "output=", "columns=", "antennas="])
	except getopt.GetoptError as err:
		# print help information and exit:
		print str(err)
		usage()
		sys.exit(2)

	args = {
		"verbose": False,
		"bin_time": None,
		"timezone": None,
		"hdf5_folder": None,
		"input": None,
		"output": None,
		"columns": None,
		"antennas": None
	}

	for o, a in opts:
		if o == "-v":
			args['verbose'] = True
		elif o in ("-h"):
			usage()
			sys.exit()
		elif o in ("-b"):
			args['bin_time'] = a
		elif o in ("-z"):
			args['timezone'] = a
		elif o in ("-f"):
			args['hdf5_folder'] = a
		elif o in ("-i"):
			args['input'] = a
		elif o in ("-o"):
			args['output'] = a
		elif o in ("-c"):
			args['columns'] = a
		elif o in ("-a"):
			args['antennas'] = a
		else:
			assert False, "unhandled option"

	p = Process()
	a = p.process(
		timezone=args["timezone"],
		hdf5_folder=args["hdf5_folder"],
		input=args["input"],
		output_dir=args["output"],
		bin_time=int(args["bin_time"]),
		columns=args["columns"],
		antennas=args["antennas"])

	mprint("Getting you into an IPhython session!")
	IPython.embed()

def usage():
	print "usage:"
	print "-b time -z timezone -f hdf5_folder -i input_folder -o output_folder"

if __name__ == "__main__":
	main()
