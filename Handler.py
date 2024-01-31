import pandas as pd
import json
import os
import shutil

class Handler:
    detailsFile = "data/details.json"

    def __init__(self):
        self.loadConfiguration()

    def loadConfiguration(self):
        with open(self.detailsFile, 'r') as file:
            data = json.load(file)
            self.responseAgreed = data["SLAresponse"]
            self.resolutionAgreed = data["SLAresolution"]
            self.resolutionOpen = data["statusOpen"]
            self.resolutionClosed = data["statusClosed"]
            self.columnsToKeep = data["columns"]

    def loadDataframe(self,fileName):
        print("File read: ", fileName)
        df = pd.read_csv(fileName)
        df.columns = df.columns.str.lower()
        return df
    
    def filterClients(self,df:pd.DataFrame):
        stringRegex = r'^([A-Za-z]+)-\d+'
        clientsInDf = df['issue key'].str.extract(stringRegex)[0].unique()
        if len(clientsInDf == 1):
            print(f"Your dataframe contains tickets from {clientsInDf} only.")
            return df
        else:
            print(f"The clients in your dataframe are:\n {clientsInDf} \n")
            userIn = input("Which ones do you want to keep? Type 'ALL' or the client sufixes separated by commas")
            userPrefix = set(userIn.upper().split(','))
            if 'ALL' in userPrefix:
                return df
            else: #TODO Don't recognise weird inputs
                filteredDf = df[df['issue key'].str.extract(stringRegex)[0].isin(userPrefix)]
                print(filteredDf)
                return filteredDf
        
    def handleColumns(self,df:pd.DataFrame):
        # Remove custom field columns
        fieldPattern = 'custom field ('
        for column in df.columns:
            if fieldPattern in column:
                newColumns = column.replace(fieldPattern, '').rstrip(')')
                df.rename(columns={column: newColumns}, inplace=True)

        # Drop any unnecessary columns
        missing_columns = [col for col in self.columnsToKeep if col not in df.columns]
        if missing_columns:
            print(f"Error: The following columns are not present in the DataFrame: {missing_columns}")
        else:
            df.drop(columns=[col for col in df.columns if col not in self.columnsToKeep], inplace=True)

        #TODO Rename only if column exist
        df.rename(columns={"time to first response": "response time", "time to resolution": "resolution time"}, inplace=True)
        df = df.loc[:, ~df.columns.duplicated()] # type: ignore #TODO Remove warning
        return df
    
    def handleValues(self,df:pd.DataFrame):
        def convertToMinutes(row):
            print(row, type(row))
            if pd.notna(row) and isinstance(row,str) and ':' in row:
                return int(row.split(':')[0]) * 60 + int(row.split(':')[1])
            elif pd.notna(row) and isinstance(row,float):
                return int(row)
            else:
                print(f'{row} was not converted to minutes')
        
        def assignActuals(df:pd.DataFrame):
            for index, row in df.iterrows():
                resolution = row['resolution time']
                response = row['response time']
                resolutionTarget = int(self.resolutionAgreed.get(row['priority'], pd.NA))
                responseTarget = int(self.responseAgreed.get(row['priority'], pd.NA))
                if pd.notna(resolution) and resolution <= resolutionTarget: df.at[index,'actual resolution'] = resolutionTarget - resolution
                elif pd.notna(resolution) and resolution > resolutionTarget: df.at[index,'actual resolution'] = resolution
                else: pd.NA

                if pd.notna(response) and response <= responseTarget: df.at[index,'actual response'] = responseTarget - response
                elif pd.notna(response) and response > responseTarget: df.at[index,'actual response'] = response
                else: pd.NA
            return df
        
        def assignStatus(row):
            statusLower = str(row['status']).lower().strip()
            if statusLower in self.resolutionClosed:
                return 'Closed'
            elif statusLower in self.resolutionOpen:
                return 'Open'
            else:
                return 'Unknown'
            
        #TODO Make iterators consistent in all of them
        df['response time'] = df['response time'].apply(convertToMinutes)
        df['resolution time'] = df['resolution time'].apply(convertToMinutes)
        df['resolution'] = df.apply(assignStatus, axis=1)
        df['actual response'] = pd.NA
        df['actual resolution'] = pd.NA
        df = assignActuals(df)
        return df
    
    def handleFormat(self, df:pd.DataFrame):
        df['issue key'] = df['issue key'].astype('string')
        df['issue type'] = df['issue type'].astype('string')
        df['priority'] = df['priority'].astype('string')
        df['category'] = df['category'].astype('string')
        df['reporter'] = df['reporter'].astype('string')
        df['assignee'] = df['assignee'].astype('string')
        df['summary'] = df['summary'].astype('string')
        df['status'] = df['status'].astype('string')
        df['resolution'] = df['resolution'].astype('string')
        df['first time fix'] = df['first time fix'].fillna("Yes").astype('string')
        df["in scope"] = df["in scope"].fillna("Yes").astype('string')
        df['ticket source'] = df['ticket source'].astype('string')
        df['cost centre'] = df['cost centre'].astype('string')
        df['location'] = df['location'].astype('string')
        df['response time'] = pd.to_numeric(df['response time'], errors='coerce').astype('Int64')
        df['resolution time'] = pd.to_numeric(df['resolution time'], errors='coerce').astype('Int64')
        df['actual response'] = pd.to_numeric(df['actual response'], errors='coerce').astype('Int64')
        df['actual resolution'] = pd.to_numeric(df['actual resolution'], errors='coerce').astype('Int64')
        df['satisfaction rating'] = pd.to_numeric(df['satisfaction rating'], errors='coerce').astype('Int64')
        df['time spent'] = pd.to_numeric(df['time spent'], errors='coerce').astype('Int64')
        df['created'] = pd.to_datetime(df['created'],format="mixed")
        df['updated'] = pd.to_datetime(df['updated'],format="mixed")
        return df
    
    def formatDf(self, df:pd.DataFrame):
        df = self.filterClients(df)
        df = self.handleColumns(df)
        df = self.handleValues(df)
        df = self.handleFormat(df)
        print("Dataframe size: ", df.size,'\n')
        return df
    
    def mergeDf(self, existingDf: pd.DataFrame, newDf = None):
        if newDf == None:
            newDf = self.populateDf(pd.DataFrame())
        auxDf = pd.DataFrame()
        auxDf = pd.concat([existingDf, newDf])
        auxDf.drop_duplicates(subset="issue key", keep="first", inplace=True)
        return auxDf
    
    def populateDf(self, df: pd.DataFrame):
        df = self.loadDataframe(df)
        df = self.formatDf(df)
        while input("Do you want to add another dataframe? (y/n): \n").lower() == 'y':
            df = self.mergeDf(df)
            print(f"Df size {df.size}: {df.shape[0]} * {df.shape[1]}")
        return df
    
    def setOutputFile(self, df:pd.DataFrame): #TODO simplify this code
        stringRegex = r'^([A-Za-z]+)-\d+'
        clientsInDf = df['issue key'].str.extract(stringRegex)[0].unique()
        directory = 'dataset'
        subDir = [f for f in os.listdir(directory)]
        if len(clientsInDf) == 1:
            recommended = f'{clientsInDf[0].lower()}.csv'
            if recommended in subDir:
                print(f"There is a file named {recommended} at {directory}.")
                selection = input("1 to merge with existing file.\n2 to save with a different name.\n3 to overwrite the file\nAny other input to discard the dataframe")
                if selection == str(1):
                    auxDf = pd.read_csv(f'{directory}/{recommended}')
                    auxDf = self.formatDf(auxDf)
                    newDf = self.mergeDf(auxDf,df)
                    newDf.to_csv(f'{directory}/{recommended}',index=False, encoding="utf-8")
                elif selection == str(2):
                    name = f'{input("Type the name of the output file (Omit the file type)")}.csv'
                    df.to_csv(f'{directory}/{name}',index=False, encoding="utf-8")
                    print(f'New file at {directory}/{name} has been created')
                elif selection == str(3):
                    shutil.rmtree(f'{directory}/{recommended}')
                    os.makedirs(f'{directory}/{recommended}', exist_ok=True)
                else:
                    print(f"Dataframe has been discarded")
            else:
                print(f"No file named {recommended} was found at {directory}")
                selection = input(f"1 to create a new file named '{recommended}'\n2 to create a new file with a different name\nAny other input to discard the dataframe")
                if selection == str(1):
                    df.to_csv(f'{directory}/{recommended}',index=False, encoding="utf-8")
                    print(f'New file at {directory}/{recommended} has been created')
                elif selection == str(2):
                    name = f'{input("Type the name of the output file (Omit the file type)")}.csv'
                    df.to_csv(f'{directory}/{name}',index=False, encoding="utf-8")
                    print(f'New file at {directory}/{name} has been created')
                else:
                    print(f"Dataframe has been discarded")
        elif len(clientsInDf) > 1:
            print(f"Your dataframe contains data from {len(clientsInDf)} different clients")
            name = f'{input("Type the name of the output file (Omit the file type)")}.csv'
            df.to_csv(f'{directory}/{name}',index=False, encoding="utf-8")