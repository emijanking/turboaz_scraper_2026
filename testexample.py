from playwright.sync_api import sync_playwright
import time 
def scraper_firefox():
    with sync_playwright() as p:
        browser = p.firefox.launch(headless = False)
        st = time.time()
        page = browser.new_page()
        page.goto('https://turbo.az')
        
        page.wait_for_selector(".products-i__link")
        page.close()
        end = time.time()
        
        print(f" firefox opened in {end - st:.2f} seconds")

def scraper_chromium():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless = False)
        st = time.time()
        page = browser.new_page()
        page.goto('https://turbo.az')
        
        page.wait_for_selector(".products-i__link")
        page.close()
        end = time.time()
        
        print(f"Chrpmium opened in {end - st:.2f} seconds")



if __name__ == "__main__":
    scraper_firefox()