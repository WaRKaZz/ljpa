import json
import logging
import os
from getpass import getpass
from time import sleep
from typing import List, Optional, Tuple

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from consts import LINKEDIN_SEARCH_URL, RESOURCES_PATH, SELENIUM_COMMAND_EXECUTOR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LinkedInScraper:
    LOGIN_URL = "https://www.linkedin.com/login"
    SEARCH_URL = LINKEDIN_SEARCH_URL
    COOKIES_PATH = os.path.join(RESOURCES_PATH, "linkedin_cookies.json")
    SCREENSHOT_PATH = "/tmp/linkedin_error.png"

    def __init__(self):
        self.driver = self._configure_driver()
        self.wait = WebDriverWait(self.driver, 15)

    def _configure_driver(self) -> webdriver.Chrome:
        options = ChromeOptions()

        # Essential options for Docker + GUI
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Important for Xvfb display
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--verbose")
        # return webdriver.Chrome(service=service, options=options)
        return webdriver.Remote(
            command_executor=SELENIUM_COMMAND_EXECUTOR, options=options
        )

    # Rest of the class remains the same as original Firefox version
    @staticmethod
    def _get_credentials() -> Tuple[str, str]:
        return (
            os.getenv("LINKEDIN_EMAIL") or input("LinkedIn email: "),
            os.getenv("LINKEDIN_PASSWORD") or getpass("LinkedIn password: "),
        )

    def _scroll_down(self, scroll_pause: float = 2.0, max_scrolls: int = 10):
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        for _ in range(max_scrolls):
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            sleep(scroll_pause)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def _save_cookies(self):
        with open(self.COOKIES_PATH, "w") as file:
            json.dump(self.driver.get_cookies(), file)
        logger.info("Cookies saved.")

    def _load_cookies(self):
        if os.path.exists(self.COOKIES_PATH):
            with open(self.COOKIES_PATH, "r") as file:
                for cookie in json.load(file):
                    self.driver.add_cookie(cookie)
            logger.info("Cookies loaded.")

    def login(self) -> bool:
        try:
            self.driver.get(self.LOGIN_URL)
            self._load_cookies()
            self.driver.refresh()
            if "feed" in self.driver.current_url:
                logger.info("Already logged in.")
                return True

            email, password = self._get_credentials()
            self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            ).send_keys(email)
            self.driver.find_element(By.ID, "password").send_keys(password)
            self.driver.find_element(By.XPATH, "//button[@type='submit']").click()

            self.wait.until(
                lambda d: "feed" in d.current_url
                or "checkpoint/challenge" in d.current_url
            )
            if "checkpoint/challenge" in self.driver.current_url:
                logger.warning("2FA required! Please complete verification.")
                sleep(360)

            self._save_cookies()
            logger.info("Login successful!")
            return True
        except Exception as e:
            logger.error("Login failed: %s", e)
            self._capture_screenshot()
            return False

    def search_posts(self) -> Optional[List[str]]:
        try:
            self.driver.get(self.SEARCH_URL)
            self._scroll_down(scroll_pause=2.0, max_scrolls=5)
            sleep(5)
            posts = self.driver.find_elements(By.CLASS_NAME, "fie-impression-container")
            response = {}
            for post in posts[:10]:
                try:
                    more_button = post.find_element(
                        By.CSS_SELECTOR,
                        ".feed-shared-inline-show-more-text__see-more-less-toggle > span",
                    )
                except NoSuchElementException:
                    more_button = None
                    print("no element")
                if more_button:
                    self.driver.execute_script("arguments[0].click();", more_button)
                    # more_button.click()
                response[post.text] = post.screenshot_as_png
            return response

        except Exception as e:
            logger.error("Failed to search posts: %s", e)
            self._capture_screenshot()
            return None

    def _capture_screenshot(self):
        self.driver.save_screenshot(self.SCREENSHOT_PATH)
        logger.error("Screenshot saved to %s", self.SCREENSHOT_PATH)

    def close(self):
        self.driver.quit()


def startLinkedinScrapper():
    scraper = LinkedInScraper()
    try:
        if scraper.login():
            posts = scraper.search_posts()
            if posts:
                logger.info(f"Found {len(posts)} posts:")
                return posts
            else:
                logger.warning("No posts found.")
    finally:
        scraper.close()


if __name__ == "__main__":
    scraper = LinkedInScraper()
    if scraper.login():
        posts = scraper.search_posts()
        if posts:
            for post_text, _ in posts.items():
                print(f"Post: {post_text}")
        scraper.close()
