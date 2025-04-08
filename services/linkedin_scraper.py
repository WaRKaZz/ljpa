import json
import logging
import os
from getpass import getpass
from time import sleep
from typing import Dict, List, Optional, Tuple

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import LINKEDIN_SEARCH_URL, RESOURCES_PATH, SELENIUM_COMMAND_EXECUTOR

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LinkedInScraper:
    """
    Scraper for LinkedIn that handles login, scrolling, and post extraction.
    """

    LOGIN_URL = "https://www.linkedin.com/login"
    SEARCH_URL = LINKEDIN_SEARCH_URL
    COOKIES_PATH = os.path.join(RESOURCES_PATH, "linkedin_cookies.json")
    SCREENSHOT_PATH = "/tmp/linkedin_error.png"

    def __init__(self) -> None:
        self.driver: WebDriver = self._configure_driver()
        self.wait = WebDriverWait(self.driver, 15)

    def _configure_driver(self) -> WebDriver:
        """
        Configures and returns a Selenium Remote WebDriver using Chrome options.
        """
        options = ChromeOptions()
        # Options for Docker and headless environments
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--verbose")
        return webdriver.Remote(
            command_executor=SELENIUM_COMMAND_EXECUTOR, options=options
        )

    @staticmethod
    def _get_credentials() -> Tuple[str, str]:
        """
        Retrieves LinkedIn credentials from environment variables or via user prompt.
        """
        email = os.getenv("LINKEDIN_EMAIL") or input("LinkedIn email: ")
        password = os.getenv("LINKEDIN_PASSWORD") or getpass("LinkedIn password: ")
        return email, password

    def _scroll_down(self, scroll_pause: float = 2.0, max_scrolls: int = 10) -> None:
        """
        Scrolls down the page to load additional content.

        Args:
            scroll_pause (float): Pause time between scrolls.
            max_scrolls (int): Maximum number of scrolls.
        """
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

    def _save_cookies(self) -> None:
        """
        Saves the current session cookies to a file.
        """
        with open(self.COOKIES_PATH, "w") as file:
            json.dump(self.driver.get_cookies(), file)
        logger.info("Cookies saved to %s", self.COOKIES_PATH)

    def _load_cookies(self) -> None:
        """
        Loads session cookies from a file if available.
        """
        if os.path.exists(self.COOKIES_PATH):
            with open(self.COOKIES_PATH, "r") as file:
                cookies = json.load(file)
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
            logger.info("Cookies loaded from %s", self.COOKIES_PATH)

    def login(self) -> bool:
        """
        Performs login on LinkedIn using saved cookies or by providing credentials.

        Returns:
            bool: True if login is successful; False otherwise.
        """
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

            # Wait until user is redirected to the feed or challenge checkpoint appears.
            self.wait.until(
                lambda d: "feed" in d.current_url
                or "checkpoint/challenge" in d.current_url
            )

            if "checkpoint/challenge" in self.driver.current_url:
                logger.warning(
                    "Two-factor authentication required! Please complete verification."
                )
                sleep(360)

            self._save_cookies()
            logger.info("Login successful!")
            return True
        except Exception as err:
            logger.error("Login failed: %s", err)
            self._capture_screenshot()
            return False

    def search_posts(self) -> Optional[Dict[str, bytes]]:
        """
        Searches for posts on LinkedIn by scrolling and extracting text and screenshots.

        Returns:
            Optional[Dict[str, bytes]]: Dictionary mapping post text to screenshot PNG bytes,
                                        or None if an error occurs.
        """
        try:
            self.driver.get(self.SEARCH_URL)
            self._scroll_down(scroll_pause=2.0, max_scrolls=5)
            sleep(5)  # Ensure page content is fully loaded
            posts_elements = self.driver.find_elements(
                By.CLASS_NAME, "fie-impression-container"
            )
            posts_data = {}
            for post in posts_elements[:10]:
                try:
                    more_button = post.find_element(
                        By.CSS_SELECTOR,
                        ".feed-shared-inline-show-more-text__see-more-less-toggle > span",
                    )
                    # Expand the post if the "see more" button is present.
                    self.driver.execute_script("arguments[0].click();", more_button)
                except NoSuchElementException:
                    logger.debug("No 'see more' button found for a post.")
                posts_data[post.text] = post.screenshot_as_png
            return posts_data
        except Exception as err:
            logger.error("Failed to search posts: %s", err)
            self._capture_screenshot()
            return None

    def _capture_screenshot(self) -> None:
        """
        Captures a screenshot of the current driver window for debugging.
        """
        self.driver.save_screenshot(self.SCREENSHOT_PATH)
        logger.error("Screenshot saved to %s", self.SCREENSHOT_PATH)

    def close(self) -> None:
        """
        Closes the Selenium WebDriver session.
        """
        self.driver.quit()


def start_linkedin_scraper() -> Optional[Dict[str, bytes]]:
    """
    Initializes the LinkedIn scraper, logs in, and performs a post search.

    Returns:
        Optional[Dict[str, bytes]]: The scraped posts data if successful, None otherwise.
    """
    scraper = LinkedInScraper()
    try:
        if scraper.login():
            posts = scraper.search_posts()
            if posts:
                logger.info("Found %d posts.", len(posts))
                return posts
            else:
                logger.warning("No posts found.")
    finally:
        scraper.close()
    return None


if __name__ == "__main__":
    scraper = LinkedInScraper()
    if scraper.login():
        posts = scraper.search_posts()
        if posts:
            for post_text in posts.keys():
                logger.info("Post: %s", post_text)
        scraper.close()
