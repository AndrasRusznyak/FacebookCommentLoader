# -*- coding: utf-8 -*-
"""
Created on Wed Oct 28 15:30:08 2020

@author: Andras
"""

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import time
import re
import csv
import getpass

class PatternHandler():

    def __init__(self, pattern_string, false_positive_signs, irrelevant_characters = r"", min_length = 1):
        self.pattern = re.compile(pattern_string)
        self.false_positive_signs = false_positive_signs
        self.irrelevant_characters = irrelevant_characters
        self.min_length = min_length

    # Return True if the pattern was found, False if not
    # In addition return a warning if false positive signs were found
    def detect_pattern(self, input_string):
        match = bool(self.pattern.search(input_string))

        false_positive_warning = False
        if any(value in input_string.lower() for value in self.false_positive_signs):
            false_positive_warning = True

        return match, false_positive_warning

    # Return a list of all matches for the given pattern
    def extract_pattern(self, input_string):
        return [re.sub(self.irrelevant_characters, '', match) for match in self.pattern.findall(input_string) if not len(match) < self.min_length]

class FBCommentLoader():

    def __init__(self, url, language = 'en'):
        self.driver = webdriver.Firefox()
        self.driver.get(url)
        if(language == 'hu'):
            self.prev_com_text = "Korábbi hozzászólások megtekintése"
            self.more_com_text = "További hozzászólások"
            self.comment_label = "hozzászólása"
        else:
            self.prev_com_text = "View previous comments"
            self.more_com_text = "View more comments"
            self.comment_label = "Comment by"

    def check_element_by_id(self, id_):
        try:
            self.driver.find_element_by_id(id_)
        except NoSuchElementException:
            return False

        return True

    def login(self):
        try:
            print("FB username: ")
            uname = str(input())

            self.driver.find_element_by_name('email').send_keys(uname)

            password = getpass.getpass("FB password: ")
            password_field = self.driver.find_element_by_name('pass')
            password_field.send_keys(password)
            password_field.send_keys(Keys.RETURN)

            # Wait for next page to see if two factor auth is needed
            self.driver.implicitly_wait(5)

            if self.check_element_by_id('approvals_code'):
                print("Two factor auth code: ")
                code = str(input())
                code_field = self.driver.find_element_by_id('approvals_code')
                code_field.send_keys(code)
                submit_button = self.driver.find_element_by_id('checkpointSubmitButton')
                submit_button.click()

                self.driver.implicitly_wait(4)

                # Wait for the submit button to appear on the next screen
                submit_button = EC.presence_of_element_located((By.ID, 'checkpointSubmitButton'))
                WebDriverWait(self.driver, 10).until(submit_button)

                submit_button = self.driver.find_element_by_id('checkpointSubmitButton')
                submit_button.click()
                comment = EC.presence_of_element_located((By.XPATH, "//div[contains(@aria-label,'" + self.comment_label + "')]"))
                WebDriverWait(self.driver, 10).until(comment)

        except TimeoutException:
            print("The front page has not loaded yet, please handle the browser and press Enter when the page has loaded")
            waiting_input = input()
            pass

        except NoSuchElementException:
            print("The page has not loaded successfully for login")
            self.close()

    def load_all_comments(self):
        # Load all previous comments until there are none
        try:
            while(True):
                # Find the button that has a sub-tag with the previous comments text
                prev_com = self.driver.find_element_by_xpath("//*[text()='" + self.prev_com_text + "']/ancestor::*[@role='button']")

                if prev_com is not None:
                    prev_com.click()
                # Slow down clicking on the button to lower the load
                self.driver.implicitly_wait(3)

        except NoSuchElementException:
            # When all previous comments are loaded, jump to the next step
            pass
        # Load all further comments, until there are none
        try:
            while(True):
                # Find the button that has a sub-tag with the more comments text
                more_com = self.driver.find_element_by_xpath("//*[text()='" + self.more_com_text + "']/ancestor::*[@role='button']")

                if more_com is not None:
                    more_com.click()
                # Slow down clicking on the button to lower the load
                self.driver.implicitly_wait(3)

        except NoSuchElementException:
            return True

    def extract_comments(self, ph, include_replies = False):
        try:
            # Find the first comment and take its ancestor list as the comment list
            comment_list = self.driver.find_element_by_xpath("//div[contains(@aria-label,'" + self.comment_label + "')]/ancestor::ul[*]")

            # Extract the list of comments from the list tag
            if include_replies:
                comments = comment_list.find_elements_by_xpath(".//div[@role='article']")
            else:
                # If replies are not required, filter to first level comments only
                comments = comment_list.find_elements_by_xpath(".//div[@role='article'][contains(@aria-label,'" + self.comment_label + "')]")

            # Start building the list of relevant comments, i.e. thoe that have a matching pattern
            self.relevant_comments = []
            for idx, comment in enumerate(comments):
                # Find the name of the commenter
                name = ""
                # There should be at least two hyperlinks in a comment
                # The first is the picture of the user, the sacond is the name
                links = comment.find_elements_by_xpath(".//a[@role='link'][contains(@href,'/user/')]")
                if len(links) > 1:
                    name = links[1].text

                # Find the individual lines of the comment and take them separately
                comment_lines = comment.find_elements_by_xpath(".//div[@style='text-align: start;']")

                for line in comment_lines:

                    # Clear the variables before matching
                    result = ""
                    warning_message = ""

                    match, warning = ph.detect_pattern(line.text)

                    if match:
                        # The matches are cleaned of non numeric characters and concatenated into a single string
                        match_list = ph.extract_pattern(line.text)
                        result += (" ".join(match_list)).strip()

                        # If there are more than 3 matches in a single line,
                        # it is very likely a false positive result
                        if(warning or len(match_list) > 2):
                            warning_message = "Check this result"

                        # Save result line by line, not comment by comment
                        if(not (result == "")):
                            self.relevant_comments.append([idx, name, result, warning_message, line.text])

        except NoSuchElementException:
            print("There are no comments on the page")
            self.close()
            return False

        return self.relevant_comments

    def save_results(self, filename):
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as result_file:
                wr = csv.writer(result_file)
                wr.writerow(["Comment number", "Name", "Extracted result", "False positive warning", "Full comment line"])
                wr.writerows(self.relevant_comments)

            print("The results have been saved to {}".format(filename))

        except Exception as exc:
            print("A(n) {} type error occured during saving the results".format(type(exc).__name__))
            print(exc)

    def close(self):
        self.driver.quit()

def main():
    url = "https://www.facebook.com/groups/1458939870864411/permalink/3461178263973885/"
    # Edit this pattern to extract different expressions from comments
    # Pattern explanation:
    #    \b - start with a word boundary, i.e. the pattern should be a separate word
    #    [+]? - followed by an optional + sign
    #    \d+ - followed by one or more digits
    #    [.]?[,]? - may or may not have a dot or a comma as a thousand separator
    #    \d* - followed by any number of digits
    #    \S* - followed by any number of non-whitespace characters
    #    \b - end with a word boundary
    pattern = r"\b[+]?\d+[.]?[,]?\d*\S*\b"

    # If any of the following expressions occur in the comment,
    # it may not be a true positive match, human review needed
    false_positive_signs = [
        "total",
        "totál",
        "#",
        "(",
        "kg",
        "kilo",
        "kiló",
        "-"]

    # The following characters need to be removed from the matches
    # Currently all non numeric characters are removed
    irrelevant_characters = r"[^0-9]"

    # Matches shorter than the minimum length will be ignored
    min_match_length = 2

    # FB display language
    # Currently supported: en and hu
    fb_display_lan = 'hu'

    pattern_handler = PatternHandler(pattern,
                                     false_positive_signs,
                                     irrelevant_characters,
                                     min_match_length)
    loader = FBCommentLoader(url, fb_display_lan)

    # Wait for the browser to open and load the page
    time.sleep(3)

    # Login
    loader.login()

    # Load all comments not shown
    loader.load_all_comments()

    # Wait for the browser to catch up
    time.sleep(5)

    # Extract the comments matching the pattern
    comments = loader.extract_comments(pattern_handler, include_replies = False)
    print("{} comments have been extracted".format(len(comments)))

    # Save the results
    loader.save_results("comments.csv")

    # Close the process
    loader.close()

if __name__ == "__main__":
    main()