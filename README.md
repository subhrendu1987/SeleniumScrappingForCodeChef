# Selenium scrapper for CodeChef
## Install and Configure selenium
```
pip install selenium webdriver-manager bs4
#export MOZ_ENABLE_WAYLAND=0
#export DISPLAY=:0
```
## Run code
* Run `python3 fetchQuestionTable.py`
	- Login with your credentials and press enter in the shell
	- This will extract table sources in the `data/`
* Check if there are some errors while extractions.
* Run `python3 parseTable.py`
	- This will extract the contents of table into `parsed_problems.csv`
