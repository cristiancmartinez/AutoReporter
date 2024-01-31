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