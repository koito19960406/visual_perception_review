from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pdfkit
import time
import os
import dotenv

# # setup selenium
# options = webdriver.ChromeOptions()
# # options.add_argument("--headless")  # Ensuring the browser runs in headless mode
# driver = webdriver.Chrome(options=options)  # replace with your webdriver
url = "https://link-springer-com.libproxy1.nus.edu.sg/chapter/10.1007/978-3-031-21333-5_86"
# driver.get(url)

# # wait for the NUS button to appear and click it
# nus_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="btn_nus"]')))
# nus_button.click()

# # wait for the login form to appear
# username_field = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="userNameInput"]')))
# password_field = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="passwordInput"]')))

# # fill in the username and password
# dotenv.load_dotenv()
# USERNAME = os.getenv("NUS_USERNAME")
# PASSWORD = os.getenv("NUS_PASSWORD")
# username_field.clear()
# username_field.send_keys(USERNAME)  # replace with your username
# password_field.clear()
# password_field.send_keys(PASSWORD)  # replace with your password

# # submit the form
# submit_button = driver.find_element(By.XPATH, '//*[@id="submitButton"]')
# submit_button.click()

# # wait for the next page to load
# time.sleep(5)  # wait for a while for the page to load fully

# # get the source
# html = driver.page_source

# # Print all the cookies after logging in
# cookies = driver.get_cookies()
# for cookie in cookies:
#     print(cookie['name'], cookie['value'])

# # Don't forget to quit the driver after everything is done
# driver.quit()

# # Save HTML to a file (necessary because pdfkit does not accept cookies)
# with open('notebooks/target.html', 'w') as f:
#     f.write(html)

# # Convert HTML file to PDF
# with open('notebooks/target.html') as f:
#     pdfkit.from_file(f, 'notebooks/out.pdf')
# # Access the webpage and save it as a PDF
options = {
    'page-size': 'Letter',
    'margin-top': '0.75in',
    'margin-right': '0.75in',
    'margin-bottom': '0.75in',
    'margin-left': '0.75in',
    'encoding': "UTF-8",
    'zoom': '1.3',  # adjust this as needed
    'custom-header': [
        ('Accept-Encoding', 'gzip')
    ],
    'cookie': [
        ('ezproxyn', 'Y65w5AKFvQA2CWW'),
        ('ezproxyl', 'Y65w5AKFvQA2CWW'),
        ('ezproxy', 'Y65w5AKFvQA2CWW')
    ],
    'no-outline': None
}

r = pdfkit.PDFKit(url, 'url', options = options, verbose=True)
print(' '.join(r.command()))
# try running wkhtmltopdf to create PDF
output = r.to_pdf()
# save PDF to file
with open('notebooks/out.pdf', 'wb') as f:
    f.write(output)
