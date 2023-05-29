# Instagram-Competitor-Follower-Tracker
The Instagram Follower Tracker script is a Python tool that uses Instagram API, Google Sheets, and MySQL to monitor and analyze followers and following of an Instagram account. It fetches the latest data, updates Google Sheets and MySQL database, identifies new followers/following, and runs at a specified frequency. 

Here's a summary of what the code does:

(1) Imports necessary libraries and modules.
(2) Sets up configuration variables, including Instagram account credentials, Google Sheets settings, database configuration, and execution frequency.
(3) Initializes the Instagram API client and defines a signal handler for script termination.
(4) Defines helper functions to fetch followers, following, and followers and following who follow each other.
(5) Defines a login function to authenticate with the Instagram API.
(6) Connects to the MySQL database and creates the necessary tables if they don't exist.
(7) Defines a function to handle rate limit exceeded errors.
(8) Defines functions to check if a follower or following is new.
(9) Defines a function to update the "follow_each_other" worksheet with followers and following who follow each other.
(10) Defines functions to update the followers and following sheets in Google Sheets and the MySQL database.
(11) Defines the main function to run the script.
(12) Authenticates with the Instagram API.
(13) Creates spreadsheets in Google Sheets for followers, following, new followers, new following, and followers and following who follow each other.
(14) Enters a loop to periodically update the followers and following sheets.
(15) The script continuously fetches the latest followers and following, updates the corresponding sheets, checks for new followers and following, and stores the data in the database.
(16) The script also updates the "follow_each_other" sheet with the followers and following who follow each other.
(17) The script waits for the specified execution frequency before retrying the updates.

In summary, this script allows you to track the followers and following of an Instagram account, store the data in a MySQL database, and update corresponding Google Sheets for analysis and monitoring.




