from selenium.webdriver.common.by import By

def wait_for_manual_login(driver):
    driver.get("https://www.codechef.com/")
    print("\n🔐 Login manually...")
    input("👉 Press ENTER after login...")