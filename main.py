import Handler
import GUI
import PySimpleGUI as sg
import pandas as pd
import os
import shutil
import Visualiser

def clearResources():
    subDir = [f for f in os.listdir('resources')]
    for directory in subDir:
        fileName = f'{'resources'}/{directory}'
        shutil.rmtree(fileName)
        os.makedirs(fileName, exist_ok=True)

def loadDataframe(fileName):
    print("File read: ", fileName)
    df = pd.read_csv(fileName, index_col=False)
    df.columns = df.columns.str.lower()
    return df

clearResources()
gui = GUI.GUI()
handler = Handler.Handler()
visualiser = Visualiser.Visualiser()

while gui.window:
    event, values = gui.window.read() # type: ignore
    if event == sg.WIN_CLOSED:
        gui.window.close()
        break
    else:
        if gui.currentLayout == 'Main':
            filePath = gui.handleEvent(event, values)
            if filePath:
                df = loadDataframe(filePath)
                print(len(df))
        elif gui.currentLayout == 'Import':
            answer = gui.handleImport(event,values)
            if answer and event == 'MERGE':
                df = handler.mergeDf(df,loadDataframe(answer))
                print(len(df))
            elif event == 'FORMAT':
                df = handler.formatDf(df)
            elif answer and event == 'SAVE':
                handler.saveDf(df,answer)
                print('File saved as', answer)
        elif gui.currentLayout == 'Report':
            startDate, endDate, filePath = gui.handleReport(event, values)
            if startDate and endDate and filePath:
                visualiser.run(df, startDate, endDate, filePath)
                gui.window.close()
                break