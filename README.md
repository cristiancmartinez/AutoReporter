# AUTOREPORTER

## Description

Autoreporter streamlines the process of generating client reports by consolidating relevant information into a single PDF file. It offers two primary functionalities:

- Data Import and Cleaning: Import data from a CSV file, clean it by removing noise and inconsistencies, and export it into a standardized CSV format.
- Report Generation: Create a comprehensive PDF report from the cleaned CSV file.

## How to use

The program operates in three stages:

### Fetch the data

Retrieve ticket information from JIRA using the "Export - Export CSV (all fields)" function. Ensure that no column filters are applied to prevent issues with data consistency. Note that opening the CSV file with Excel may alter the format and impede Autoreporter's functionality.

### Import the data
Use this mode to merge multiple reports and perform data cleaning. The format function eliminates unused columns, standardizes values, and resolves inconsistencies.

- To merge files, ensure they have been pre-formatted using the format functionality. This feature proves beneficial for generating reports spanning multiple companies or compiling past reports.

### Generate Report
Generate a PDF file containing summary graphs of tickets raised by a specified company within a designated timeframe.

#### Overview:
Generate graphs based on the entire year, utilizing all data provided in the file regardless of the specified "FROM" and "TO" dates.
The ticket table displays all open tickets in the dataframe, irrespective of the month.
#### Priorities:
Generate graphs based on the selected timeframe to represent monthly trends rather than specific ongoing issues.
The ticket table displays all tickets created within the specified timeframe.

## Colour scheme

Throughout the report, 2 colours are used on th ticket tables. Orange represents that a ticket has spent longer than the time specified by the Resolution Agreement. On the other hand, blue represents that the ticket was within the time stated in the agreement.

## Authors

- Cristian Martinez - camilocmf77@gmail.com

