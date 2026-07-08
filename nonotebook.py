import signal as sig
import re #regex

#threading and memory
import threading
import queue

#Data Cleaning
import bs4 as bs 
import requests as req
import pandas as pd
import numpy as np

#Scraping, Selenium and Soup
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

#Camoufox
import camoufox


class Scraper:
    def __init__(self,num_consumers):
        
                #--- Constants
        self.main_page = "https://turbo.az"
        self.time_quota = 4
        self.num_consumers = num_consumers
        self.websites = self.producer_link_gen(10)

                #--- Shared state across threads
        self.url_queue = queue.Queue()      #FIFO queue 
        self.seen_urls = set()              #set
        self.seen_lock = threading.Lock()   #thread lock

        self.results = []                   #list for results
        self.results_lock = threading.Lock()# thread safe locking
        
    @staticmethod   
    def create_driver():
        '''
        This function supposed to be called by individual threads and creates webdriver instances.
        (Using global driver is not Thread safe!!!)
        '''
        with sync_playwright() as p:
            browser = p.chromium.launch(headless = False)
            return browser.new_page() 
            

    
    
    #crawler and its producer

    def crawler(self, url, driver) -> list:
        '''
        Crawler scraper. Scrapes hrefs,
        creats full link connecting href with
        main page(turbo.az) and sends link to the producer
        '''
        driver.goto(url)
        soup = BeautifulSoup(driver.content())
    
        return [
            f"{self.main_page}{i['href']}"
            for i in soup.find_all('a', href=True)
            if re.fullmatch(r'/autos/\d+[\w-]*', i['href'])
        ]
    
    
    def producer(self, url):
        """
        Initializes Crawler and redirects links to consumer
        """
        driver = self.create_driver()
        try:
            hrefs = self.crawler(url, driver)
            print(hrefs)
            print(len(hrefs))
            for href in hrefs:
                with self.seen_lock:
                    if href in self.seen_urls:
                        continue
                    self.seen_urls.add(href)
                self.url_queue.put(href)
            print('crawler ended')    
        finally:
            driver.quit()

    def producer_link_gen(self, max_pages):
        for page_num in range(1, max_pages + 1):
            yield f'https://turbo.az/autos?page={page_num}'


    #--- fetcher and its consumer
    #@staticmethod
    def details_parser(self, soup):
        
        rows = soup.select('.product-properties__i')
        properties = {}
        for row in rows:
            name_el = row.select_one('.product-properties__i-name')
            value_el = row.select_one('.product-properties__i-value')
            if name_el == value_el:
                name = name_el.get_text(strip=True)
                value = value_el.get_text(strip=True)
                properties[name] = value
        return properties 

    def fetch_details(self, href, driver):
        """
        Takes parameters from consumer and scrapes whatever i needed from targeted pages(Test)
        """
        driver.get(href)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        properties = self.details_parser(soup)
        return {
        "url": href,
        "city": properties.get("Şəhər"),
        "brand": properties.get("Marka"),
        "model": properties.get("Model"),
        "year": properties.get("Buraxılış ili"),
        "body_type": properties.get("Ban növü"),
        "color": properties.get("Rəng"),
        "engine": properties.get("Mühərrik"),
        "mileage": properties.get("Yürüş"),
    }
    
    
    
    def consumer(self):
        driver = self.create_driver()

        try:
            while True:
                href = self.url_queue.get()
                if href is None:
                    break
                data = self.fetch_details(href, driver)
                print('consumer ended')
                
                with self.results_lock:
                    self.results.append(data)
                self.url_queue.task_done()
                
        finally:
            webdriver.quit()
        

    def run(self):
        # 1. Start consumers FIRST — they'll just block on an empty
        #    queue until producers put work in.
        consumer_threads = [
            threading.Thread(target=self.consumer)
            for _ in range(self.num_consumers)
        ]
        for t in consumer_threads:
            print('comsumer started')
            t.start()
        # for t in consumer_threads:
        #     t.join()

        
        # 2. Start one producer(Crawler starter) thread per website.
        producer_threads = [
            threading.Thread(target=self.producer, args=(url,))
            for url in self.websites
        ]
        for t in producer_threads:
            print('crawler started')
            t.start()
        for t in producer_threads:
            t.join()   # wait until all producers finish finding hrefs



        # 3. Now that no more hrefs are coming, tell each consumer to stop
        for _ in range(self.num_consumers):
            self.url_queue.put(None)

        for t in consumer_threads:
            t.join()

        return self.results        

def main():
    print("Starting web scraping with multithreading...")
    start_time = time.time()
    scraper = Scraper(
        num_consumers= 8
    )
    results = scraper.run()
    print(results)
    end_time = time.time()
    print(f"Scraped {len(results)} listings in {end_time - start_time:.2f} seconds")





if __name__ == "__main__":
    #main()
    driver = Scraper.create_driver()
    driver.goto('https://turbo.az')