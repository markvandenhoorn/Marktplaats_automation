# Marktplaats_automation
Automatically notifies you when a new Nintendo DS is listed on Marktplaats.
Note: There is a relatively large chance that this may not work on other systems but my own. Please notify me of any errors so I can change it to work on other devices as well. 

## Requirements
To use this program, you will have need to have the pushover app on a device. You will also need to get an API token and user key from pushover. Library requirements are listed in requirements.txt

installing them is done by running the following in a terminal:

~~~
pip install -r requirements.txt
~~~

## Usage
<ul>
  <li>Create a .env file in the same folder as the script. In this .env file, write:

  USER_KEY = "your pushover user key"
  
  API_TOKEN = "your pushover API Token"
  
  GOOGLE_EMAIL = "your google email"
  
  GOOGLE_PASSWORD = "your google password"</li>

  <li>From there you can run the script.</li>
  <li>In the first screen, you will need to login manually. Then, go back to your shell and press enter. This will save     the cookies. </li>

<li>Next, a new window opens up. Click 'Accepteren' or 'Accept'. And done! The rest of the work will be done by the script.</li>
</ul>
You will get a pushover notification when a new listing is posted. You will also get a notification when the program crashes. When Wifi connection is lost, the program will try to reconnect every 30 seconds. This makes it so connections issues should not prevent the program from working.

