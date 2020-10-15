# Import libraries
import RPi.GPIO as GPIO
import random
import ES2EEPROMUtils
import os
import time

# some global variables that need to change as we run the program
end_of_game = None  # set if the user wins or ends the game
win = 0
# DEFINE THE PINS USED HERE
LED_value = [11, 13, 15]
LED_accuracy = 32
btn_submit = 16
btn_increase = 18
buzzer = None
eeprom = ES2EEPROMUtils.ES2EEPROM()

LED_count = 0
interrupt_timer = 0
pwmLED = None

#count of user guesses
score = 0

#user must guess the value
value = 0


# Print the game banner
def welcome():
    os.system('clear')
    print("  _   _                 _                  _____ _            __  __ _")
    print("| \ | |               | |                / ____| |          / _|/ _| |")
    print("|  \| |_   _ _ __ ___ | |__   ___ _ __  | (___ | |__  _   _| |_| |_| | ___ ")
    print("| . ` | | | | '_ ` _ \| '_ \ / _ \ '__|  \___ \| '_ \| | | |  _|  _| |/ _ \\")
    print("| |\  | |_| | | | | | | |_) |  __/ |     ____) | | | | |_| | | | | | |  __/")
    print("|_| \_|\__,_|_| |_| |_|_.__/ \___|_|    |_____/|_| |_|\__,_|_| |_| |_|\___|")
    print("")
    print("Guess the number and immortalise your name in the High Score Hall of Fame!")


# Print the game menu
def menu():
    global end_of_game
    global value
    global win
    option = input("Select an option:   H - View High Scores     P - Play Game       Q - Quit\n")
    option = option.upper()
    if option == "H":
        os.system('clear')
        print("HIGH SCORES!!")
        s_count, ss = fetch_scores()
        display_scores(s_count, ss)
    elif option == "P":
        os.system('clear')
        win = 0
        print("Starting a new round!")
        print("Use the buttons on the Pi to make and submit your guess!")
        print("Press and hold the guess button to cancel your game")
        value = generate_number()
        print(value)
        while not end_of_game:
            pass
    elif option == "Q":
        print("Come back soon!")
        exit()
    else:
        print("Invalid option. Please select a valid one!")


def display_scores(count, raw_data):
    # print the scores to the screen in the expected format
    print("There are {} scores. Here are the top 3!".format(count))

    names = []
    scoreList = []

    if raw_data == None: 
        print("No scores")
        return None

    for i in range(3):
        name = ""
        for j in range(3): #name section of the block
            print(raw_data[i*4 + j])
            name += raw_data[i*4 + j]
                
        names.append(name)
        scoreList.append(raw_data[i*4 + 3])


    for i in range(3):
        print(i+1,"-",names[i], "took", str(scoreList[i]), "guesses")

    #end

# Setup Pins
def setup():
    global pwmLED
    global buzzer

    GPIO.setmode(GPIO.BOARD)
	
	#set up inputs
    GPIO.setup(btn_submit, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.setup(btn_increase, GPIO.IN, pull_up_down = GPIO.PUD_UP)
	#set up callbacks which will handle debounce
    GPIO.add_event_detect(btn_submit, GPIO.FALLING, callback = btn_guess_pressed, bouncetime = 2000)
    GPIO.add_event_detect(btn_increase, GPIO.FALLING, callback = btn_increase_pressed, bouncetime = 200)
	
	#set up outputs
    for i in range(3):
        GPIO.setup(LED_value[i], GPIO.OUT)
        GPIO.output(LED_value[i], 0)
		
	#set up PWM for LED and Buzzer
    GPIO.setup(LED_accuracy, GPIO.OUT)
    GPIO.setup(33, GPIO.OUT) 
    pwmLED = GPIO.PWM(LED_accuracy, 100)
    buzzer = GPIO.PWM(33, 4)		#set frequency to 4 Hz
	
    buzzer.start(0)
    pwmLED.start(0)


# Fetch all scores
def fetch_scores():
    # get however many scores there are
    print("in fetch scores")

    score_count = eeprom.read_byte(0x00)
    print(score_count)
    
    if score_count == 0:
        return score_count, None
    
    scores = []    #i.e. a list of blocks
    pointer = 0x20
                              #update to new position
    data = eeprom.read_block(pointer,4*score_count)    #add block to scores, each index in scores, is a 4 index array i.e. a block 
    
    
    for i in range(len(data)):
        if i ==0:
            continue
        elif((i+1) % 4) == 0:
            #convert to ascii
            name = ""
            entry = data[i-3:i]
            for character in entry:
                scores.append(chr(character))
                print(character)
            #name += "_"
            #name += str(entry[-1]) 

            #name = name.strip()
            
            #print(entry[-1])
            #scores.append(name)
            scores.append(data[i])
    
    #print
    #return back the results     scores = <name>_<score>
    return score_count, scores
    

def sortBlocks(data): #for sorting purposes splits and returns 2nd element which stores score as comparison value for sort
    #data = data.split("_")
    return data[3]

# Save high scores
def save_scores(name):
    global score
    # fetch scores
    # include new score
    # sort
    # update total amount of scores
    # write new scores
    score_count, scores = fetch_scores()
    score_count += 1
    
    #toAdd = []
    #toAdd.append(name)
    #toAdd.append(score)
    for character in name:
        scores.append(character)

    scores.append(score)

    blocks = []

    for i in range(len(scores)):
        if i == 0:
            continue

        elif (i+1)%4 == 0:
            blocks.append(scores[i-3:i+1])


    blocks.sort(key = sortBlocks)
    
    toWrite = []
    eeprom.write_byte(0x00, score_count)
    
    for block in blocks:
        for i in range(len(block)):
            if i == 3:
                toWrite.append(block[i])
            else:
                toWrite.append(ord(block[i]))       
            
    

    eeprom.write_block(0x20,toWrite)
    print("Saved Scores to EEPROM")
    


# Generate guess number
def generate_number():
    return random.randint(0, 7)


# Increase button pressed
def btn_increase_pressed(channel):
    global LED_count
    global interrupt_timer

    # Increase the value shown on the LEDs
    # You can choose to have a global variable store the user's current guess, 
    # or just pull the value off the LEDs when a user makes a guess
    #print("button pressed")
	#Debounce:
    currentTime = int(round(time.time()) *1000)

    if (currentTime - interrupt_timer) > 400 :			#200 millis have passed i.e. ok

		#handle looping i.e. 6, 7, 0, 1...
        if LED_count < 7:
            LED_count += 1
        else:
            LED_count = 0 
	
        setValue = []		#stores whether a high or low

        for i in range(3):
            if (LED_count >> i) & 1 == 1:
                setValue.insert(i, GPIO.HIGH)
            else:
                setValue.insert(i, GPIO.LOW)

        GPIO.output(LED_value, setValue)

    interrupt_timer = currentTime


		


# Guess button
def btn_guess_pressed(channel):
    global interrupt_timer
    global end_of_game
    global win
    # If they've pressed and held the button, clear up the GPIO and take them back to the menu screen
    # Compare the actual value with the user value displayed on the LEDs
    # Change the PWM LED
    # if it's close enough, adjust the buzzer
    # if it's an exact guess:
    # - Disable LEDs and Buzzer
    # - tell the user and prompt them for a name
    # - fetch all the scores
    # - add the new score
    # - sort the scores
    # - Store the scores back to the EEPROM, being sure to update the score count
    

    currentTime = int(round(time.time() * 1000))	#time in millis
	
	#check for debounce
    if (currentTime - interrupt_timer) > 400 and win == 0: 		#200 millis between interrupt i.e. is ok
        #print("Entered")
        
        #time.sleep(0.4)	#not actually debouncing here, sleeping to see if they are holding the button
	
        timer = 8                           # 1 unit = 50 ms, start on 200 to account for debounce delay

        while (GPIO.input(channel) == 0):
            timer +=1
            time.sleep(0.05)

        if timer >= 20:		#held for 1s indicates long press
            #end game
            print("end game")
            end_of_game = 1

        else:
            win = 1
            guess()		#they let go, before 300 millis + 200 debounce i.e. a short press
            end_of_game = 1
            

    interrupt_timer = currentTime
		


# LED Brightness
def accuracy_leds(dif):
    global pwmLED
    # Set the brightness of the LED based on how close the guess is to the answer
    # - The % brightness should be directly proportional to the % "closeness"
    # - For example if the answer is 6 and a user guesses 4, the brightness should be at 4/6*100 = 66%
    # - If they guessed 7, the brightness would be at ((8-7)/(8-6)*100 = 50%

    dc = ((7 - dif)/7) * 100
    pwmLED.ChangeDutyCycle(dc)

	
    

# Sound Buzzer
def trigger_buzzer(dif):
    global buzzer
    # The buzzer operates differently from the LED
    # While we want the brightness of the LED to change(duty cycle), we want the frequency of the buzzer to change
    # The buzzer duty cycle should be left at 50%
    # If the user is off by an absolute value of 3, the buzzer should sound once every second
    # If the user is off by an absolute value of 2, the buzzer should sound twice every second
    # If the user is off by an absolute value of 1, the buzzer should sound 4 times a second
    if dif == 3:
        buzzer.ChangeFrequency(1)
	
    elif dif == 2:
        buzzer.ChangeFrequency(2)

    elif dif == 1:
        buzzer.ChangeFrequency(4)

    if dif > 3 or dif == 0:
        buzzer.ChangeDutyCycle(0)

    else:
        buzzer.ChangeDutyCycle(5)



def guess():
    global score 
    global end_of_game
    score += 1

    difference = min(abs(value - LED_count), abs(LED_count + 8 - value))		# might wrap around

    trigger_buzzer(difference)
    accuracy_leds(difference)

    if difference == 0:
        print("You have won")
        name = input("Please enter a 3 character name: ")
        
        if len(name)!= 3:
            print("Error: your username must be 3 characters")
            name = input("Please enter a 3 character name: ")

        save_scores(name)
        
        #end_of_game = 0

    #time.sleep(0.3)


if __name__ == "__main__":
    try:
        # Call setup function
        setup()
        welcome()
        while True:
            menu()
            pass
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
