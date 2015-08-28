import re
import csv
import IPython

from printer import mprintln
from subprocess import check_output

class Records:
	FIELD_ANTENNA = 0
	FIELD_BX = 1
	FIELD_BY = 2
	FIELD_DISTANCE = 3
	FIELD_SEPARATION = 4
	FIELD_TIME = 5
	FIELD_TEMP = 6
	FIELD_TRANSITION = 7

	def __init__(self):
		self.number_of_antennas = 12
		self.records = [[['subject', 'time', 'temperature', 'transitions', 'distance', 'separation', 'isolation']]]
		self.num_of_columns = len(self.records[0][0]) + self.number_of_antennas

		# add titles for antennas
		for n in range(1, self.number_of_antennas + 1):
			self.records[0][0].append("antenna" + str(n))

	def get_records(self):
		return self.records

	def add_record(self, bin_data):
		record = [None] * self.num_of_columns

		record[1] = bin_data[0][5]
		record[2] = self.get_temperature(bin_data)
		record[3] = self.get_transitions(bin_data)
		record[4] = self.get_distance(bin_data)
		record[5] = self.get_separation(bin_data)
		record[6] = self.get_isolation(bin_data)
		record[-self.number_of_antennas:] = self.add_antennas(record, bin_data, self.number_of_antennas)

		self.records[0].append(record)

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


class Process:
	def __init__(self):
		pass

	def save_to_csv(self, fname, subjects):
		mprintln('Saving the data to: ' + fname)

		with open(fname, 'wb') as csvfile:
			writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
			for subject in subjects:
				for record in subject:
					writer.writerow(record)

	def dump_data(self, hdf5_folder, filename):
		mprintln('Dumping the data from: ' + filename)
		out_h5ls = check_output([hdf5_folder + 'h5ls', filename + '/subjects'])

		subjects = []
		for n in out_h5ls.split('\n'):
			subject = n.split(' ')[0]
			if subject:
				out_h5dump = check_output([hdf5_folder + 'h5dump', '--group=subjects/' + subject, filename])
				subjects.append(self.extract_data(out_h5dump))

		return subjects

	def extract_data(self, data):
		matches = re.findall('\(\d+\):\s\{[\w\s,.]+\}', data)
		formatted_matches = []
		for match in matches:
			formatted_match = map(lambda x: x.replace(",", "").strip(), match.split('\n'))[1:-1]
			formatted_matches.append(formatted_match)

		return formatted_matches

	def process(self, hdf5_folder, filename, bin_time, fout):
		subjects = self.dump_data(hdf5_folder, filename)
		processed_data = self.process_all(subjects, bin_time)
		self.save_to_csv(fout, processed_data)

		return subjects

	def process_all(self, subjects, bin_time):
		mprintln('Processing the data...')

		records = Records()
		for subject in subjects:
			binned_data = self.get_binned_data(subject, bin_time)
			for bin_data in binned_data:
				records.add_record(bin_data)

		return records.get_records()

	def get_binned_data(self, data, bin_time):
		arr = []
		sub_arr = []
		t0 = None
		for record in data:
			if t0 is None:
				t0 = int(record[5])

			if int(record[5]) > t0 + bin_time:
				arr.append(sub_arr)
				sub_arr = []
				t0 = None

			sub_arr.append(record)

		arr.append(sub_arr)
		return arr

def main():
	hdf5_folder = '/usr/local/hdf5/bin/'
	filename = '1433757203990_000167_AOD12Week1Part2_0000601200000.hdf5'

	p = Process()
	d = p.process(hdf5_folder, filename, 5000 * 60 * 1000, 'output.csv')

	print ''

	mprintln("Getting you into an IPhython session!")
	IPython.embed()

if __name__ == "__main__":
	main()
