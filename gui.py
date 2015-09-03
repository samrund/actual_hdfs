import wx
from subprocess import call

class BrowseFolderButton(wx.Button):

	def __init__(self, *args, **kw):
		super(BrowseFolderButton, self).__init__(*args, **kw)

		self._defaultDirectory = '/'
		self.target = None
		self.Bind(wx.EVT_BUTTON, self.on_botton_clicked)

	def on_botton_clicked(self, e):
		dialog = wx.DirDialog(None, "Choose input directory", "", wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)

		if dialog.ShowModal() == wx.ID_OK:
			if self.target:
				self.target.SetValue(dialog.GetPath())

		dialog.Destroy()
		e.Skip()

class BrowseSaveButton(wx.Button):

	def __init__(self, *args, **kw):
		super(BrowseSaveButton, self).__init__(*args, **kw)

		self._defaultDirectory = '/'
		self.target = None
		self.Bind(wx.EVT_BUTTON, self.on_botton_clicked)

	def on_botton_clicked(self, e):
		dialog = wx.FileDialog(self, "Save CSV file", "", "", "CSV files (*.csv)|*.csv", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

		if dialog.ShowModal() == wx.ID_OK:
			if self.target:
				self.target.SetValue(dialog.GetPath())

		dialog.Destroy()
		e.Skip()

class Interface(wx.Frame):

	def __init__(self, parent, title):
		super(Interface, self).__init__(parent, title=title, size=(500, 300))

		self.field_timezone = None
		self.field_spin = None
		self.field_hdf5 = None
		self.field_input = None
		self.field_output = None

		self.init_ui()
		self.Centre()
		self.Show()

	def init_ui(self):
		panel = wx.Panel(self)

		sizer = wx.GridBagSizer(7, 5)

		# BLOCK 1
		# #######
		text_timezone = wx.StaticText(panel, label="Timezone")
		sizer.Add(text_timezone, pos=(0, 0), flag=wx.LEFT | wx.TOP, border=10)

		self.field_timezone = wx.TextCtrl(panel, value="Europe/London")
		sizer.Add(self.field_timezone, pos=(0, 1), span=(1, 2), flag=wx.TOP | wx.EXPAND, border=10)

		text_bin_size = wx.StaticText(panel, label="Bin size (s)")
		sizer.Add(text_bin_size, pos=(1, 0), flag=wx.LEFT | wx.TOP, border=10)

		self.field_spin = wx.SpinCtrl(panel, value='60', size=(60, -1), min=1, max=9999)
		sizer.Add(self.field_spin, pos=(1, 1), span=(1, 1), flag=wx.TOP | wx.EXPAND)

		line = wx.StaticLine(panel)
		sizer.Add(line, pos=(2, 0), span=(1, 5), flag=wx.EXPAND | wx.TOP | wx.BOTTOM, border=10)

		# BLOCK 2
		# #######

		# Line 1
		label_hdf5_folder = wx.StaticText(panel, label="HDF5 folder")
		sizer.Add(label_hdf5_folder, pos=(3, 0), flag=wx.LEFT | wx.TOP, border=10)

		self.field_hdf5 = wx.TextCtrl(panel, value="/usr/local/hdf5/bin/")
		sizer.Add(self.field_hdf5, pos=(3, 1), span=(1, 3), flag=wx.TOP | wx.EXPAND, border=5)

		button1 = BrowseFolderButton(panel, label="Browse...")
		button1.target = self.field_hdf5
		sizer.Add(button1, pos=(3, 4), flag=wx.TOP | wx.RIGHT, border=5)

		# Line 2
		label_input = wx.StaticText(panel, label="Input")
		sizer.Add(label_input, pos=(4, 0), flag=wx.LEFT | wx.TOP, border=10)

		self.field_input = wx.TextCtrl(panel, value="")
		sizer.Add(self.field_input, pos=(4, 1), span=(1, 3), flag=wx.TOP | wx.EXPAND, border=5)

		button1 = BrowseFolderButton(panel, label="Browse...")
		button1.target = self.field_input
		sizer.Add(button1, pos=(4, 4), flag=wx.TOP | wx.RIGHT, border=5)

		# Line 3
		label_output = wx.StaticText(panel, label="Output")
		sizer.Add(label_output, pos=(5, 0), flag=wx.LEFT | wx.TOP, border=10)

		self.field_output = wx.TextCtrl(panel, value="output.csv")
		sizer.Add(self.field_output, pos=(5, 1), span=(1, 3), flag=wx.TOP | wx.EXPAND, border=5)

		button1 = BrowseSaveButton(panel, label="Browse...")
		button1.target = self.field_output
		sizer.Add(button1, pos=(5, 4), flag=wx.TOP | wx.RIGHT, border=5)

		line2 = wx.StaticLine(panel)
		sizer.Add(line2, pos=(6, 0), span=(1, 5), flag=wx.EXPAND | wx.TOP | wx.BOTTOM, border=10)

		# BLOCK 3
		# #######
		button_cancel = wx.Button(panel, label="Cancel")
		button_cancel.Bind(wx.EVT_BUTTON, self.close_window)
		sizer.Add(button_cancel, pos=(7, 3), span=(1, 1), flag=wx.BOTTOM | wx.RIGHT, border=5)

		button_ok = wx.Button(panel, label="Ok")
		button_ok.Bind(wx.EVT_BUTTON, self.process)
		sizer.Add(button_ok, pos=(7, 4))

		sizer.AddGrowableCol(2)

		panel.SetSizer(sizer)

	def close_window(self, event):
		self.Destroy()

	def process(self, event):
		tz = self.field_timezone.GetValue()
		b = str(int(self.field_spin.GetValue()) * 1000)
		hdf5 = self.field_hdf5.GetValue()
		i = self.field_input.GetValue()
		o = self.field_output.GetValue()

		print " ".join(["anaconda", "./process.py", "-b", b, "-z", tz, "-f", hdf5, "-i", i, "-o", o])
		call(["anaconda", "./process.py", "-b", b, "-z", tz, "-f", hdf5, "-i", i, "-o", o])

if __name__ == '__main__':

	app = wx.App()
	Interface(None, title='Actual HDFS')
	app.MainLoop()
