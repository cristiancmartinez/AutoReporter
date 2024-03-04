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
    df = pd.read_csv(fileName, index_col=False)
    df.columns = df.columns.str.lower()
    print(f"File read: {fileName}. Dimensions: {df.shape[1]} x {df.shape[0]}")
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
        elif gui.currentLayout == 'Import':
            answer = gui.handleImport(event, values)
            if answer and event == 'MERGE':
                df = handler.mergeDf(df,loadDataframe(answer))
                print(len(df))
            elif event == 'FORMAT':
                df = handler.formatDf(df)
            elif answer and event == 'SAVE':
                gui.window.close()
                handler.saveDf(df,answer)
                sg.popup_ok(f'File saved has been as {answer}')
                break
                
        elif gui.currentLayout == 'Report':
            startDate, endDate, filePath, title, author, client = gui.handleReport(event, values)
            if startDate and endDate and filePath:
                gui.window.close()
                visualiser.run(df, startDate, endDate, filePath, title, author, client)
                sg.popup_ok(f'File has been saved as {filePath}')
                break