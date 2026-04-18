# Selenium scrapper for CodeChef
## Install and Configure selenium with Chrome driver in Ubuntu
* Tested on Ubuntu 22.04-LTS
```
sudo apt install wkhtmltopdf
sudo apt install chromium-chromedriver
pip install selenium webdriver-manager bs4
pip install pdfkit
```
## Fetch Assesments
* Run `python3 fetchQuestionTable.py`
	- Login with your credentials and press enter in the shell
	- This will extract table sources in the `data/`
* Check if there are some errors while extractions.
* Run `python3 parseTable.py`
	- This will extract the contents of table into `parsed_problems.csv`
* Run `python3 groupProblemCodes.py`
	- this will consolidate the Question IDs into `grouped_problems.csv`
* Run `python3 fetchQuestions.py`
	- this will place the convert the problem statements into PDF and place them in `problems/`

## Fetch Regular Excercises
* (If required) Open `Codechef Portal` and update the `CSVs/CodechefTopicURL.tsv` with latest URL of Topics, subtopics, and their base URLs from the course homepage.

* Run `python3 fetchURLofExcercises.py`
	- Login with your credentials and press enter in the shell
	- This will read tpoics and subtopics from `CSVs/CodechefTopicURL.tsv` and extract all URLS in the `CSVs/ProblemURL.tsv`

* Run `python3 fetchPracticeProblems.py`
	- Login with your credentials and press enter in the shell
	- This will extract problems in the `Excercise/` folder
## Extract Problem Name from `HTML`
* Run `bash extractProblemName.sh <FOLDERNAME>` to extract Problem Title
