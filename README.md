# Dino-Game-Bot
This is a bot designed to play the Google Chrome Dino game.

 - Performace is based on computer performance and screen pixel density. Values for tuning are labeled at the top of the 'DinoBot' class.
 - 4 detectors are used and may need adjusting based on browser window location and size.
 - 1 detector is used to trigger jump. This detector is moved as the game speeds up. This detector is tuned for optimal performance.
 - 2 detectors used to measure the time it takes for the obstacles to pass, monitoring game speed.
 - 1 detector triggered when reset button appears. Game screen is recorded and saved in a separate folder named 'score'.
 - Threading is used for optimal performace of obstacle detection.
 
