# The Champ Timer - Automatic Race Logger
## Complete Setup Guide for Mac, Windows, and Arduino

---

## 📋 OVERVIEW

This package includes programs to automatically capture and log race times from your Champ timer:

1. **Python Logger** (Mac/Windows) - Displays results and saves to CSV spreadsheet
2. **Arduino Logger** - Hardware solution with LEDs, buzzer, optional LCD/SD card
3. **Setup Instructions** for each platform

---

## 🖥️ SETUP FOR MAC/WINDOWS (Python Logger)

### Prerequisites

1. **Install Python 3.8 or newer**
   - **Mac**: Python usually pre-installed, or download from python.org
   - **Windows**: Download from https://python.org/downloads/
   
2. **Install required library**
   Open Terminal (Mac) or Command Prompt (Windows) and run:
   ```bash
   pip install pyserial
   ```
   
   Or if that doesn't work:
   ```bash
   pip3 install pyserial
   python3 -m pip install pyserial
   ```

### Hardware Connection

1. Connect The Champ timer to your computer using:
   - USB cable (if your timer has USB output), OR
   - USB-to-Serial adapter connected to the timer's RS-232 port

2. Power on The Champ timer

3. Verify the connection:
   - **Mac**: Open Terminal and run `ls /dev/tty.*` to see available ports
   - **Windows**: Check Device Manager → Ports (COM & LPT)

### Running the Logger

1. Open Terminal (Mac) or Command Prompt (Windows)

2. Navigate to the folder with the program:
   ```bash
   cd path/to/folder
   ```

3. Run the program:
   ```bash
   python champ_timer_logger.py
   ```
   Or:
   ```bash
   python3 champ_timer_logger.py
   ```

4. Follow the prompts:
   - Select your timer's serial port from the list
   - Enter baudrate (usually 9600)
   - Program will start listening for race data

5. **Run races!** Each time the timer sends data, it will:
   - Display results on screen
   - Save to CSV file in `race_results/` folder
   - Show winner with 🏆 indicator

6. Press `Ctrl+C` to stop logging

### Opening the Spreadsheet

- Navigate to the `race_results/` folder
- Open the CSV file with:
  - **Mac**: Excel, Numbers, or Google Sheets
  - **Windows**: Excel, or import to Google Sheets
  
- The file contains: Race #, Timestamp, Lane 1-4 times, Winner

---

## 🤖 SETUP FOR ARDUINO

### What You Need

**Required:**
- Arduino board (Uno, Mega, Nano, etc.)
- USB cable for Arduino
- Jumper wires
- Connection to The Champ timer's serial output

**Optional (for enhanced features):**
- 4 LEDs + resistors (220Ω) for winner indication
- Buzzer for audio alerts
- 16x2 LCD display with I2C (for local display)
- SD card module (for standalone logging)
- OLED display (alternative to LCD)

### Hardware Wiring

**Basic Connection:**
```
The Champ Timer    →    Arduino
----------------------------------
TX (Data Out)      →    Pin 2 (TIMER_RX_PIN)
GND                →    GND
```

**Optional LEDs:**
```
Arduino Pin 8  →  LED1 (Lane 1) →  220Ω resistor  →  GND
Arduino Pin 9  →  LED2 (Lane 2) →  220Ω resistor  →  GND
Arduino Pin 10 →  LED3 (Lane 3) →  220Ω resistor  →  GND
Arduino Pin 11 →  LED4 (Lane 4) →  220Ω resistor  →  GND
```

**Optional Buzzer:**
```
Arduino Pin 12  →  Buzzer (+)
GND             →  Buzzer (-)
```

**Optional I2C LCD:**
```
LCD SDA  →  Arduino A4 (SDA)
LCD SCL  →  Arduino A5 (SCL)
LCD VCC  →  5V
LCD GND  →  GND
```

**Optional SD Card Module:**
```
SD CS   →  Pin 4
SD MOSI →  Pin 11
SD MISO →  Pin 12
SD SCK  →  Pin 13
SD VCC  →  5V
SD GND  →  GND
```

### Software Setup

1. **Install Arduino IDE**
   - Download from https://arduino.cc/en/software

2. **Install Required Libraries** (if using optional features)
   
   In Arduino IDE: Tools → Manage Libraries, then search and install:
   - `LiquidCrystal I2C` (if using LCD)
   - `Adafruit SSD1306` (if using OLED)
   - `Adafruit GFX Library` (if using OLED)

3. **Open the Arduino sketch**
   - Open `champ_timer_arduino.ino` in Arduino IDE

4. **Configure the code**
   
   Edit these lines at the top of the file:
   ```cpp
   #define TIMER_BAUDRATE 9600   // Match your timer's speed
   #define NUM_LANES 4           // Number of lanes (2, 3, or 4)
   ```
   
   **Enable optional features** by uncommenting:
   ```cpp
   // #define USE_LCD           // Remove // to enable LCD
   // #define USE_OLED          // Remove // to enable OLED
   // #define USE_SD_CARD       // Remove // to enable SD logging
   ```

5. **Upload to Arduino**
   - Connect Arduino via USB
   - Select: Tools → Board → (your Arduino model)
   - Select: Tools → Port → (your Arduino's port)
   - Click Upload button

6. **Test the connection**
   - Open Serial Monitor (Tools → Serial Monitor)
   - Set to 115200 baud
   - You should see "Waiting for race data..."
   - Run a race on The Champ timer
   - Results should appear!

### Using the Arduino Logger

Once programmed, the Arduino will:
1. ✅ Wait for race data from The Champ timer
2. 📊 Display results on Serial Monitor (and LCD/OLED if connected)
3. 💾 Log to SD card (if SD module connected)
4. 💡 Light up winner's LED
5. 🔊 Sound buzzer to celebrate
6. ⏳ Wait 2 seconds before next race

---

## 🔧 TROUBLESHOOTING

### "No serial ports found"
- **Check connections**: USB cable plugged in securely
- **Check drivers**: Some USB-serial adapters need drivers
- **Mac**: May need to allow USB device in Security settings
- **Windows**: Check Device Manager for COM port

### "No data received"
- **Check baudrate**: Common values are 9600, 19200, 38400
- **Check timer settings**: Ensure serial output is enabled on The Champ
- **Check wiring**: TX from timer goes to RX on Arduino/computer
- **Try different port**: Some timers have multiple output formats

### "Data parsing errors"
- The timer's output format may be different than expected
- Check what data looks like in Serial Monitor or raw output
- You may need to customize the `parse_timer_data()` function
- Contact me with a sample of the raw output for help customizing

### Arduino won't upload
- **Check board selection**: Make sure correct Arduino model selected
- **Check port**: Make sure correct USB port selected
- **Close Serial Monitor**: Can't upload while Serial Monitor is open
- **Press reset**: Try pressing reset button on Arduino

---

## 📊 DATA OUTPUT FORMAT

### CSV Spreadsheet Columns:
| Race # | Timestamp | Lane 1 | Lane 2 | Lane 3 | Lane 4 | Winner | Notes |
|--------|-----------|--------|--------|--------|--------|---------|-------|
| 1 | 2026-02-11 14:30:15 | 3.2450 | 3.2678 | 3.3012 | 3.2891 | Lane 1 | |
| 2 | 2026-02-11 14:31:02 | 3.1890 | 3.2103 | 3.2456 | 3.1967 | Lane 1 | |

### Arduino SD Card (races.csv):
```
Race,Lane1,Lane2,Lane3,Lane4,Winner
1,3.2450,3.2678,3.3012,3.2891,Lane 1
2,3.1890,3.2103,3.2456,3.1967,Lane 1
```

---

## 🎯 CUSTOMIZATION IDEAS

### Python Logger:
- Add contestant names instead of just lane numbers
- Create charts/graphs of times
- Calculate statistics (average, best time, etc.)
- Send results via email or text
- Upload to Google Sheets in real-time

### Arduino Logger:
- Add RGB LEDs for color-coded results
- Use larger displays for spectators
- Add buttons for manual race numbering
- Create bracket tournament tracking
- Add Wi-Fi module to post results online

---

## 📞 SUPPORT

If you need help customizing the code for your specific timer format:

1. Run the program and capture what the raw data looks like
2. Take a screenshot or copy the output
3. Share the data format and I can help customize the parser

Common timer output formats:
- `Lane1: 3.2450  Lane2: 3.2678  Lane3: 3.3012  Lane4: 3.2891`
- `3.2450,3.2678,3.3012,3.2891`
- `1:3.2450 2:3.2678 3:3.3012 4:3.2891`
- Tab-separated values

---

## 🏁 QUICK START CHECKLIST

**For Python (Mac/Windows):**
- [ ] Python installed
- [ ] pyserial library installed  
- [ ] Timer connected via USB/serial
- [ ] Run `python champ_timer_logger.py`
- [ ] Select port and baudrate
- [ ] Run races and check CSV file!

**For Arduino:**
- [ ] Arduino IDE installed
- [ ] Libraries installed (if using LCD/OLED/SD)
- [ ] Hardware wired correctly
- [ ] Code configured and uploaded
- [ ] Serial Monitor shows "Ready"
- [ ] Run race and watch LEDs light up!

---

Good luck with your races! 🏁🏆
