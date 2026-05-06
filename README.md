# Selenium scrapper for CodeChef
## Install and Configure selenium with Chrome driver in Ubuntu
* Tested on Ubuntu 22.04-LTS
```
sudo apt install wkhtmltopdf
sudo apt install chromium-chromedriver
pip install selenium webdriver-manager bs4
pip install pdfkit
```
## Fetch Contests
* Run `python3 fetchContestQuestionTable.py`
	- Login with your credentials and press enter in the shell
	- This will extract table sources in the `data/`
* Check if there are some errors while extractions.
* Run `python3 parseContestTable.py`
	- This will extract the contents of table into `parsed_problems.csv`
* Run `python3 groupContestProblemCodes.py`
	- this will consolidate the Question IDs into `grouped_problems.csv`
* Run `python3 fetchQuestions.py`
	- this will place the convert the problem statements into PDF and place them in `contest/`
* To merge PDFs, you can use `gs -dBATCH -dNOPAUSE -q -sDEVICE=pdfwrite -sOutputFile=merged.pdf pdfs/*.pdf`

## Fetch Regular Excercises
* (If required) Open `Codechef Portal` and update the `CSVs/CodechefTopicURL.tsv` with latest URL of Topics, subtopics, and their base URLs from the course homepage.

* Run `python3 fetchURLofExcercises.py`
	- Login with your credentials and press enter in the shell
	- This will read tpoics and subtopics from `CSVs/CodechefTopicURL.tsv` and extract all URLS in the `CSVs/ProblemURL.tsv`

* Run `python3 fetchPracticeProblems.py`
	- Login with your credentials and press enter in the shell
	- This will extract problems in the `Excercise/` folder
## Extract Problem Name from `HTML`
* Consult help `bash extractProblemName.sh --help` 
* Run `bash extractProblemName.sh <FOLDERNAME>` to extract Problem Titles from a given folder.
* Run `bash extractProblemName.sh <TSV-FILENAME>` to extract Problem Titles from a given TSV file.

## Fetch evaluated results with Student submissions
* Provided we know the contestID, and numeric studentID (which can be obtained from the codeChef students portal also)
* Download the report shared by the CodeChef team in `TSV` format (Say the name is `CSVs/StudList-Full.tsv`)
* Check the Header section and update the `### INPUT TSV FILES SET FIELD NAMES` section with appropriate column name
* Filter out the section IDs based on group numbers (e.g. `awk 'NR==1 || /2C33|2C73|2C13|2C14/' CSVs/StudList-Full.tsv > CSVs/MyGroup.tsv `)
* Take this output file (`MyGroup.tsv`) as the input of next step.
```
 

## Fetch student submissions
* CodeChef uses a general URL for fetching student submission, `https://www.codechef.com/moderate/solutions/<CONTEST_ID>?sort_by=All&sorting_order=asc&language=All&status=All&pcode=<PROBLEM_ID>&handle=<STUDENT_ID>&Submit=GO`
Therefore, create a file (`CSVs/2C33URLS.tsv`) containing as following 	 

``` 2C33		
	DO NOT EDIT COL DATA CodechefURLs	
Roll	CodingProblem1	CodingProblem2
1024030451	https://www.codechef.com/moderate/solutions/NZJDQ?sort_by=All&sorting_order=asc&language=All&status=All&pcode=CHESSGM&handle=fkansal_be24&Submit=GO	https://www.codechef.com/moderate/solutions/NZJDQ?sort_by=All&sorting_order=asc&language=All&status=All&pcode=JBSQNCE&handle=fkansal_be24&Submit=GO
```
* ``` https://docs.google.com/spreadsheets/d/121Wy3ZUxFrfz5JplTIZKqFue7T9aOPTZg4kIrDOejZA/edit?gid=900185514#gid=900185514```
This tab is used for extracting URL from the actual submissions. CHange cell A1 values to get the URLs and download this file as CSV.

* ``` python3 fetchStudSubmission.py  --input CSVs/2C33URLS.tsv --output CSVs/2C33Codes.tsv ```
* ``` python3 fetchStudSubmission.py  --input CSVs/2C33URLS.tsv --output CSVs/2C33Codes.tsv --debug```

## Fetch Questionwise scores
* Use "https://www.codechef.com/manage/<ContestID>?tab=assessment_users" to download student assessment ID (last col)
* Fetch question wise analysis using 
```
python3 fetchStudAssessment.py   --input input_le2.tsv   --output output.tsv
```



