# FacebookCommentLoader
*Scripts to load comments from a facebook post and extract expressions*

This project was created for the specific purpose of extracting numbers from the comments of a FB post. However I tried to make the handling of comments and expressions generic, so the script can be modified to extract other types of expressions.

For now there is only one script that extracts information from all comments under one post following a specific pattern. Currently I have no plans to expand on it.

## How to use
### Prerequisites
This python script uses Selenium, you need to have it installed before using this. For more information, see the [Selenium website](https://pypi.org/project/selenium/)

Regular expressions are also used. Regex is a built in python library, so there is no need to install it separately. However, changing the patterns requires regex knowledge. 

### Parameters
The main function at the end of the script contains all parameters and their descriptions.
The following can (and should) be changed:
- the URL of the facebook page
- the regex pattern of the expressions to be matched
- a list of of expressions that indicate a false positive match
- a regex of characters that need to be removed from the results
- the minimum length of a matching expression that counts
- the facebook display language
  - currently only english (default) and hungarian are supported

### Authentication
As facebook has access control for users, the script requires authentication. When the page has loaded, the script will ask for login details. It can handle basic two factor authentication as well. These details are not saved and not used after the login was successful.

## Disclaimer
This script has only been used once and may contain bugs. It has known exceptions that it can not handle, e.g. on two factor auth screens.
Currently there is no support provided to fix these bugs, nor any plan to develop the script further. Feel free to use and modify the script at your own discretion.
