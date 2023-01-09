import threading
from PIL import ImageOps, Image
import pyautogui
import time
import mss
import os
from statistics import mean
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException

# Set web browser to open dino game in predefined window size and position.
URL = "chrome://dino/"
chrome_driver_path = Service("/Users/adamrembiasz/Documents/100_days_of_Code/_chrome driver/chromedriver")
op = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=chrome_driver_path, options=op)
driver.set_window_rect(22, 47, 800, 500)

# Screen grab tool.
sct = mss.mss()


class DinoBot:
    def __init__(self):
        # Values for tuning bot.
        self.time_trigger_shift = 0.06  # Amount time trigger is reduced each time it's triggered.
        self.time_trigger = 1           # Initial time trigger to move jump detector.
        self.detector_shift = 18        # Amount jump detector is moved each time the time trigger is reached.
        self.detector_start = 325       # X-position of the jump detector at start.

        # Color based on screen and detector size.
        # Based on detector size and screen density i.e. Mac screen is much more pixel dense.
        self.color_trigger = 7756  # 7531 & 7755 (day & night values) 20255 for a Mac screen

        # Detector size x-width, y top and bottom edges.
        self.detector_size = 150
        self.y1 = 359
        self.y2 = 409

        self.shift_count = 1            # Used to calculate new detector position i.e. no. shifts x shift amount.
        self.timer_start_list = []
        self.timer_end_list = []

        # List used to calculate average time delta for last 10 records.
        # Initially populated with 10 records of initial time trigger.
        self.av_time_list = [self.time_trigger for _ in range(10)]

        self.jump_queue = 0             # A queue is used incase next jump is triggered during previous jump.

        # Detector used to trigger jump. This detector is moved as the game speeds up.
        self.jump_detector = (self.detector_start, self.y1, self.detector_start + self.detector_size, self.y2)

        # Detectors used for timer. Timers detect how the game speeds up.
        self.start_detector = (660, self.y1, 660 + self.detector_size, self.y2)
        self.end_detector = (130, self.y1, 130 + self.detector_size, self.y2)

        # Set logic to run loops.
        self.dino_running = True

    def jump_trigger(self):
        previous_detected_color = 0
        while self.dino_running:
            # screen grab and sum grayscale colors in image.
            sct_img = sct.grab(self.jump_detector)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            gray_img = ImageOps.grayscale(img)
            detected_color = sum(map(sum, gray_img.getcolors()))

            # If detected color goes from obstacle to background color trigger jump.
            # i.e. detecting back end of obstacle.
            if detected_color < self.color_trigger < previous_detected_color:
                self.jump_queue += 1

            previous_detected_color = detected_color

    def jump(self):
        while self.dino_running:
            # Check jump_queue and jump if not 0, wait until jump duration passed.
            if self.jump_queue > 0:
                # print('start-jump')    # 56 ms duration
                pyautogui.keyDown("space")
                time.sleep(0.05)
                pyautogui.keyUp("space")
                time.sleep(0.30)
                self.jump_queue -= 1
                # print('End-jump')

    def start_timer(self):
        previous_detected_color_1 = 0
        while self.dino_running:
            # screen grab and sum grayscale colors in image.
            signal_1_sct_img = sct.grab(self.start_detector)
            signal_1_img = Image.frombytes("RGB", signal_1_sct_img.size, signal_1_sct_img.bgra, "raw", "BGRX")
            signal_1_gray_img = ImageOps.grayscale(signal_1_img)
            signal_1_detected_color = sum(map(sum, signal_1_gray_img.getcolors()))

            # If detected color goes from background to obstacle start timer.
            if previous_detected_color_1 < self.color_trigger < signal_1_detected_color:
                start = time.time()
                self.timer_start_list.append(start)

            previous_detected_color_1 = signal_1_detected_color

    def end_timer(self):
        previous_detected_color_0 = 0
        while self.dino_running:
            # screen grab and sum grayscale colors in image.
            signal_0_sct_img = sct.grab(self.end_detector)
            signal_0_img = Image.frombytes("RGB", signal_0_sct_img.size, signal_0_sct_img.bgra, "raw", "BGRX")
            signal_0_gray_img = ImageOps.grayscale(signal_0_img)
            signal_0_detected_color = sum(map(sum, signal_0_gray_img.getcolors()))

            # If detected color goes from background to obstacle end timer.
            if previous_detected_color_0 < self.color_trigger < signal_0_detected_color:
                end = time.time()
                self.timer_end_list.append(end)

            previous_detected_color_0 = signal_0_detected_color

    def detector_update(self):
        while self.dino_running:
            # If start detector misses obstacle reset end timer list.
            # i.e. start timer list empty but end timer list is not.
            if len(self.timer_end_list) > 0 and len(self.timer_start_list) == 0:
                self.timer_end_list.pop(0)
            # If end detector signals obstacle calculate average time obstacle passes detectors.
            elif len(self.timer_end_list) > 0:
                # Take the oldest start time from timer list and add time delta to average time list
                # Remove the oldest entry from both timer and average time list.
                self.av_time_list.append(self.timer_end_list.pop(0) - self.timer_start_list.pop(0))
                self.av_time_list.pop(0)

                # Calculate average time based on last 10 time delta values.
                av_time = mean(self.av_time_list)

                # print(f"average time, time trigger:, {av_time}, {self.time_trigger}")

                # Shift first detector further from dino when time delta gets shorter.
                # Tuning values; time trigger, time trigger shift, detector shift and shift count used here.
                if av_time < self.time_trigger:
                    self.jump_detector = (self.detector_start + (self.detector_shift * self.shift_count),
                                          self.y1,
                                          self.detector_start +
                                          (self.detector_shift * self.shift_count) + self.detector_size,
                                          self.y2)
                    self.shift_count += 1
                    self.time_trigger -= self.time_trigger_shift
                    self.detector_shift += 1
            time.sleep(0.1)

    def background_color(self):
        # Use to find background colors when tuning bot, prints value that is used to set detectors.
        while self.dino_running:
            background_detector = (50, 470, 200, 520)
            bkg_grab = sct.grab(background_detector)
            bkg_img = Image.frombytes("RGB", bkg_grab.size, bkg_grab.bgra, "raw", "BGRX")
            gray_bkg = ImageOps.grayscale(bkg_img)
            detected_bkg = sum(map(sum, gray_bkg.getcolors()))
            print(f"Background color: {detected_bkg}")
            # pyautogui.moveTo(background_detector[2], background_detector[3])
            # pyautogui.moveTo(background_detector[0], background_detector[1])

    def end_of_game(self):
        # Detects location of reset button. If found stops bot.
        bbox = (397, 339, 447, 376)                 # This needs to be set to capture reset button.
        while self.dino_running:
            # Check area where restart button appears at end of game.
            lose_grab = sct.grab(bbox)
            lose_img = Image.frombytes("RGB", lose_grab.size, lose_grab.bgra, "raw", "BGRX")
            gray_lose_img = ImageOps.grayscale(lose_img)
            detected_color = sum(map(sum, gray_lose_img.getcolors()))
            # print(f"End game: {detected_color}")

            if detected_color == 2385:
                # Screen grab game area and save with time stamp to record score.
                time_stamp = time.strftime("%Y%m%d-%H%M%S")
                bbox_score = (22, 173, 819, 536)
                score_grab = sct.grab(bbox_score)
                score_img = Image.frombytes("RGB", score_grab.size, score_grab.bgra, "raw", "BGRX")
                dir_name = "Score"

                # If directory does not exist create new directory to save scores.
                if not os.path.exists(dir_name):
                    os.mkdir(dir_name)

                filepath = f"{dir_name}/game_over-{time_stamp}.jpg"
                score_img.save(filepath)

                # Close bot.
                self.dino_running = False
            time.sleep(1)

    def run_bot(self):
        # Start the game.
        time.sleep(0.5)
        pyautogui.press("space")
        time.sleep(3)

        # Show location of detector.
        # pyautogui.moveTo(self.start_detector[2], self.start_detector[3])

        # Set loop for jump detector and for jump function.
        t1 = threading.Thread(target=self.jump_trigger)
        t1.start()
        t2 = threading.Thread(target=self.jump)
        t2.start()

        # Set loop to check for end of game.
        t3 = threading.Thread(target=self.end_of_game)
        t3.start()

        # Detect start and end time of obstacle passing screen.
        t4 = threading.Thread(target=self.start_timer)
        t4.start()
        t5 = threading.Thread(target=self.end_timer)
        t5.start()

        # Update detector position based on average time change.
        t6 = threading.Thread(target=self.detector_update)
        t6.start()

        # Check background color - prints value.
        # t7 = threading.Thread(target=self.background_color)
        # t7.start()


def main():
    try:
        driver.get(URL)     # Open browser with dino game.
    except WebDriverException:
        pass

    bot = DinoBot()
    bot.run_bot()


if __name__ == "__main__":
    main()
