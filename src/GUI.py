import PySimpleGUI as sg
import json
from datetime import datetime as dt

class GUI:
    currentLayout = None
    errorDate = "Invalid date format. Please enter valid dates."
    errorFile = "Invalid file path. Please provide a valid file."
    detailsFile = 'tools/details.json'
    noneList = None, None, None, None, None, None, None

    def __init__(self):
        sg.theme('SystemDefault')
        self.currentLayout = 'Main'
        self.window = sg.Window('Main', self._mainLayout(), element_justification='c', finalize=True)
        
    def handleEvent(self, event, values):
        if self.currentLayout == 'Main':
            filePath = values.get('FILEPATH', '')
            if filePath:
                if event == 'IMPORT DATA':
                    self.changeLayout('Import', self._import1Layout())
                elif event == 'GENERATE REPORT':
                    self.changeLayout('Report', self._report1Layout())
                return filePath
            else: sg.popup_no_buttons(self.errorFile)
            
    def handleImport(self, event, values):
        if event == 'MERGE':
            filePath = values.get('FILEPATHMERGE')
            return filePath if filePath else sg.popup_no_buttons(self.errorFile)
        if event == 'SAVE':
            outputFile = values.get('FILEPATHOUTPUT')
            return outputFile if outputFile else sg.popup_no_buttons(self.errorFile)

    def handleReport(self, event, values):
        if event != 'SAVE':
            return self.noneList
        
        startingDate = f"{values.get('DAY1')}/{values.get('MONTH1')}/{values.get('YEAR1')}"
        endDate = f"{values.get('DAY2')}/{values.get('MONTH2')}/{values.get('YEAR2')}"
        filepath = values.get('FILEPATH')
        title = values.get('TITLE')
        author = values.get('AUTHOR')
        client = values.get('CLIENT')
        checkBox = values.get('CHECK')
        try:
            startingDate = dt.strptime(startingDate, '%d/%m/%Y')
            endDate = dt.strptime(endDate, '%d/%m/%Y')
        except ValueError:
            sg.popup_no_buttons(self.errorDate)
            return self.noneList
        if not filepath:
            sg.popup_no_buttons(self.errorFile)
            return self.noneList
        elif not title:
            sg.popup_no_buttons('Please provide a title')
            return self.noneList
        elif not author:
            sg.popup_no_buttons('Please provide an author')
            return self.noneList
        elif not client:
            sg.popup_no_buttons('Please select a client')
            return self.noneList
        else:
            return startingDate, endDate, filepath, title, author, client, checkBox

    def changeLayout(self, title:str, layout:list):
        self.window.close()
        self.window = sg.Window(title, layout, element_justification='c', finalize=True)
        self.currentLayout = title

    def _mainLayout(self):
        return [
            [sg.Text('Please select a file to start')],
            [sg.FileBrowse(button_text='BROWSE', target='FILEPATH', size=(50,1))],
            [sg.InputText(key='FILEPATH', size=(50, 1), visible= False)],
            [sg.Text('Please select an action')],
            [sg.Button('IMPORT DATA', size=(23, 1)), sg.Button('GENERATE REPORT', size=(23, 1))]
        ]

    def _import1Layout(self):
        return [
            [sg.Text('Add additional dataframes')],
            [sg.FileBrowse(button_text='BROWSE', target='FILEPATHMERGE', size=(40, 1))],
            [sg.InputText(key='FILEPATHMERGE', size=(32, 1)), sg.Button('MERGE', size=(10, 1))],
            [sg.Text('Format dataframe')],
            [sg.Button('FORMAT', size=(40, 1))],
            [sg.InputText(key='FILEPATHOUTPUT', size=(1, 1), visible=False)],
            [sg.FileSaveAs(button_text='SELECT OUTPUT',target='FILEPATHOUTPUT', size=(28, 1)),sg.Button('SAVE', size=(10, 1))]
        ]

    def _report1Layout(self):
        today = dt.today()
        days = [i for i in range(1, 32)]
        ds1 = sg.Spin(days, readonly=True, size=5, enable_events=True, key='DAY1')
        ds2 = sg.Spin(days, initial_value=str(today.day), readonly=True, size=5, enable_events=True, key='DAY2')
        months = [i for i in range(1, 13)]
        ms1 = sg.Spin(months, readonly=True, size=5, enable_events=True, key='MONTH1')
        ms2 = sg.Spin(months, initial_value=str(today.month), readonly=True, size=5, enable_events=True, key='MONTH2')
        years = [i for i in range(today.year-3, today.year+1)]
        ys1 = sg.Spin(years, initial_value=str(today.year), readonly=True, size=15, enable_events=True, key='YEAR1')
        ys2 = sg.Spin(years, initial_value=str(today.year), readonly=True, size=15, enable_events=True, key='YEAR2')
        with open(self.detailsFile, 'r') as file:
            data = json.load(file)
            clients = data['clients']

        return [
            [sg.Text('Title   '), sg.InputText(key='TITLE', default_text= 'MANAGED SERVICE REPORT', size=(30, 1))],
            [sg.Text('Author'), sg.InputText(key='AUTHOR', default_text= 'Freddy Loft', size=(30, 1))],
            [sg.Text('Client'), sg.Combo(clients, enable_events= True, key= 'CLIENT', size =(28,1))],
            [sg.Text('Select a start date')],
            [ds1, ms1, ys1],
            [sg.Text('Select an end date')],
            [ds2, ms2, ys2],
            [sg.Text('Select the output file')],
            [sg.FileSaveAs(target='FILEPATH', button_text='SELECT OUTPUT', size=(28, 1)),sg.Button('SAVE', size=(10, 1))],
            [sg.Checkbox('Do you want to save the formatted file?', key = 'CHECK',size=(30,1), default=False)],
            [sg.InputText(key='FILEPATH', size=(1, 1), visible=False)]
        ]