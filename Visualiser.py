import calendar
import json
import matplotlib.pyplot as plt
import pandas as pd
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas
from PIL import Image
from datetime import date

class Visualiser:
    detailsFile = 'tools/details.json'
    resourcesDirectory = 'resources'
    overviewDirectory = os.path.join(resourcesDirectory, 'general')
    pageCount = 1
    
    def __init__(self):
        self._loadConfiguration()

    def run(self, df:pd.DataFrame, startDate, endDate, outputFileName:str, fileTitle: str): #TODO: Add GUI to set the project author and client name
        self.fileTitle = fileTitle
        self.author = 'Freddy Loft'
        self.today = date.today().strftime('%d/%m/%y')
        self.startDateLong = startDate.strftime('%d/%m/%Y')
        self.endDateLong = endDate.strftime('%d/%m/%Y')
        self.startDateShort = startDate.strftime('%d/%m/%y')
        self.endDateShort = endDate.strftime('%d/%m/%y')
        df.columns = df.columns.str.lower()
        df['created'] = pd.to_datetime(df['created'],format='mixed')
        df['updated'] = pd.to_datetime(df['updated'],format='mixed')
        self.filteredDf = df[(df['created'] >= startDate) & (df['created'] <= endDate)]
        self.populateResources(df)
        self.generatePDF(outputFileName)

    def populateResources(self, df:pd.DataFrame):
        '''
        It creates all of the resources and place them in the correspondent directory.
        - Overview uses a dataframe that contains all tickets.
        - Priority uses a filtered dataframe, limited by the dates chosen when it was created.
        '''
        # OVERVIEW
        annualGraph = self._generateAnnualGraph(self._splitMonths(df))
        self._savePlt(annualGraph,self.overviewDirectory,'annualGraph')
        timeGraph = self._generateTimeGraph(df)
        self._savePlt(timeGraph,self.overviewDirectory,'timeGraph')
        openTickets = df[df['resolution'] == 'Open']
        self._generateTicketTable(openTickets, self.overviewDirectory, 'openTable', isOverview= True)

        # PRIORITY
        priorityDfs, pStatusList = self._splitPriorities(self.filteredDf)
        tags = ['Open', 'Closed', 'Unknown']
        for priority, label, status in zip(priorityDfs, self.priorityLabels, pStatusList):
            labelDir = os.path.join(self.resourcesDirectory,label)
            if not priority.empty:
                statusLabel = [f"{tag} ({count})" for tag, count in zip(tags, status)]
                statusPie = self._generatePie(plt, status, statusLabel)
                self._savePlt(statusPie, labelDir, 'statusPie')
                typesPie = self._generateTypesPie(priority)
                self._savePlt(typesPie, labelDir, 'typesPie')
                self._generateTicketTable(priority, labelDir, 'ticketTable', isOverview=False) if not priority.empty else print(f"No tickets to generate table {label}")
            else:
                print(f"No tickets to generate graph for {label}")

    def generatePDF(self, outputFileName:str):
        '''It creates the pdf canvas and stores it in the given outputFileName'''
        reportPDF = Canvas(f'{outputFileName}.pdf', pagesize=A4)

        # COVER SHEET
        imgSet = []
        imgSet.append(self._fetchImages('tools/logos',['theICEway.png','Topdeck.png']))
        reportPDF = self._populatePDF(reportPDF, imgSet, title= self.fileTitle, isCover=True)
        
        # OVERVIEW
        imgSet = []
        imgSet.append(self._fetchImages(self.overviewDirectory,['annualGraph.png','timeGraph.png']))
        tblImgs = self._fetchImages(self.overviewDirectory,conditionStr='Table')
        for tbl in tblImgs:
            imgSet.append([tbl])
        reportPDF = self._populatePDF(reportPDF, imgSet, title= 'MONTHLY TICKETS', isCover = False)
        
        # PRIORITY
        priorityDfs, _ = self._splitPriorities(self.filteredDf) #TODO: Change method to have a single return if wanted
        for priority, label in zip(priorityDfs, self.priorityLabels):
            if not priority.empty:
                imgSet = []
                labelDir = os.path.join(self.resourcesDirectory, label)
                imgSet.append(self._fetchImages(labelDir,['statusPie.png','typesPie.png']))
                tblImgs = self._fetchImages(labelDir,conditionStr='Table')
                for tbl in tblImgs:
                    imgSet.append([tbl]) # append table images separetely
                reportPDF = self._populatePDF(reportPDF, imgSet, title=f"{label} - {len(priority)} tickets", isCover = False)

        reportPDF.save()

# PRIVATE METHODS
    def _loadConfiguration(self):
        with open(self.detailsFile, 'r') as file:
            data = json.load(file)
            self.responseAgreed = data['SLAresponse']
            self.resolutionAgreed = data['SLAresolution']
            self.priorityLabels = data['priorityLabels']
            self.colorsICE = data['colorsICE']

    def _populatePDF(self, pdfCanvas:Canvas, imgSet:list, title: str, isCover: bool):
        '''
        It populates the @pdfCanvas using the images provided.
        @imgSet: It holds several sets of images. ImgSet are divided in pages, while imgList are on the same page.
        @yCoord: Signals the position of the title. Only use for the page cover, as the rest of titles will have a position by default  
        '''
        canvasSize = [pdfCanvas._pagesize[0], pdfCanvas._pagesize[1]]
        # COVER PAGE
        tempTitle = 'MANAGED SERVICE REPORT'
        if isCover:
            margins = [70, 50] # Controls the images padding
            xPad = 50 # Controls the text padding
            yPad = 20
            fontSize = 30
            yCoord = margins[1] + 3*fontSize + 2*yPad
            pdfCanvas.setFont('Helvetica', fontSize)
            titleDate = f"FROM {self.startDateShort} TO {self.endDateShort}"
            pdfCanvas.drawString(text= tempTitle, x= xPad, y= yCoord)
            yCoord = yCoord - yPad - fontSize
            pdfCanvas.drawString(text= titleDate, x= xPad, y= yCoord)
            yCoord = yCoord - yPad - fontSize
            pdfCanvas.drawString(text= self.author, x= xPad, y= yCoord)
            yCoord = canvasSize[1] - margins[1]
        else:
            margins = [30, 30]
            yPad = 30
            fontSize = 50
            yCoord = canvasSize[1] - margins[1] - fontSize
            pdfCanvas.setFont('Helvetica', fontSize)
            titleWidth = pdfCanvas.stringWidth(title)
            pdfCanvas.drawString(x= canvasSize[0]/2 - titleWidth/2, y= yCoord, text= title)

        # IMAGES
        for imgList in imgSet:
            for img in imgList:
                imgRatio = img.size[0] / img.size[1]
                imgWidth = canvasSize[0] - margins[0]
                imgHeight = imgWidth / imgRatio
                yCoord = yCoord - yPad - imgHeight
                xCoord = canvasSize[0]/2 - imgWidth/2
                pdfCanvas.drawInlineImage(img, x=xCoord, y=yCoord, width=imgWidth, height=imgHeight)

            # FOOTER
            if not isCover:
                yFooter = 30
                pdfCanvas.setFont('Helvetica', 12)
                todayWidth = pdfCanvas.stringWidth(self.today)
                pdfCanvas.drawString(x= margins[0], y= yFooter, text= self.author)
                pdfCanvas.drawString(x= canvasSize[0]/2, y= yFooter, text= str(self.pageCount))
                pdfCanvas.drawString(x= canvasSize[0] - margins[0] - todayWidth, y= yFooter, text= self.today)

            pdfCanvas.showPage()
            self.pageCount = self.pageCount + 1
            yCoord = canvasSize[1]
        return pdfCanvas

    def _splitPriorities(self, df:pd.DataFrame):
        '''It splits the dataframe provided into its priorities. It returns the dataframes holding tickets based on their priority and the count of each status in them'''
        priorityDfs = []
        pStatusList = []
        for label in self.priorityLabels:
            priorityDfs.append(df[df['priority'].isin([label])])
        for auxDf in priorityDfs:
            pStatusList.append([len(auxDf[auxDf['resolution'] == 'Open']), len(auxDf[auxDf['resolution'] == 'Closed']), len(auxDf[auxDf['resolution'] == 'Unknown'])])
        
        return priorityDfs, pStatusList

    def _splitMonths(self, df: pd.DataFrame):
        '''It returns a list containing 12 dataframes, each containing the tickets created in each month'''
        monthly_dfs = [df[df['created'].dt.month == month] for month in range(1, 13)]
        return monthly_dfs

    def _fetchImages(self, directory:str, fileNames = None, conditionStr = None):
        '''It opens the files located at the @inputDir that match the conditions.
        @fileNames: It searches for exact matches. It accepts lists of names.
        @conditionStr: It searches for files containing the conditionStr in its name.
        '''
        imgs = []
        if fileNames:
            files = fileNames
        elif conditionStr:
            files = [f for f in os.listdir(directory) if conditionStr.lower() in f.lower()]
        else:
            print('There are no images to fetch')
            files = []

        for imgName in files:
            fileName = os.path.join(directory, imgName)
            imgs.append(Image.open(fileName))
        return imgs
    
    def _savePlt(self,plt, directoryName:str, fileName:str):
        '''It saves the figure as a PNG file in the directory provided. This directory must be inside the 'resources' directory'''
        pngFilepath = os.path.join(directoryName, fileName)
        plt.savefig(pngFilepath, bbox_inches='tight')
        plt.figure()  # Clear current figure
        print(f"The graph {fileName} has been succesfully saved as {pngFilepath}")
        
    def _generatePie(self, plt, values:list, labels:list):
        if len(values)>0:
            values = values[:6]
            plt.pie(values, colors = self.colorsICE,startangle=90, counterclock=False)
            plt.legend(labels, bbox_to_anchor=(1, 1), loc='upper left')
            return plt
    
    def _generateAnnualGraph(self, dfsList:list[pd.DataFrame]):
        closedDf, openDf, auxDf, unknownDf = [], [], [], []
        months = calendar.month_abbr[1:]
        for monthDf in dfsList:
            closedTickets = len(monthDf[monthDf['resolution'] == 'Closed'])
            openTickets = len(monthDf[monthDf['resolution'] == 'Open'])
            closedDf.append(closedTickets)
            openDf.append(openTickets)
            auxDf.append(closedTickets + openTickets)
            unknownDf.append(len(monthDf[monthDf['resolution'] == 'Unknown']))
        plt.bar(months, closedDf, color= self.colorsICE[1], label= f"Closed ({sum(closedDf)})")
        plt.bar(months, openDf, bottom= closedDf, color= self.colorsICE[0], label=f"Open ({sum(openDf)})")
        plt.bar(months, unknownDf, bottom= auxDf, color= self.colorsICE[2], label= f"Unknown ({sum(unknownDf)})")
        plt.ylabel('N tickets')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        return plt

    def _generateTicketTable(self, df: pd.DataFrame, directoryName:str, fileName:str, isOverview: bool):
        def colorTable(df):
            colors = []
            for index, row in df.iterrows():
                if pd.isna(row['actual resolution']) or row['actual resolution'] <= int(self.resolutionAgreed.get(row['priority'])):
                    colors.append(['#ADDFFF','#FFFFFF','#FFFFFF','#FFFFFF','#FFFFFF','#FFFFFF','#FFFFFF','#FFFFFF'])
                else:
                    colors.append(['#FCD299','#FFFFFF','#FFFFFF','#FFFFFF','#FFFFFF','#FFFFFF','#FFFFFF','#FFFFFF'])
            return colors
        
        if isOverview:
            cols = ['issue key', 'summary', 'priority', 'created', 'updated', 'first time fix', 'in scope', 'ticket source']
        else:
            cols = ['issue key', 'summary', 'resolution', 'created','updated',  'first time fix', 'in scope','ticket source']
        colLabels = cols.copy()
        colLabels[5] = '1st fix'
        colLabels[7] = 'source'
        colWidths = [0.1, 0.4, 0.08, 0.08, 0.07, 0.07, 0.07, 0.09]
        length = 100
        limits = [0, length]
        fontSize = 14
        index = 1

        df.loc[:,'summary'] = df.loc[:,'summary'].apply(lambda x: x[:50] if isinstance(x, str) else x)
        df.loc[:,'ticket source'] = df.loc[:,'ticket source'].apply(lambda x: x[:10] if isinstance(x, str) else x)

        while limits[0] <= len(df):
            auxDf = df[limits[0]:limits[1]]
            auxDf.loc[:, 'created'] = pd.to_datetime(auxDf['created']).dt.strftime('%d/%m/%y')
            auxDf.loc[:, 'updated'] = pd.to_datetime(auxDf['updated']).dt.strftime('%d/%m/%y')
            limits[0] = limits[0] + length
            limits[1] = limits[1] + length
            colorTab = colorTable(auxDf)

            _, ax = plt.subplots(figsize=(16, 5))
            ax.axis('off')
            table = ax.table(cellText=auxDf[cols].values, colLabels=colLabels, loc='upper center', cellLoc='left', fontsize=fontSize, colWidths=colWidths, cellColours=colorTab)
            table.auto_set_font_size(False)
            self._savePlt(plt, directoryName, f"{fileName}{index}")
            index = index + 1

    def _generateTypesPie(self, df):
        _, axs = plt.subplots(1, 2, figsize=(12, 6))
        issues = df['issue type'].value_counts()
        sources = df['ticket source'].value_counts()
        self._generatePie(axs[0], issues.values, [f"{issue} ({count})" for issue, count in zip(issues.index, issues.values)])
        self._generatePie(axs[1], sources.values, [f"{source} ({count})" for source, count in zip(sources.index, sources.values)])
        plt.tight_layout()
        return plt
    
    def _generateTimeGraph(self, df:pd.DataFrame):
        def calculateAvg(df:pd.DataFrame, colName:str):
            return int(df[colName].sum()) / len(df) if not df.empty else 0 

        def calculatePct(df:pd.DataFrame, colName:str, priorityLabel:str):
            avg = calculateAvg(df,colName)
            if colName == 'actual response':
                timeLimit = int(self.responseAgreed.get(priorityLabel))
                return avg / timeLimit if avg < timeLimit else 1
            elif colName == 'actual resolution':
                timeLimit = int(self.resolutionAgreed.get(priorityLabel))
                return avg / timeLimit if avg < timeLimit else 1
            else: return 0

        resolutionsAvg, resolutionPcts, responseAvg, responsePcts, firstFixPcts = [], [], [], [], []
        priorityDfs, _ = self._splitPriorities(df)

        for priority, label in zip(priorityDfs, self.priorityLabels):
            resolutionsAvg.append(int(calculateAvg(priority,'actual resolution')))
            resolutionPcts.append(calculatePct(priority,'actual resolution',label))
            responseAvg.append(calculateAvg(priority,'actual response'))
            responsePcts.append(calculatePct(priority,'actual response',label))
            firstFixPcts.append((priority['first time fix'] == 'Yes').sum() / len(priority))

        firstFixedResolutions = [round(res * ffr , 2) for res, ffr in zip(resolutionPcts, firstFixPcts)]
        firstFixedResolutionsOpposite = [round(res - ffr, 2) for res, ffr in zip(resolutionPcts, firstFixedResolutions)]

        print(f'%:{resolutionPcts}, FFResolution:{firstFixedResolutions}, FFROpposite:{firstFixedResolutionsOpposite}, avgResolutions:{resolutionsAvg}')

        resolutionBar1 = plt.bar(self.priorityLabels, firstFixedResolutions, color=self.colorsICE[1], label='Fixed at first')
        resolutionBar2 = plt.bar(self.priorityLabels, firstFixedResolutionsOpposite, bottom=firstFixedResolutions, color=self.colorsICE[0], label='Not fixed at first')
        plt.scatter(self.priorityLabels, responsePcts, color='black')
        plt.plot(self.priorityLabels, responsePcts, color='black', label='Response time')
        plt.ylabel('Time taken from targets')
        plt.gca().yaxis.set_major_formatter('{x:.0%}') # Set Y axis to percentage format
        plt.ylim(0, 1)  # Set Y axis limits
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

        for i, (priority, (rect1, rect2)) in enumerate(zip(self.priorityLabels, zip(resolutionBar1, resolutionBar2))):
            height = rect1.get_height() + rect2.get_height()
            plt.text(rect1.get_x() + rect1.get_width() / 2, height, f'{resolutionsAvg[i]} / {self.resolutionAgreed.get(priority)}', ha='center', va='bottom')
        #plt.text(rect1.get_x() + rect1.get_width() / 2, height, f'AVG:{resolutionsAvg[i]} min', ha='center', va='bottom')
        return plt

    def _generateSatisfactionGraph(self, df:pd.DataFrame): # TODO to complete
        df['satisfaction rating'] = pd.to_numeric(df['satisfaction rating'], errors='coerce')
        reviews = df['satisfaction rating'].value_counts()
        reviewsAvg = round(reviews.sum() / len(reviews),2)
        reviewsRate= round(len(reviews) / (df['resolution'] == 'Closed').sum(),2)
        print(reviewsAvg,reviewsRate)