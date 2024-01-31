import pandas as pd
import json

class Handler:
    detailsFile = "tools/details.json"

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
    
    def formatDf(self, df:pd.DataFrame):
        df = self._handleColumns(df)
        df = self._handleValues(df)
        df = self._handleFormat(df)
        print(f"Dataframe size after formatting: {df.size}, len: {len(df)}")
        return df
    
    def mergeDf(self, existingDf: pd.DataFrame, newDf = None):
        if newDf == None:
            newDf = self.populateDf(pd.DataFrame())
        auxDf = pd.concat([existingDf, newDf])
        auxDf.drop_duplicates(subset="issue key", keep="first", inplace=True)
        return auxDf
    
    def saveDf(self, df:pd.DataFrame, outputFileName:str):
        df.to_csv(f"{outputFileName}.csv")
        print(f"File was saved at {outputFileName}.csv")
    
    def _handleColumns(self,df:pd.DataFrame):
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
    
    def _handleValues(self,df:pd.DataFrame):
        def convertToMinutes(row):
            if pd.notna(row) and isinstance(row,str) and ':' in row:
                return int(row.split(':')[0]) * 60 + int(row.split(':')[1])
            elif pd.notna(row) and isinstance(row,float):
                return int(row)
        
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
    
    def _handleFormat(self, df:pd.DataFrame):
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
    
    
