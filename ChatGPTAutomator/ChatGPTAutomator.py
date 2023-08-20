from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import chromedriver_autoinstaller
import time
import socket
import threading
import os
import sys
import ssl

class ChatGPTAutomator:

    def __init__(self, wait_sec=20):
        """
        :param wait_sec: waiting for chatgpt response time
        """ 
        ssl._create_default_https_context = ssl._create_unverified_context
        self.chrome_path = self.get_chrome_path()
        self.chrome_driver_path = chromedriver_autoinstaller.install()

        self.wait_sec = wait_sec

        url = "https://chat.openai.com"
        free_port = self.find_available_port()
        self.start_remote_chrome(free_port, url)
        self.wait_for_human_verification()
        self.driver = self.setup_webdriver(free_port)
        self.driver.get(url)

    def get_chrome_path(self):
        platform = sys.platform
        
        if platform == "win32":
            # Usually located at this path on Windows
            chrome_path = "C:\\Program\ Files\ (x86)\\Google\\Chrome\\Application\\chrome.exe"
        elif platform == "darwin":
            # Usually located at this path on macOS
            chrome_path = "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome"
        else:
            # On Linux, 'google-chrome' is usually available in the PATH.
            chrome_path = "google-chrome"
        
        return chrome_path

    def find_available_port(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return s.getsockname()[1]

    def start_remote_chrome(self, port, url):
        def open_chrome():
            chrome_cmd = f"{self.chrome_path} --remote-debugging-port={port} --user-data-dir=remote-profile {url}"
            os.system(chrome_cmd)

        chrome_thread = threading.Thread(target=open_chrome)
        chrome_thread.start()

    def setup_webdriver(self, port):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
        driver = webdriver.Chrome(options=chrome_options)
        return driver

    def send_prompt_to_chatgpt(self, prompt):
        input_box = self.driver.find_element(by=By.CSS_SELECTOR, value="form textarea")
        input_btn = self.driver.find_element(by=By.CSS_SELECTOR, value="form textarea+button")
        self.driver.execute_script(f"arguments[0].value = '{prompt}';", input_box)
        input_box.send_keys(Keys.ENTER)
        input_btn.click()
        time.sleep(self.wait_sec)

    def return_chatgpt_conversation(self):
        return self.driver.find_elements(by=By.CSS_SELECTOR, value='div.text-base')

    def save_conversation(self, file_name):
        directory_name = "conversations"
        if not os.path.exists(directory_name):
            os.makedirs(directory_name)

        delimiter = "|＠|"
        chatgpt_conversation = self.return_chatgpt_conversation()
        with open(os.path.join(directory_name, file_name), "a") as file:
            for i in range(0, len(chatgpt_conversation), 2):
                file.write(
                    f"prompt: {chatgpt_conversation[i].text}\nresponse: {chatgpt_conversation[i + 1].text}\n\n{delimiter}\n\n")

    def return_last_response(self):
        """ :return: the text of the last chatgpt response """
        try:
            WebDriverWait(self.driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.text-base")))
            response_elements = self.driver.find_elements(by=By.CSS_SELECTOR, value='div.text-base')
            if response_elements:
                return response_elements[-1].text
            else:
                return ""
        except:
            return ""
        
    def wait_for_human_verification(self):
        print("Please complete the login or human verification steps if required.")

        while True:
            user_input = input(
                "Press 'y' once you've finished the login or human verification, or 'n' to review again:").lower()

            if user_input == 'y':
                print("Proceeding with the automated steps...")
                break
            elif user_input == 'n':
                print("Please finish the human verification. Waiting for completion...")
                time.sleep(5)  # You can adjust the waiting time as needed
            else:
                print("Incorrect input. Please enter 'y' or 'n'.")

    def quit(self):
        """ Closes the browser and terminates the WebDriver session."""
        print("Closing the browser...")
        self.driver.close()
        self.driver.quit()
