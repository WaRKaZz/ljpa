import logging
from time import sleep
from typing import Optional, Dict

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnergyJoblineScraper:
    SEARCH_URL = "https://www.energyjobline.com/jobs?keywords=PLC&date_posted=Today"
    SCREENSHOT_PATH = "/tmp/energyjobline_error.png"

    def __init__(self, headless: bool = True):
        self.driver = self._configure_driver(headless)
        self.wait = WebDriverWait(self.driver, 15)

    def _configure_driver(self, headless: bool) -> webdriver.Firefox:
        options = FirefoxOptions()
        if headless:
            options.add_argument("--headless")
        options.set_preference("dom.webnotifications.enabled", False)
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        return webdriver.Firefox(options=options)

    def _load_all_jobs(self, max_clicks: int = 5):
        """Click 'Show more jobs' button to load all available positions"""
        for _ in range(max_clicks):
            try:
                button = self.driver.find_element(
                    By.CSS_SELECTOR, "button[data-test-id='show-more-jobs']"
                )
                button.click()
                sleep(2)
                self.wait.until(EC.staleness_of(button))
            except NoSuchElementException:
                break

    def search_posts(self) -> Optional[Dict[str, bytes]]:
        try:
            self.driver.get(self.SEARCH_URL)
            
            # Wait for initial results and load all jobs
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-test-id='job-card']")))
            self._load_all_jobs()

            # Get all job posts
            posts = self.driver.find_elements(By.CSS_SELECTOR, "div[data-test-id='job-card']")
            response = {}

            for post in posts:
                try:
                    # Expand job description if available
                    expand_btn = post.find_element(By.CSS_SELECTOR, "button[data-test-id='read-more-button']")
                    expand_btn.click()
                    sleep(0.5)
                except NoSuchElementException:
                    pass

                # Capture text and screenshot
                response[post.text] = post.screenshot_as_png

            return response

        except Exception as e:
            logger.error("Failed to search posts: %s", e)
            self.driver.save_screenshot(self.SCREENSHOT_PATH)
            return None

    def close(self):
        self.driver.quit()


if __name__ == "__main__":
    scraper = EnergyJoblineScraper(headless=True)
    try:
        posts = scraper.search_posts()
        if posts:
            for text, screenshot in posts.items():
                print(f"Job Post:\n{text}\n{'='*50}")
                # To save screenshots:
                # with open(f"post_{hash(text)}.png", "wb") as f:
                #     f.write(screenshot)
    finally:
        scraper.close()