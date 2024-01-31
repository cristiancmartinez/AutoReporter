import calendar
import json
import matplotlib.pyplot as plt
import pandas as pd
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas
from PIL import Image

class Visualiser:
    logoFile = "tools/theICEwayLogo.png"
    detailsFile = "tools/details.json"
    resourcesDirectory = 'resources'
    overviewDirectory = 'general'
    
    def __init__(self):
        self._loadConfiguration()

    def run(self, df:pd.DataFrame, startDate, endDate, outputFileName:str):
        df.columns = df.columns.str.lower()
        df['created'] = pd.to_datetime(df['created'],format="mixed")
        df['updated'] = pd.to_datetime(df['updated'],format="mixed")
        self.filteredDf = df[(df['created'] >= startDate) & (df['created'] <= endDate)]
        print(f"From {startDate} to {endDate}. Len: {len(self.filteredDf)}")
        self.populateResources(df)
        self.generatePDF(outputFileName)

    def populateResources(self, df:pd.DataFrame):
        '''It creates the resources (images)'''
        # OVERVIEW (full dataframe)
        annualGraph = self._generateAnnualGraph(self._splitMonths(df))
        self._savePlt(annualGraph,self.overviewDirectory,'annualGraph')

        timeGraph = self._generateTimeGraph(df)
        self._savePlt(timeGraph,self.overviewDirectory,'timeGraph')

        openTickets = df[df['resolution'] == 'Open']
        self._generateTicketTable(openTickets, self.overviewDirectory, 'openTable')

        # PRIORITY (filtered dataframe)
        priorityDfs, pStatusList = self._splitPriorities(self.filteredDf)
        for priority, label, status, in zip(priorityDfs, self.priorityLabels, pStatusList):
            print(label)
            if not priority.empty:
                statusPie = self._generatePie(plt, status, self.statusLabels)
                self._savePlt(statusPie, label, 'statusPie')

                typesPie = self._generateTypesPie(priority)
                self._savePlt(typesPie, label, 'typesPie')

                notOnTime = priority[priority['actual resolution'] > int(self.resolutionAgreed.get(label))]
                others = priority[(priority['actual resolution'] <= int(self.resolutionAgreed.get(label))) | (priority['actual resolution'].isna())]
                print(f'{len(priority)}. Not on time: {len(notOnTime)}. Others: {len(others)}')
                
                self._generateTicketTable(notOnTime, label, 'breachTable') if not notOnTime.empty else print("No tickets that breach agreement")
                self._generateTicketTable(others, label, 'regularTable') if not others.empty else print("No tickets that meet the agreement")
            else:
                print("No tickets to display graph for", label)

    def generatePDF(self, outputFileName:str):
        reportPDF = Canvas(f'{outputFileName}.pdf', pagesize=A4)
        
        # COVER SHEET
        imgSet = []
        imgSet.append([Image.open(self.logoFile)])
        reportPDF = self._populatePDF(reportPDF, imgSet)
        
        # OVERVIEW
        imgSet = []
        imgSet.append(self._fetchImages(self.overviewDirectory,['annualGraph.png','timeGraph.png']))
        tblImgs = self._fetchImages(self.overviewDirectory,conditionStr='Table')
        for tbl in tblImgs:
            imgSet.append([tbl]) # append table images separetely
        reportPDF = self._populatePDF(reportPDF, imgSet)
        
        # PRIORITY
        priorityDfs, _ = self._splitPriorities(self.filteredDf) #TODO: Change method to have a single return if wanted
        for priority, label in zip(priorityDfs,self.priorityLabels):
            if not priority.empty:
                imgSet = []
                imgSet.append(self._fetchImages(label,['statusPie.png','typesPie.png']))
                tblImgs = self._fetchImages(label,conditionStr='Table')
                for tbl in tblImgs:
                    imgSet.append([tbl]) # append table images separetely
                reportPDF = self._populatePDF(reportPDF, imgSet, title=label)

        reportPDF.save()

# PRIVATE METHODS

    def _loadConfiguration(self):
        with open(self.detailsFile, 'r') as file:
            data = json.load(file)
            self.responseAgreed = data["SLAresponse"]
            self.resolutionAgreed = data["SLAresolution"]
            self.priorityLabels = data["priorityLabels"]
            self.statusLabels = data["statusLabels"]
            self.colorsICE = data["colorsICE"]
        
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

    def _fetchImages(self, inputDir:str, fileNames = None, conditionStr = None):
        '''It opens the files provided and opens either the files provided in fileNames, or the ones that match the conditionStr'''
        imgs = []
        files = list[str]
        dirName = os.path.join(self.resourcesDirectory,inputDir)
        if fileNames != None:
            files = fileNames
        elif conditionStr != None:
            files = [f for f in os.listdir(dirName) if conditionStr.lower() in f.lower()]
        else:
            print("There are no images to fetch")
            files = []

        for imgName in files:
            fileName = os.path.join(dirName,imgName)
            imgs.append(Image.open(fileName))
        return imgs

    def _populatePDF(self, pdfCanvas:Canvas, imgSet:list, title = None, margins = None):
        '''It populates the @pdfCanvas using @imgSet. Each set of @imgSet will be attached in separate pages, while each subset will be together.'''
        canvasSize = [pdfCanvas._pagesize[0], pdfCanvas._pagesize[1]]
        if margins == None: margins = [40,40]
        yCoord = canvasSize[1] - margins[1] # Set at the top

        if title != None:
            fontSize = 50
            pdfCanvas.setFont("Helvetica", 50, fontSize)
            titleWidth = pdfCanvas.stringWidth(title, "Helvetica", fontSize)
            pdfCanvas.drawString(canvasSize[0]/2 - titleWidth/2 , canvasSize[1] - 70,title)
        
        for imgList in imgSet:
            yCoord = yCoord - margins[1]
            for img in imgList:
                imgRatio = canvasSize[0] / img.size[0]
                imgWidth = canvasSize[0] - margins[0]
                imgHeight = (img.size[1] - margins[1]) * imgRatio
                yCoord = yCoord - imgHeight
                xCoord = canvasSize[0]/2 - imgWidth/2
                pdfCanvas.drawInlineImage(img, x=xCoord, y=yCoord, width=imgWidth, height=imgHeight)
                
            # New page
            pdfCanvas.showPage()
            yCoord = canvasSize[1] - margins[1]
        return pdfCanvas
    
    def _savePlt(self,plt, directoryName:str, fileName:str):
        '''It saves the figure as a PNG file in the directory provided. This directory must be inside the 'resources' directory'''
        pngFilepath = os.path.join(self.resourcesDirectory,directoryName, fileName)
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
        closedDf = []
        openDf = []
        months = calendar.month_abbr[1:]
        for monthDf in dfsList:
            closedDf.append(len(monthDf[monthDf['resolution'] == 'Closed']))
            openDf.append(len(monthDf[monthDf['resolution'] != 'Closed']))
        plt.bar(months,closedDf,color=self.colorsICE[1], label="Closed")
        plt.bar(months,openDf, bottom=closedDf,color=self.colorsICE[0], label="Open")
        plt.ylabel('N tickets')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        return plt

    def _generateTicketTable(self, df: pd.DataFrame, directoryName:str, fileName:str):
        df.loc[:, 'created'] = df['created'].dt.date
        df.loc[:, 'updated'] = df['updated'].dt.date
        length = 100
        limits = [0, length]
        fontSize = 14
        cols = ['issue key', 'summary', 'created','updated', 'resolution', 'first time fix', 'in scope','ticket source']
        colWidths = [0.07, 0.4, 0.08 ,0.08 , 0.06, 0.06, 0.05, 0.08]
        index = 1
        while limits[0] <= len(df):
            auxDf = df[limits[0]:limits[1]]
            limits[0] = limits[0] + length
            limits[1] = limits[1] + length

            # Create a table for the current slice of data
            fig, ax = plt.subplots(figsize=(20, 5))
            ax.axis('off')
        
            table = ax.table(cellText=auxDf[cols].values, colLabels=auxDf[cols].columns, loc='center', cellLoc='left', fontsize=fontSize, colWidths=colWidths)
            table.auto_set_font_size(False)
            table.scale(1, 1)
            self._savePlt(plt, directoryName, f"{fileName}{index}")
            index = index + 1

    def _generateTypesPie(self, df):
        fig, axs = plt.subplots(1,2, figsize=(12, 6))
        issues = df['issue type'].value_counts()
        sources = df['ticket source'].value_counts()
        self._generatePie(axs[0],issues.values,issues.index)
        self._generatePie(axs[1],sources.values,sources.index)
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
        priorityDfs, holder = self._splitPriorities(df)

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
        plt.plot(self.priorityLabels,responsePcts,color='black', label='Response time' )
        plt.ylabel('Time taken from targets')
        plt.gca().yaxis.set_major_formatter('{x:.0%}') # Set Y axis to percentage format
        plt.ylim(0, 1)  # Set y-axis limits from 0% to 100%
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

        for i, (rect1, rect2) in enumerate(zip(resolutionBar1, resolutionBar2)):
            height = rect1.get_height() + rect2.get_height()
            plt.text(rect1.get_x() + rect1.get_width() / 2, height, f'AVG:{resolutionsAvg[i]} min', ha='center', va='bottom')
        
        return plt

    def _generateSatisfactionGraph(self, df:pd.DataFrame): # TODO to complete
        df['satisfaction rating'] = pd.to_numeric(df['satisfaction rating'], errors='coerce')
        reviews = df['satisfaction rating'].value_counts()
        reviewsAvg = round(reviews.sum() / len(reviews),2)
        reviewsRate= round(len(reviews) / (df['resolution'] == 'Closed').sum(),2)