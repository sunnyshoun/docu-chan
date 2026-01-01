# impression
The project contains files related to MIDI playback, LED screen display, and video playback. It includes MIDI files, video files, images, and scripts for various functionalities such as conversion, playback control, and LED screen animation. There are separate directories for MIDI player and LED screen components.
# pic18-player/assets/bad_apple.mid
# pic18-player/MidiPlayer/scripts/pyproject.toml
## relationship
### dependencies
- `mido`
- `pyserial`
- `win-precise-time`

### key elements
None specified.

### summary
The file is a `pyproject.toml` for the "scripts" project in the MIDI player directory. It specifies dependencies required for MIDI playback functionality, including libraries like `mido`, `pyserial`, and `win-precise-time`.
## Logic
### objectives
The designer wants to create a Python project for MIDI playback with specific dependencies and requirements.

### logics and flow
1. **Project Metadata**: The `pyproject.toml` file sets up the basic metadata for the project, including the name, version, description, and README file.
   ```toml
   [project]
   name = "scripts"
   version = "0.1.0"
   description = "Add your description here"
   readme = "README.md"
   ```

2. **Python Version Requirement**: The project specifies that it requires Python 3.12 or higher.
   ```toml
   requires-python = ">=3.12"
   ```

3. **Dependencies**: The project lists several dependencies necessary for MIDI playback, including `mido`, `pyserial`, and `win-precise-time`.
   ```toml
   dependencies = [
       "mido>=1.3.3",
       "pyserial>=3.5",
       "win-precise-time>=1.4.2",
   ]
   ```

This setup ensures that the project has all the necessary tools and libraries to function correctly, adhering to the specified Python version and dependencies.
# pic18-player/assets/rolling girl.mp4
# pic18-player/MidiPlayer/scripts/uv.lock
This is a Python package manifest file in the form of a `pyproject.toml` or similar format. It describes the dependencies and metadata for a project named "scripts". Here's a breakdown:

- **Package Name**: `scripts`
- **Version**: `0.1.0`
- **Source**: The source is local, indicated by `{ virtual = "." }`, meaning it's part of the current directory.

### Dependencies:
The package depends on three other packages:
1. **mido**
   - Minimum version: `>=1.3.3`
2. **pyserial**
   - Minimum version: `>=3.5`
3. **win-precise-time**
   - Minimum version: `>=1.4.2`

### Metadata:
The metadata section specifies that the package requires these dependencies to be installed.

### Additional Information:
- The project uses a virtual environment, indicated by `{ virtual = "." }`.
- It includes wheels for Windows platforms (both 32-bit and 64-bit) for `win-precise-time`.

This manifest file is typically used with build systems like `pip` or `poetry` to manage dependencies and ensure that the project can be installed and run correctly.
 ```json
{
  "name": "scripts",
  "version": "0.1.0",
  "source": {
    "virtual": "."
  },
  "dependencies": [
    {
      "name": "mido",
      "specifier": ">=1.3.3"
    },
    {
      "name": "pyserial",
      "specifier": ">=3.5"
    },
    {
      "name": "win-precise-time",
      "specifier": ">=1.4.2"
    }
  ],
  "package_metadata": {
    "requires-dist": [
      {
        "name": "mido",
        "specifier": ">=1.3.3"
      },
      {
        "name": "pyserial",
        "specifier": ">=3.5"
      },
      {
        "name": "win-precise-time",
        "specifier": ">=1.4.2"
      }
    ]
  },
  "packages": [
    {
      "name": "mido",
      "version": "1.3.3",
      "source": {
        "registry": "https://pypi.org/simple"
      },
      "dependencies": [
        {
          "name": "python",
          "specifier": ">=3.6"
        }
      ]
    },
    {
      "name": "pyserial",
      "version": "3.5",
      "source": {
        "registry": "https://pypi.org/simple"
      },
      "dependencies": [
        {
          "name": "python",
          "specifier": ">=2.7, !=3.0.*, !=3.1.*"
        }
      ]
    },
    {
      "name": "win-precise-time",
      "version": "1.4.2",
      "source": {
        "registry": "https://pypi.org/simple"
      },
      "dependencies": [
        {
          "name": "python",
          "specifier": ">=3.6"
        }
      ]
    }
  ]
}
```
# pic18-player/doc/System diagram.md
## relationship
### dependencies
- None

### key elements
- `System diagram.md`

### summary
The file "pic18-player/doc/System diagram.md" provides a detailed system circuit diagram and specifications for the hardware components of the project, including the PIC18F4520 microcontroller, WS2812 LED matrix, and audio output modules. The diagram illustrates the connections between these components and outlines important hardware specifications such as power supply requirements and clock distribution.
## Logic
### objectives
The designer wants to create a system that controls an LED display and plays audio using a PIC18F4520 microcontroller. The system should be able to handle multiple LED panels and manage audio output through UART communication.

### logics and flow
1. **Audio System**:
   - The PIC18F4520 (referred to as "Audio MCU") is connected to a buzzer circuit via UART.
   - The audio data is sent from the host computer to the Audio MCU over UART, which then controls the buzzer.

2. **LED Display System**:
   - The system uses 8 PIC18F4520 microcontrollers (referred to as "LED MCUs") to control a total of 16 WS2812 LED panels.
   - Each group of 2 PICs controls 4 LED panels.
   - A shared 10MHz active crystal oscillator is used by all the PICs, which is connected to their `OSC1` pins and left floating on `OSC2`.
   - The host computer communicates with each group of PICs via UART ports (UART_LED_A, UART_LED_B, UART_LED_C, UART_LED_D).
   - Each LED panel is controlled by setting specific bits in the PIC's registers.

3. **Power Supply**:
   - The WS2812 LED panels require a significant amount of power, so they are powered by an external high-current power supply.
   - The PICs and other components are powered from a 5V 10A external power source.

4. **Signal Integrity**:
   - To ensure proper signal transmission over UART, the designer has provided guidelines for consistent wiring lengths and avoiding signal attenuation or interference, especially with the shared oscillator.

This system allows for centralized control of both audio output and LED display through a single host computer, making it versatile for various applications that require synchronized audio and visual feedback.
# pic18-player/MidiPlayer/scripts/test_play.py
## relationship
### dependencies
- `serial`: For serial communication.
- `time`: For time-related operations.
- `json`: For JSON file handling.
- `win_precise_time as wdt`: For precise timing.

### key elements
- `send_timed_midi_to_pic18(events)`: Function to send MIDI events with timing precision.
- `UART_PORT` and `BAUD_RATE`: Configuration for serial port connection.
- Main block for reading JSON file, establishing serial connection, and playing MIDI events in a loop.

### summary
The script `test_play.py` is designed to play MIDI events on a PIC18 microcontroller using a serial connection. It reads MIDI event data from a JSON file and sends these events with precise timing control. The script handles serial communication, error checking, and provides basic user interaction through keyboard interrupts.
## Logic
### objectives
The script `test_play.py` is designed to play MIDI events from a JSON file on a PIC18 microcontroller using a serial connection. It ensures that each MIDI event is sent at the correct time as specified by its timestamp.

### logics and flow
1. **Initialization**:
   - The script initializes a serial connection to the PIC18 microcontroller using the `serial` library.
   - It sets up the UART port and baud rate based on user configuration (`UART_PORT` and `BAUD_RATE`).

2. **Loading MIDI Events**:
   - The script reads MIDI events from a JSON file named `play.json`.

3. **Sending MIDI Events**:
   - The script defines a function `send_timed_midi_to_pic18(events)` that iterates through the list of MIDI events.
   - For each event, it calculates the delay needed to ensure the event is sent at the correct time using the `wdt.sleep(delay_needed)` function from the `win_precise_time` module.
   - If the calculated delay is negative (indicating a significant lag), it prints a warning message.

4. **Sending Data**:
   - The script prepares and sends each MIDI event as two bytes (`status_byte` and `data1_byte`) over the serial connection.
   - It records and displays the actual time of sending for debugging purposes.

5. **Error Handling**:
   - The script handles potential errors during the serial communication, such as timeouts or other exceptions, by printing error messages and breaking out of the loop.

6. **Main Execution Loop**:
   - The script enters a main execution loop where it continuously calls `send_timed_midi_to_pic18(midi_events_array)` to play the MIDI events.
   - It waits for 1 second between each iteration using `wdt.sleep(1)`.
   - If a keyboard interrupt (Ctrl+C) is detected, it sends a reset command to the PIC18 and closes the serial connection.

7. **Cleanup**:
   - The script ensures that the serial connection is closed properly in the `finally` block to release resources.

### Key Expressions
- `wdt.sleep(delay_needed)` - Ensures precise timing of MIDI event transmission.
- `ser.write(bytes_to_send)` - Sends data over the serial connection.
- `try...except` blocks - Handle potential errors during serial communication.
# pic18-player/README.md
## relationship
### dependencies
- FFmpeg (for video/image processing)
- Python 3.x (for script execution)
- MPLAB X IDE and XC8 Compiler (for C language development)

### key elements
- `main.py` (project main script)
- `MidiPlayer/main.c` (PIC18 music player software main program)
- `LEDScreen/main.c` (PIC18 screen control software main program)
- `MidiPlayer/scripts/convertor.py` (MIDI to C array/binary converter script)
- `LEDScreen/scripts/pic_extractor.py` (video/image extraction tool script)

### summary
The project is a multimedia playback system based on the PIC18 microcontroller, focusing on MIDI music decoding and LED screen animation display. It includes two main modules: MidiPlayer for music playback and LEDScreen for LED screen display. The system uses Python scripts for pre-processing multimedia files and FFmpeg for video/image processing. The C code is developed using MPLAB X IDE and XC8 Compiler.
## Logic
### objectives
The designer wants to create an embedded multimedia player system based on the PIC18 microcontroller, capable of playing MIDI music and displaying animations on an LED matrix screen. The project aims to integrate hardware control software (C language) with computer-side resource conversion tools (Python).

### logics and flow
1. **MIDI Player Module**
   - Parse MIDI file formats.
   - Control a buzzer or speaker to play music using the PIC18 microcontroller.
   - Include test tracks like "Undertale" and "Bad Apple!!".

2. **LED Screen Module**
   - Display images and animations on an LED matrix screen.
   - Support frame extraction and conversion for videos, including a Bad Apple animation demonstration.

3. **System Architecture**
   - Computer-side scripts preprocess multimedia files, package the data, and transmit it via UART to the microcontroller.
   - The system consists of video processing and audio (MIDI) processing modules.
   - Video processing involves extracting time stamps and images using FFmpeg.
   - Audio processing includes parsing MIDI files, splitting chords, packing channels into packets, and synchronizing with packets.
   - The processed data is converted to a bit stream and transmitted via UART to the PIC18 device.

4. **Environment Setup**
   - Hardware requirements include a PIC18 microcontroller, speaker circuitry, LED matrix display module, and programmer (e.g., PICkit).
   - Software development environment for C language includes MPLAB X IDE and XC8 C Compiler.
   - Script execution environment for Python and tools requires FFmpeg for multimedia processing.

5. **Usage Instructions**
   - To add MIDI music to the microcontroller:
     1. Place `.mid` files in the `assets/` directory.
     2. Use `MidiPlayer/scripts/convertor.py` to convert MIDI files into a format readable by the microcontroller (e.g., C Array or binary data).
     ```bash
     cd MidiPlayer/scripts
     python convertor.py
     ```

This structure ensures that the project is modular, with clear separation of hardware and software components, and provides a comprehensive guide for setting up and using the system.
# pic18-player/LEDScreen/scripts/images/frame2.jpg
Since the provided image (`frame2.jpg`) is a single static frame (likely for LED screen animation), it doesn’t inherently show **module relationships** in the system. However, based on the **filepath context** (`pic18-player/LEDScreen/scripts/images/frame2.jpg`), here’s a structured breakdown of inferred relationships:

---

## **Relationship**
### **Key Elements**
1. **`pic18-player`** – Root project directory (likely contains core MIDI/LED/video logic).
2. **`LEDScreen`** – Dedicated module for LED display control (e.g., animations, rendering).
   - **`scripts/`** – Scripts to process/animate LED frames.
   - **`images/`** – Static frames (like `frame2.jpg`) used in LED animations.
3. **`frame2.jpg`** – A single frame in an LED animation sequence (input for `LEDScreen`).

### **Summary**
- **`LEDScreen`** depends on **`scripts/`** to load/process frames (e.g., `frame2.jpg`) for LED animations.
- **`frame2.jpg`** is a **data input** for the LED module, not a standalone module itself.
- **No direct relationships** to MIDI/video modules are visible here—this is **LED-specific**.
- **Not important** for system-wide architecture (focus on `LEDScreen`’s role in the hierarchy).

---
**Note:** For full system relationships, analyze MIDI/video directories (e.g., `MIDIPlayer`, `VideoPlayer`) to see how `LEDScreen` integrates with them.
## Logic
### objectives
- **Primary Objective**: Display a static or animated frame on an LED screen for visual synchronization with MIDI playback or video playback. This frame is likely part of a larger sequence (e.g., for LED animations, visualizers, or synchronized multimedia displays).

- **Secondary Objective**: Ensure the image is compatible with the LED screen’s resolution, color depth, and refresh rate for smooth rendering.

---
### logics and flow
1. **Image Source**:
   - `frame2.jpg` is a **static image** (not a transition or dynamic state change) meant to be part of a sequence of frames (e.g., `frame1.jpg`, `frame2.jpg`, etc.).
   - **Not important**: No explicit data flow or state transitions are depicted in this single image alone. It is a **static asset** for rendering.

2. **Integration with LED Screen**:
   - The image is likely processed by a script (e.g., in `pic18-player/LEDScreen/scripts/`) to:
     - Convert the JPEG to a format compatible with the LED matrix (e.g., bitmap, PPM, or binary data).
     - Scale/resize the image to match the LED screen’s resolution (e.g., 32x32, 64x64 pixels).
     - Apply color mapping (e.g., RGBW or monochrome) based on the LED screen’s capabilities.
     - Send the data to the LED controller via serial (UART/SPI/I2C) or direct memory mapping.

3. **Temporal Context (Not Shown in Image)**:
   - If this is part of an animation sequence, transitions between frames (e.g., `frame1.jpg` → `frame2.jpg`) would be handled by:
     - A **timer-based script** (e.g., delay between frames).
     - A **MIDI-triggered sequence** (e.g., frame changes synchronized to MIDI beats).
     - A **video playback loop** (e.g., frames extracted from a video file for LED visualization).

4. **Data Flow (Inferred, Not Visible in Image)**:
   - **Input**: `frame2.jpg` (static image file).
   - **Processing**:
     1. Image decoding (JPEG → pixel data).
     2. Resizing/color conversion.
     3. Buffering for LED output.
   - **Output**: Rendered frame on the LED screen.

---
**Key Takeaway**: This image is a **static frame** in a larger system. No transitions or dynamic states are visible here; the logic lies in the **scripts/directories** handling frame sequences, MIDI/vide synchronization, and LED rendering. Mark as **not important for state/transition analysis** in isolation.
# pic18-player/LEDScreen/scripts/pyproject.toml
## relationship
### dependencies
- `pillow>=12.0.0`
- `pyserial>=3.5`

### key elements
- Not specified in the provided content.

### summary
The file `pic18-player/LEDScreen/scripts/pyproject.toml` is a configuration file for a Python project named "scripts" with version 0.1.0. It specifies dependencies on `pillow` and `pyserial`, indicating that these libraries are required for the project to run. The purpose of this file is to manage project metadata and dependencies, ensuring that all necessary packages are installed when the project is set up or updated.
## Logic
### objectives
The designer wants to set up a Python project for controlling an LED screen using the PIC18 microcontroller. The project should include dependencies for image processing and serial communication.

### logics and flow
1. **Project Metadata**: Define basic metadata such as the project name, version, description, README file, and required Python version.
2. **Dependencies**: List necessary packages that the project depends on, including `pillow` for image processing and `pyserial` for serial communication.

```toml
[project]
name = "scripts"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.12"

[project.dependencies]
pillow = ">=12.0.0"
pyserial = ">=3.5"
```
# pic18-player/doc/LED screen.jpg
The image you provided appears to be a block diagram for a microcontroller-based system using PIC18F4620 microcontrollers and WS2812B (commonly known as NeoPixel) LED modules. Here’s a detailed breakdown of the diagram:

### Top Section:
1. **Microcontrollers:**
   - Two PIC18F4620 microcontrollers are shown, each connected to a 10 MHz clock source.
   - Each microcontroller has its pins labeled for communication and control.

2. **LED Communication:**
   - Each PIC18F4620 is connected to WS2812B LED modules (indicated as "WS2812 #0", "#1", "#2", "#3").
   - The WS2812B LEDs are used for addressable LED displays, where each LED can be individually controlled.

### Bottom Section:
1. **Blocks Representation:**
   - The bottom section shows a hierarchical block diagram of how the LEDs are organized into blocks.
   - **Block #0** contains four LEDs labeled LED #0, LED #1, LED #2, and LED #3.
   - **Blocks #1, #2, and #3** are shown as larger blocks, indicating that they contain multiple LEDs or sub-blocks.

### Explanation of Blocks:
- **Block #0:**
  - This block is detailed with individual LEDs (LED #0, LED #1, LED #2, LED #3).
  - It appears to be a specific grouping of LEDs directly connected to the microcontroller.

- **Blocks #1, #2, and #3:**
  - These blocks are not detailed in the image but are represented as larger units, indicating that they may contain multiple LEDs or further sub-blocks.
  - The hierarchical structure suggests that each block can be controlled individually or collectively by the microcontrollers.

### Summary:
- **Microcontroller Control:**
  - Each PIC18F4620 microcontroller controls a set of WS2812B LEDs, which can be individually addressed and controlled.
  - The LEDs are organized into blocks, with Block #0 showing individual LEDs and Blocks #1, #2, and #3 representing larger groups of LEDs.

- **Purpose:**
  - This setup is likely used for creating dynamic LED displays, such as a matrix or a scrolling text display, where each LED can be controlled independently to create complex visual effects.

### Additional Notes:
- **WS2812B (NeoPixel) LEDs:**
  - These LEDs are known for their ease of use and the ability to control each LED individually over a single data line using a specific protocol.

- **Microcontroller Communication:**
  - The communication between the microcontrollers and LEDs is typically done via serial communication, where each LED receives a bitstream to determine its color and state.

This setup is versatile and can be used in various applications, such as decorative lighting, signage, or interactive displays.
The image you provided appears to be a conceptual diagram for a modular system involving microcontrollers and LED displays. Here's a detailed breakdown of the components and their possible functions based on the image:

### Top Section:
1. **Microcontroller Setup:**
   - **PIC18F4520 Microcontroller:** This is a specific type of microcontroller from Microchip Technology. It is used for controlling the system.
   - **Clock Signal:** The 10 MHz clock signal is likely used to provide timing for the microcontroller operations.

2. **Communication:**
   - **Serial Communication:** The connections labeled "Tx Port #0" and "Rx Port #0" indicate serial communication ports for data transmission and reception.

3. **LED Display:**
   - **WS2812B LEDs:** These are addressable RGB LEDs, often used for creating LED matrices or strips. Each LED can be individually controlled to display different colors.

### Middle Section:
- **Block #0:**
  - This block contains four LEDs labeled LED #0, LED #2, LED #2, and LED #3. It seems to be a specific module or segment of the system, possibly a small LED display or indicator panel.

### Bottom Section:
- **Modular Blocks:**
  - **Block #2 and Block #3:** These are additional modular blocks that can be connected to the system. Each block likely contains similar LED modules or other components that can be controlled by the microcontroller.

### Overall System:
- **Modular Design:** The system appears to be designed with modularity in mind, allowing for easy expansion and reconfiguration. Each block can be added or removed as needed, providing flexibility in the system's configuration.

### Possible Applications:
- **LED Art or Displays:** The system could be used for creating dynamic LED displays, such as digital art installations, signage, or decorative lighting.
- **Industrial Control Panels:** It could be used in industrial applications where visual feedback is required.
- **Educational Projects:** This setup could be used for educational purposes to teach about microcontrollers, serial communication, and modular electronics.

### Summary:
The image illustrates a modular system where a PIC18F4520 microcontroller controls multiple LED modules (using WS2812B LEDs) through serial communication. The modular blocks allow for scalable and flexible configurations, making it suitable for various applications involving LED displays.
# pic18-player/MidiPlayer/main.h
## relationship
### dependencies
- None

### key elements
- `TOGGLE_CYCLE[]`: An array of values representing toggle cycles for MIDI notes.

### summary
The file "pic18-player/MidiPlayer/main.h" contains configuration settings and definitions specific to the PIC18 microcontroller, including oscillator settings, watchdog timer configurations, and constants used in MIDI playback. The key element is an array defining toggle cycles for MIDI notes, which is essential for controlling the timing of MIDI note events.
## Logic
### objectives
The primary objective of this file is to configure the hardware settings and define constants for a MIDI player project on an 8-bit microcontroller (PIC18F series). This includes setting up the oscillator, enabling/disabling various peripherals, defining timing parameters, and preparing arrays for MIDI note frequencies.

### logics and flow
The code starts with preprocessor directives to include necessary configurations for the microcontroller. These configurations are crucial for the hardware's operation, such as selecting the oscillator type and enabling or disabling certain features like the watchdog timer and power-up reset. The constants defined in the file are used throughout the project to ensure consistency and ease of maintenance.

1. **Configuration Bits**: The code begins by setting up configuration bits using `#pragma config`. These bits control various aspects of the microcontroller's behavior, such as oscillator selection, brown-out reset settings, watchdog timer operation, and power-up timer functionality. For example:
   ```c
   #pragma config OSC = HSPLL      // Oscillator Selection bits (HS oscillator)
   ```
   This line specifies that the high-speed crystal oscillator with PLL is used.

2. **Oscillator Frequency**: The `#define _XTAL_FREQ 4e7` directive sets the external crystal frequency to 40 MHz, which is essential for accurate timing and MIDI note generation.

3. **Baud Rate**: The `#define BAUD 38400` directive defines the baud rate for serial communication, which is crucial for MIDI data transmission.

4. **MIDI Note Frequencies**: The code includes an array `TOGGLE_CYCLE[]` that stores the frequency values for MIDI notes. This array is used to generate accurate note frequencies when playing MIDI files. For example:
   ```c
   static unsigned TOGGLE_CYCLE[] = {
   6115,
   5772,
   5448,
   ...
   ```
   Each value in the array corresponds to a specific MIDI note frequency.

In summary, this file sets up the hardware configuration and defines constants necessary for the MIDI player project. It ensures that the microcontroller is properly configured for optimal performance and that all components are ready for their respective tasks, such as playing MIDI files and controlling the LED screen display.
# pic18-player/LEDScreen/scripts/uv.lock
 ```json
{
  "packages": [
    {
      "name": "Pillow",
      "version": "8.2.0",
      "source": { "registry": "https://pypi.org/simple" },
      "sdist": {
        "url": "https://files.pythonhosted.org/packages/3e/f5/9d4b7c6a1f8a5b9b2e2e0b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b
 ```json
{
  "packages": [
    {
      "name": "Pillow",
      "version": "8.4.0",
      "source": { "registry": "https://pypi.org/simple" },
      "sdist": {
        "url": "https://files.pythonhosted.org/packages/3e/f5/a7c9d6b2f1a9c8b9e6e0e4e5e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e
# pic18-player/LEDScreen/scripts/.python-version
## relationship
### dependencies
- Python 3.12

### key elements
- Not applicable (This file specifies the Python version, not code or functionality)

### summary
This file specifies that the project requires Python version 3.12 for execution. It does not contain any code or functionality relevant to the project's core features.
## Logic
### objectives
The objective of this file is to specify the Python version required for the scripts in the `pic18-player/LEDScreen/scripts` directory.

### logics and flow
The file contains a single line that specifies the Python version. This version will be used by any script within the `scripts` directory when running on a system that supports specifying Python versions through such files, like some IDEs or build systems.
# pic18-player/LEDScreen/scripts/pic_extractor.py
## relationship
### dependencies
- `argparse`
- `pathlib`
- `subprocess`
- `os`
- `sys`

### key elements
- `check_ffmpeg_exists`: Function to check if FFmpeg is installed and accessible.
- `extract`: Function to convert video files to sequence images.
- `main`: Main function to handle command-line arguments and call the extraction function.

### summary
The file `pic18-player/LEDScreen/scripts/pic_extractor.py` contains functions for checking the existence of FFmpeg, extracting images from videos using FFmpeg, and handling command-line arguments. It is used for converting video files into sequence images with specified parameters such as size and FPS.
## Logic
### objectives
The designer wants to create a script that can extract frames from video files and save them as image sequences. The script should allow for customization of the output size, frame rate, and file naming convention.

### logics and flow
1. **Argument Parsing**: The script uses `argparse` to parse command-line arguments, allowing users to specify the input video file path, FFmpeg executable path, output size, output file name pattern, and frame rate.
2. **FFmpeg Existence Check**: Before proceeding with the extraction, the script checks if the FFmpeg executable exists in the system environment using the `check_ffmpeg_exists` function. If FFmpeg is not found or fails to execute correctly, an error message is printed, and the script exits.
3. **Input File Validation**: The script verifies that the input video file exists. If it does not, an error message is printed, and the script exits.
4. **Output Directory Creation**: If the output directory specified in the `output_path` argument does not exist, it is created using `pathlib.Path`.
5. **FFmpeg Command Construction**: The script constructs a FFmpeg command to extract frames from the video file based on the provided arguments. The command includes options for frame rate (`fps`), cropping, and scaling.
6. **Command Execution**: The constructed FFmpeg command is executed using `subprocess.run`. If the command fails (e.g., due to an error in the FFmpeg executable or a problem with the input file), an error message is printed, and the script exits.
7. **Logging**: Throughout the process, the script prints detailed logs of the commands being executed and any errors encountered.

### Code Snippets
```python
def check_ffmpeg_exists(path: str):
    try:
        subprocess.run(
            [path, '-version'],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return True
    except FileNotFoundError:
        print("找不到 'ffmpeg' 命令。請確保它已安裝並添加到系統環境變數 PATH 中。")
        return False
    except subprocess.CalledProcessError:
        print("FFmpeg 存在但執行失敗。")
        return True

def extract(exec_path: str, input_path: str, output_path: str, fps: int, size: int):
    out_path = pathlib.Path(output_path)
    if not out_path.parent.exists():
        print("mkdir", out_path.parent)
        out_path.parent.mkdir(parents=True)
    
    filter_complex = (
        f"fps={fps},"
        f"crop=ih:ih,"
        f"scale={size}:{size}"
    )
    command = [
        exec_path,
        '-i', input_path,
        '-vf', filter_complex,
        '-y',
        output_path
    ]
    
    print("\n--- 執行命令 ---")
    print(f"命令: {' '.join(command)}")
    print("------------------")
    
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=False,
            text=True
        )
    except subprocess.CalledProcessError as e:
        print("\n❌ 錯誤：FFmpeg 執行失敗。")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 発生未知錯誤: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="將影片檔案轉換為序列照片。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('file_path', type=str, help="要處理的影片檔案路徑")
    parser.add_argument('--path', type=str, default="ffmpeg", help="ffmpeg path")
    parser.add_argument('-s', '--size', type=int, default=32, help="照片的長寬")
    parser.add_argument('-o', "--output", type=str, default="output_%04d.png", help="照片檔案名稱")
    parser.add_argument("--fps", type=int, default=30, help="照片檔案名稱")
    
    args = parser.parse_args()
    
    if not check_ffmpeg_exists(args.path):
        print(f"錯誤：找不到ffmpeg -> {args.path}")
        sys.exit(1)
    
    if not os.path.exists(args.file_path):
        print(f"錯誤：找不到輸入檔案 -> {args.file_path}")
        sys.exit(1)
    
    extract(
```
# pic18-player/LEDScreen/scripts/main.py
## relationship
### dependencies
- `serial` (not implemented in this file)
- `time` (not implemented in this file)
- `os` (not implemented in this file)
- `glob` (not implemented in this file)
- `PIL.Image, PIL.ImageEnhance` (not implemented in this file)

### key elements
- `COM_CONFIG`
- `BAUD_RATE`
- `TARGET_FPS`
- `FRAME_TIME`
- `IMG_FOLDER`
- `CONTRAST_FACTOR`
- `get_packed_pixels`
- `main`

### summary
The file `pic18-player/LEDScreen/scripts/main.py` is a script for controlling an LED screen using MIDI data. It uses the `serial`, `time`, `os`, and `glob` modules to manage serial communication, timing, file operations, and image globbing, respectively. The script defines constants for COM port configuration, baud rate, target FPS, frame time, image folder path, and contrast factor. It includes a function `get_packed_pixels` to generate pixel data packets and a main function `main` to open serial ports, read images, enhance their contrast, pack the pixels, and send them over the serial ports at the specified FPS. The script handles exceptions and ensures that the playback is synchronized with the target FPS.
## Logic
### objectives
The designer wants to achieve a system that can play images on an LED screen using multiple PIC microcontrollers connected via COM ports. The system should handle image loading, contrast enhancement, and serial communication to control the LED display.

### logics and flow
1. **Configuration Setup**:
   - Define COM port configurations for different global IDs.
   - Set baud rate and target FPS (frames per second) for the playback.

2. **Image Loading and Processing**:
   - Load images from a specified folder.
   - Sort the images in ascending order based on their filenames.
   - Open each image, convert it to RGB format, and resize it to 64x64 pixels.

3. **Contrast Enhancement**:
   - Use `PIL.ImageEnhance.Contrast` to enhance the contrast of the image by a factor specified in `CONTRAST_FACTOR`.

4. **Serial Communication**:
   - Initialize serial connections with each COM port.
   - For each image, pack the pixel data into a format that can be sent over the serial connection.
   - Send the packed data to the corresponding PIC microcontrollers via their respective COM ports.

5. **Frame Rate Control**:
   - Calculate the time taken to process and send each frame.
   - If the processing time is less than the target FPS, introduce a delay to maintain the desired frame rate.

6. **Error Handling**:
   - Handle exceptions that may occur during serial communication or image processing.

### Key Expressions
- `packet.append(0xFF)` - Initializes the synchronization byte for each packet.
- `enhancer.enhance(CONTRAST_FACTOR)` - Enhances the contrast of the image based on the specified factor.
- `time.sleep(FRAME_TIME)` - Delays execution to maintain the target FPS.
# pic18-player/assets/Spear_Of_Justice_6ch.mid
# pic18-player/.gitignore
## relationship
### dependencies
- None

### key elements
- None

### summary
The `.gitignore` file specifies directories to be ignored by Git, namely `.vscode/` and `tmp/`. This ensures that Visual Studio Code configuration files and temporary files are not tracked by version control.
## Logic
### objectives
The `.gitignore` file is used to specify intentionally untracked files that Git should ignore.

### logics and flow
The `.gitignore` file in the `pic18-player` directory specifies two directories to be ignored by Git:
- `.vscode/`: This directory typically contains Visual Studio Code-specific settings and configurations, which are not necessary for version control.
- `tmp/`: This directory likely contains temporary files that should not be tracked by Git.

Each line in the `.gitignore` file indicates a pattern of files or directories to ignore.
# pic18-player/MidiPlayer/scripts/convertor.py
## relationship
### dependencies
- `mido`: A Python library for working with MIDI files.
- `json`: A standard Python library for parsing JSON data.
- `argparse`: A standard Python library for command-line argument parsing.
- `sys`: A standard Python library for system-specific parameters and functions.

### key elements
- `convertor.py`: Contains functions for converting MIDI files, including reading MIDI events, sorting them by time, and processing note events to allocate logical channels.

### summary
The `convertor.py` file is a script that handles the conversion of MIDI files. It includes functions to read MIDI events from a file, sort these events by their absolute time, and process note events to assign logical channels. The script uses the `mido` library for MIDI file handling and standard Python libraries for parsing JSON data, command-line arguments, and system-specific operations.
## Logic
### objectives
The designer wants to create a script that can convert MIDI files into a format suitable for playback, specifically focusing on extracting and organizing MIDI events such as Note On/Off events. The script also aims to allocate logical channels for these events to facilitate playback control.

### logics and flow
1. **Import necessary libraries**: The script starts by importing required modules like `pathlib`, `mido`, `json`, `argparse`, `sys`, and `re`.

2. **Define constants and functions**:
   - `DRUM_PAT` is a regular expression pattern to identify drum tracks.
   - `get_note_name(note_number)` converts MIDI note numbers (0-127) into standard musical note names (e.g., C4, F#5).

3. **Read and process MIDI files**:
   - `get_sorted_midi_events(file_path)` reads a MIDI file, extracts Note On/Off events from all tracks, converts them to absolute time, and sorts them by time.
     - It handles exceptions for file not found or other errors during file reading.
     - It processes each track, identifying drum tracks and filtering out non-note messages.
     - It constructs a list of event dictionaries containing details like absolute time, track index, note number, and note name.

4. **Process MIDI events**:
   - `process_midi_events(sorted_array, tracks, tpb, bpm)` handles the allocation of logical channels for the MIDI events.
     - It initializes channel states to keep track of which channels are currently in use.
     - It defines a helper function `find_free_channel()` to find an available channel or create a new one if needed.
     - It iterates through the sorted events, assigning each event to a channel based on its original track and type (Note On/Off).

5. **Output the result**: The script outputs the processed MIDI events with their allocated channels.

### Key Expressions
- `accumulated_time += msg.time`: Accumulates the time for each message.
- `event_data = {...}`: Constructs a dictionary containing event details.
- `channel_states[i] = {'status': 'off', ...}`: Initializes channel states.
- `assigned_channel = find_free_channel()`: Finds or creates an available channel.
# pic18-player/LEDScreen/main.c
## relationship
### dependencies
- `xc.h` - Microchip XC8 C Compiler header file.
- None other specific modules are directly referenced in this file.

### key elements
- `main.c`
  - `Init_System()`: Initializes the system.
  - `Check_Hardware_ID()`: Reads the hardware ID from RA0 pin.
  - `Init_UART_921600()`: Initializes UART communication at 921600 bps.
  - `Unpack_And_Show()`: Unpacks and displays data.

### summary
The file `main.c` is a critical component of the LED screen project, handling hardware initialization, UART communication setup, and data unpacking for display. It uses specific configuration bits for the PIC18F4520 microcontroller and includes functions for reading hardware IDs, initializing UART at 921600 bps, and managing data unpacking and display.
## Logic
### objectives
The primary objective of this code is to control an LED screen using a PIC18F4520 microcontroller, specifically for receiving and displaying data over UART. The system should be able to synchronize with another device, check its ID, receive data packets, and display the received data on an LED screen.

### logics and flow
The code is structured to handle UART communication, state management, and LED screen control. Here's a detailed breakdown of the logic:

1. **Initialization**:
   - The `Init_System()` function initializes the system by setting up the microcontroller configuration bits.
   - The `Check_Hardware_ID()` function reads the hardware ID from the RA0 pin to determine which device is connected (either 0 or 1).
   - The `Init_UART_921600()` function configures the UART for communication at 921600 bps.

2. **Interrupt Service Routine (ISR)**:
   - The ISR handles UART receive interrupts. It processes incoming data packets and updates the state machine (`rx_state`) based on the received data.
   - When a synchronization byte (`0xFF`) is received, it transitions to `STATE_CHECK_ID`.
   - If the hardware ID matches, it transitions to `STATE_RECEIVE_DATA` and starts receiving data into the `vram`.

3. **Main Loop**:
   - The main loop continuously checks if new data is ready to be displayed.
   - When `frame_ready` is set, it disables interrupts, calls `Unpack_And_Show()` to process and display the data, and then re-enables interrupts.

4. **Data Processing**:
   - The `Unpack_And_Show()` function processes the received data by unpacking it from a compressed format into the `vram`.
   - It uses an in-place expansion algorithm to decompress the data.
   - After processing, it calls `WS2812_Send_Byte_RB0()` and `WS2812_Send_Byte_RB1()` to send the uncompressed data to the LED screen.

### Key Expressions
- **`#pragma config OSC = HSPLL`**: Configures the oscillator to use a high-speed PLL.
- **`RCSTAbits.OERR`**: Checks for UART receive buffer overflow error.
- **`rx_state`**: Manages the state of the data reception process (`STATE_WAIT_SYNC`, `STATE_CHECK_ID`, `STATE_RECEIVE_DATA`).
- **`frame_ready`**: Indicates when a complete frame is ready to be displayed.

This code effectively manages UART communication, processes incoming data packets, and controls an LED screen using a PIC18F4520 microcontroller.
# pic18-player/assets/雨露霜雪.mp4
# pic18-player/uv.lock
 ```json
{
  "package": "Pillow",
  "version": "12.0.0",
  "platforms": [
    {
      "os": "Linux",
      "architecture": "x86_64",
      "tag": "manylinux2014_x86_64"
    },
    {
      "os": "Linux",
      "architecture": "aarch64",
      "tag": "manylinux2014_aarch64"
    },
    {
      "os": "macOS",
      "architecture": "x86_64",
      "tag": "macosx_10_15_x86_64"
    },
    {
      "os": "macOS",
      "architecture": "arm64",
      "tag": "macosx_11_0_arm64"
    },
    {
      "os": "Windows",
      "architecture": "x86_64",
      "tag": "cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64"
    },
    {
      "os": "Windows",
      "architecture": "aarch64",
      "tag": "cp314-cp314t-manylinux2014_aarch64.manylinux_2_27_aarch64.manylinux_2_28_aarch64"
    },
    {
      "os": "Linux",
      "architecture": "x86_64",
      "tag": "manylinux2014_x86_64.manylinux_2_17_x86_64"
    },
    {
      "os": "Linux",
      "architecture": "aarch64",
      "tag": "manylinux2014_aarch64.manylinux_2_27_aarch64.manylinux_2_28_aarch64"
    }
  ]
}
```
The provided text is a list of Python wheel files for the Pillow library version 12.0.0. Each file corresponds to a different platform and Python architecture:

1. **musllinux_1_1_x86_64**: This is a Linux wheel for musl libc, targeting x86_64 architecture.
2. **manylinux_2_35_x86_64**: A manylinux wheel compatible with Python 3.5 and later on x86_64 systems.
3. **manylinux_2_31_x86_64**: Similar to the above, but targeting a slightly older version of manylinux (2.31).
4. **manylinux_2_24_aarch64**: A manylinux wheel for ARM 64-bit architecture.
5. **musllinux_1_1_aarch64**: A musl libc wheel for ARM 64-bit architecture.

Each entry includes:
- `url`: The URL where the wheel file can be downloaded.
- `hash`: The SHA256 hash of the file to ensure its integrity.
- `size`: The size of the file in bytes.
- `upload-time`: The timestamp when the file was uploaded to the repository.

These wheels are designed for different operating systems and architectures, allowing Pillow to be installed on a wide range of Python environments.
# pic18-player/MidiPlayer/scripts/.gitignore
## relationship
### dependencies
- None

### key elements
- play.json: Configuration file for the project.
- .venv/: Virtual environment directory for Python packages.
- __pycache__: Directory containing compiled Python files.

### summary
The `.gitignore` file specifies that `play.json`, virtual environment directories, and compiled Python files should be ignored by Git. This ensures that these files do not get committed to the version control system, keeping the repository clean and reducing its size.
## Logic
### objectives
The objective of the `.gitignore` file is to specify intentionally untracked files that Git should ignore.

### logics and flow
The `.gitignore` file lists patterns for files and directories that Git should not track. Here's a breakdown of each entry:

1. **play.json**: This file likely contains configuration settings or data related to the MIDI player, so it is ignored to prevent sensitive information from being committed to the repository.
   
   ```plaintext
   play.json
   ```

2. **.venv/**: Virtual environments are used for managing project-specific dependencies. Ignoring this directory ensures that each developer has their own isolated environment without conflicts.

   ```plaintext
   .venv/
   ```

3. **__pycache__/**: Python caches bytecode files in the `__pycache__` directories to speed up execution. Ignoring these directories helps keep the repository clean and reduces the risk of committing unnecessary files.

   ```plaintext
   __pycache__/
   ```
# pic18-player/main.py
## relationship
### dependencies
- `queue`
- `threading`
- `win_precise_time as wdt`
- `json`
- `pathlib`
- `subprocess`
- `serial`
- `time`
- `glob`
- `PIL.Image, ImageEnhance`
- `LEDScreen.scripts.pic_extractor.extract`
- `MidiPlayer.scripts.convertor.convert`

### key elements
- `get_packed_pixels`: Function to generate packed pixel data for a specific PIC.
- `update_tmp_files`: Class method to update temporary files using FFmpeg and convert MIDI files.
- `SerialWorker`: Class for handling asynchronous sending of data over a serial port.

### summary
The file "pic18-player/main.py" is the main script for controlling an LED screen with MIDI playback. It uses various Python libraries such as `queue`, `threading`, and `serial` to handle tasks like packing pixel data, updating temporary files, and sending data over a serial connection. The script also depends on external modules `LEDScreen.scripts.pic_extractor.extract` and `MidiPlayer.scripts.convertor.convert` for specific functionalities related to LED screen display and MIDI file conversion.
## Logic
The code in `pic18-player/main.py` is designed to control an LED screen and play MIDI files simultaneously. It involves converting a video file into images, extracting MIDI data, and sending the data to an LED screen via serial communication.

### Objectives
- Convert a video file into individual frames (images).
- Extract MIDI data from a MIDI file.
- Send the extracted MIDI data and image frames to an LED screen for display and playback.
- Manage the timing and synchronization of the video and MIDI playback.

### Logics and Flow
1. **Configuration Setup**:
   - Define settings such as COM ports, baud rates, target FPS, video file path, MIDI file path, BPM, and contrast factor.

2. **Image Extraction**:
   - The `update_tmp_files` function uses FFmpeg to extract frames from the video file (`assets/bad apple.mp4`) into a temporary directory.
   - It generates image files named `%04d.jpg` with a frame rate of 24 FPS and a resolution of 64x64 pixels.

3. **MIDI Data Extraction**:
   - The `update_tmp_files` function also uses FFmpeg to extract MIDI data from the MIDI file (`assets/rolling girl.mid`) into a JSON file named `play.json`.

4. **Serial Communication Setup**:
   - A `SerialWorker` class is defined to handle serial communication with the LED screen.
   - It initializes a serial connection using the specified COM port and baud rate.
   - The `run` method of `SerialWorker` continuously checks a queue for data packets and sends them over the serial connection.

5. **Image Processing**:
   - The `get_packed_pixels` function processes images to extract pixel data in a specific format (Zig-Zag order, compressed).
   - It generates packets that include synchronization bytes and pixel data, which are then sent via the serial connection.

6. **Main Execution Flow**:
   - The script initializes the necessary components: image extraction, MIDI data extraction, and serial communication.
   - It creates a temporary directory to store intermediate files.
   - It starts the `SerialWorker` thread to handle serial communication in the background.
   - It iterates through the extracted images, processes them using `get_packed_pixels`, and sends the packets via the serial connection.

### Key Expressions
- **FFmpeg**: Used for video and MIDI file processing (`subprocess.run(["rm", "-rf", tmp_folder.as_posix()])`).
- **Zig-Zag Order**: Used in image processing to optimize data transmission (`if y % 2 == 0: tx = x else: tx = 15 - x`).
- **Serial Communication**: Managed using the `serial.Serial` class and a separate thread for asynchronous data sending.
# pic18-player/assets/Undertale - Battle Against a True Hero.mid
# pic18-player/doc/midi player.JPG
The image you provided contains two diagrams: one is a block diagram for a buzzer array control system, and the other is a schematic for a sound processor circuit.

### Buzzer Array Control Diagram (Top Diagram)
1. **Buzzer Array**:
   - The diagram shows a buzzer array with outputs labeled `Fin[5:0]`, indicating it has six control lines (Fin0 to Fin5) for controlling individual buzzers or channels.

### Sound Processor Circuit (Bottom Diagram)
1. **Components**:
   - **Crystal Oscillator**:
     - The circuit includes a crystal oscillator with a frequency of 10 MHz, connected to pins labeled `OSCI` and `OSCO`.
     - The crystal is connected to capacitors (C1) for stability.

   - **Microcontroller (MCU)**:
     - The block labeled `PIC18F` is a common designation for PIC microcontrollers, which are used for processing and control tasks.
     - The pins labeled `RA[5:0]` are likely data or control lines connected to the buzzer array.
     - `Vdd` and `Vss` are the power supply pins, with `Vdd` connected to 5V and `Vss` to ground.

   - **Buzzer Array Interface**:
     - The `Fin[5:0]` lines are connected to the microcontroller, indicating control signals for the buzzer array.

   - **Resistor and Capacitor Network**:
     - The circuit includes a resistor labeled `RDO` connected to the buzzer array, likely for current limiting or signal conditioning.
     - There is a capacitor labeled `C1` connected to the oscillator circuit, ensuring stable oscillation.

   - **Serial Communication**:
     - The diagram shows a serial port labeled `TX`, `RX`, `5V`, and `GND`, indicating a serial communication interface (likely UART) for programming or data transfer.

### Connections and Wiring:
- **Power Supply**:
  - The circuit is powered by a 5V supply, with `Vdd` connected to 5V and `Vss` to ground.

- **Grounding**:
  - The ground connections are labeled `GND` and are connected to the negative terminal of the power supply.

### General Functionality:
- **Sound Generation**:
  - The microcontroller (PIC18F) controls the buzzer array based on input signals or data processed internally.
  - The crystal oscillator provides a stable clock signal for the microcontroller.

- **Serial Communication**:
  - The serial port allows for communication with other devices, likely for programming or sending MIDI data to the microcontroller.

This schematic is typically used in projects involving MIDI-controlled sound generation, where the microcontroller processes MIDI data and controls the buzzer array to produce sounds.
The image you provided appears to be a block diagram for a MIDI player circuit, specifically using a PIC18 microcontroller. Here's a detailed explanation of the components and their roles:

### Components and Connections:

1. **Buzzer Array:**
   - The buzzer array is driven by the microcontroller to produce sound. Each buzzer corresponds to a specific frequency.

2. **Frequency Input (F = 10 MHz):**
   - This is the clock frequency for the microcontroller. The 10 MHz crystal oscillator is used to provide a stable clock signal.

3. **Crystal Oscillator (XTAL1 and XTAL2):**
   - These pins (XTAL1 and XTAL2) are connected to a 10 MHz crystal oscillator, which provides the clock signal for the microcontroller.

4. **Capacitors (C1):**
   - The capacitors connected to the crystal oscillator pins are used for stabilizing the oscillator circuit.

5. **Microcontroller (PIC18):**
   - The microcontroller is responsible for processing MIDI data and controlling the buzzer array to produce the desired sounds.

6. **RA Port (RA0 to RA5):**
   - These pins (RA0 to RA5) are likely used for output to the buzzer array or other peripheral devices.

7. **RB Port:**
   - The RB pins might be used for input/output functions, potentially for controlling additional components or receiving MIDI data.

8. **Serial Communication (TX and RX):**
   - The TX (Transmit) and RX (Receive) pins are used for serial communication, likely for MIDI data input/output.

9. **Power Supply:**
   - The circuit is powered by a 5V supply, which is necessary for the microcontroller and other components to operate.

### Circuit Functionality:

1. **Clock Signal:**
   - The 10 MHz crystal oscillator provides a stable clock signal to the PIC18 microcontroller, which is essential for its operation.

2. **MIDI Data Processing:**
   - The microcontroller receives MIDI data through the serial communication pins (RX) and processes it to generate appropriate control signals for the buzzer array.

3. **Sound Generation:**
   - The microcontroller sends signals to the buzzer array via the RA ports, controlling which buzzers are activated and for how long to produce the desired MIDI notes.

4. **Grounding:**
   - The ground connections ensure that all components have a common reference point for voltage levels.

### Additional Notes:

- **Buzzer Array Control:**
  - The buzzer array is likely driven by the microcontroller's digital output pins (RA0-RA5), which can be configured to switch buzzers on and off at precise intervals to create musical notes.

- **MIDI Protocol:**
  - MIDI data is received serially and decoded by the microcontroller to determine which notes should be played and for how long.

This setup is typical for a simple MIDI player that uses buzzers to generate sound based on MIDI input. The microcontroller's role is crucial in interpreting the MIDI data and controlling the buzzer array to produce the desired musical output.
# pic18-player/doc/20251230_062048/docs/README.md.md
## relationship
### dependencies
- None

### key elements
- README.md.md

### summary
The file `README.md.md` is a markdown document providing an overview or instructions for the project. It does not contain any code but serves as documentation.
## Logic
### objectives
The objective is to understand and document the project structure, specifically focusing on the README file for the "pic18-player" directory.

### logics and flow
To achieve this objective, we will follow these steps:
1. Identify the location of the README.md.md file within the specified path.
2. Extract the content of the README.md.md file.
3. Analyze the content to understand the project structure and its components.
4. Document the findings in a structured format.

## Content Analysis
The README.md.md file is located at:
```
pic18-player/doc/20251230_062048/docs/README.md.md
```

### Project Overview
The project appears to be related to multimedia playback, specifically for MIDI files, LED screen display, and video playback. It includes various components such as:
- MIDI player
- LED screen components
- Video playback

### Directory Structure
The project is organized into several directories:
- `pic18-player`: The root directory of the project.
  - `doc`: Contains documentation files.
    - `20251230_062048`: A subdirectory with a timestamp.
      - `docs`: Another subdirectory containing documents.
        - `README.md.md`: The file being analyzed.

### Key Components
- **MIDI Player**: Handles MIDI playback functionality.
- **LED Screen Components**: Manages the display of animations on LED screens.
- **Video Playback**: Supports video playback capabilities.

### Documentation
The README.md.md file likely contains detailed information about:
- Project setup and installation instructions.
- Configuration options for different components.
- Usage examples and tutorials.
- Troubleshooting tips.

## Summary
By analyzing the README.md.md file, we have gained insight into the project's structure and key components. This documentation serves as a valuable resource for developers working on or interacting with the "pic18-player" project.
# pic18-player/LICENSE
## relationship
### dependencies
- None

### key elements
- None

### summary
The file "pic18-player/LICENSE" contains the GNU General Public License version 3. It is a legal document that outlines the terms and conditions for distributing, copying, and modifying software covered by this license. The license ensures users' freedom to share and change software while protecting developers from patent infringement.
## Logic
### Objectives
The primary objective of this file is to provide the legal terms and conditions under which the software covered by the GNU General Public License version 3 can be used, modified, and distributed.

### Logics and Flow
1. **Definitions**: The file starts with defining key terms such as "License," "Copyright," "Program," "modify," "covered work," "propagate," and "convey." These definitions are crucial for understanding the subsequent rules.
   
2. **Preamble**: This section explains the purpose of the GNU General Public License, emphasizing its goal to ensure users' freedom to share and change software.

3. **Responsibilities**: It outlines the responsibilities developers have when distributing or modifying the software, including passing on the same freedoms to recipients and ensuring they receive source code.

4. **Terms and Conditions**:
   - **0. Definitions**: Reiterates the definitions established in the preamble.
   - **1. Source Code**: Defines what constitutes "source code" and "object code," and explains the concept of a "Standard Interface."
   - **2. Distribution**: Outlines conditions for distributing copies of the software, including the requirement to provide source code if requested.
   - **3. Propagation**: Defines what constitutes propagating a work, emphasizing that mere interaction through a network does not constitute propagation.
   - **4. Conveying**: Explains what constitutes conveying a work and how it affects users' rights.

5. **Final Notes**: The file concludes by addressing potential issues related to software patents and the protection of free software against patent restrictions.

This structure ensures that all parties using, modifying, or distributing the software are aware of their rights and responsibilities under the GNU General Public License version 3.
# pic18-player/assets/雨露霜雪.mid
# pic18-player/.gitattributes
## relationship
### dependencies
- Not important

### key elements
- `.gitattributes`

### summary
This file is a Git configuration file that automatically detects text files and normalizes line endings to LF (Unix-style). It does not have any direct dependencies or key elements relevant to the project's functionality.
## Logic
### objectives
The objective of the `.gitattributes` file is to configure Git's behavior regarding line endings for text files in the repository.

### logics and flow
The `.gitattributes` file specifies that all text files should have their line endings automatically detected and normalized to LF (Unix-style) format when checked into the repository. This ensures consistency across different operating systems, preventing issues related to inconsistent line endings.
# pic18-player/MidiPlayer/scripts/.python-version
## relationship
### dependencies
- Python 3.12

### key elements
- Not applicable (only contains Python version information)

### summary
The file specifies the required Python version for the project, which is Python 3.12. There are no key elements or dependencies related to functionality in this file.
## Logic
### objectives
The designer wants to specify the Python version that should be used for running scripts in the `MidiPlayer` directory.

### logics and flow
The file `.python-version` contains a single line specifying the Python version to be used, which is `3.12`. This ensures that any script executed within this directory will use Python 3.12, helping maintain consistency across development environments.
# pic18-player/assets/Undertale_-_Spear_Of_Justice.mid
# pic18-player/LEDScreen/scripts/test.py
## relationship
### dependencies
- `serial`: For serial communication with the PIC.
- `time`: For adding delays in the script.
- `os`: For interacting with the operating system, such as file paths and directory contents.
- `glob`: For finding all files matching a pathname pattern.
- `PIL.Image`: For image processing tasks.

### key elements
- `get_packed_pixels(img, global_pic_id)`: A function that processes an image to extract and compress pixels for sending over serial.
- `main()`: The main function that initializes the serial connection, loads images, and sends them to the PIC.

### summary
The script is designed to test and control an LED screen connected via a serial port. It reads images from a specified folder, processes each image to extract relevant pixel data, and sends this data over the serial connection to the PIC for display on the LED screen. The script includes error handling and allows for manual interruption with `KeyboardInterrupt`.
## Logic
### objectives
The designer wants to achieve the following objectives:
1. Connect to a PIC microcontroller via a serial port.
2. Read images from a specified folder and resize them to 64x64 pixels.
3. Extract specific regions (ID 3) from the resized images and compress the pixel data.
4. Send the compressed pixel data to the PIC microcontroller for display on an LED screen.

### logics and flow
The script follows these steps to achieve the objectives:

1. **Setup Configuration:**
   - Define constants such as the COM port, baud rate, image folder path, and target global ID (ID 3).

2. **Get Packed Pixels Function:**
   - This function takes an image and a global picture ID as input.
   - It calculates the position of the specified region within the image.
   - It extracts pixels from the specified region in a zig-zag pattern.
   - The extracted pixels are compressed by reducing their color depth (0-255 to 0-15).
   - The function then packs these compressed pixels into a bytearray for transmission.

3. **Main Function:**
   - Establishes a serial connection to the PIC microcontroller using the specified COM port and baud rate.
   - Lists all JPEG images in the specified folder and sorts them.
   - Enters an infinite loop where it iterates through each image:
     - Opens and resizes the image to 64x64 pixels.
     - Extracts the ID 3 region from the resized image using the `get_packed_pixels` function.
     - Sends the packed pixel data to the PIC microcontroller via the serial connection.
     - Pauses for one second between sending each image to allow time for observation in test mode.

4. **Exception Handling:**
   - Handles exceptions that may occur during the serial connection or image processing, such as keyboard interrupts and other errors.
   - Closes the serial connection if an exception occurs.

5. **Execution:**
   - The script runs the `main` function when executed directly.

This flow ensures that images are read, processed, and transmitted to the PIC microcontroller for display on an LED screen in a sequential manner.
# pic18-player/LEDScreen/scripts/images_original/hidden_img.png
Since the image provided (`hidden_img.png`) appears to be unrelated to the technical structure or modular relationships of the MIDI playback, LED screen display, or video playback system (it is purely aesthetic/artistic), **there are no meaningful technical relationships or modules to analyze from this image alone**.

---

## Relationship
### Key Elements
*(None relevant to the system's technical structure)*

### Summary
This image (`hidden_img.png`) is not important for analyzing the modular relationships of the MIDI player, LED screen, or video playback system. It is likely decorative or artistic and unrelated to the technical components of the project. For a proper analysis, focus on the directories/files related to `MIDIPlayer`, `LEDScreen`, and `video playback`.
## Logic
### objectives
**Not important.**
No discernible logic, state transitions, or data flow related to system objectives is present in this image. It is a static artistic design, likely for aesthetic or branding purposes.
# pic18-player/pyproject.toml
## relationship
### dependencies
- `mido`: Library for MIDI file parsing and generation.
- `pillow`: Python Imaging Library (PIL) fork, used for image processing.
- `pyserial`: Serial port communication library.
- `win-precise-time`: High-resolution timer library for Windows.

### key elements
- Not specified in the provided content.

### summary
The file "pic18-player/pyproject.toml" contains project metadata and dependencies required for the "pic18-player" project. It specifies Python version compatibility and lists libraries essential for MIDI playback, image processing, serial communication, and high-resolution timing on Windows.
## Logic
### objectives
The designer wants to create a Python project named "pic18-player" that is capable of handling MIDI playback, LED screen display, and video playback functionalities.

### logics and flow
The project's dependencies are defined in the `pyproject.toml` file. The following steps outline how these dependencies are utilized:

1. **Project Metadata**:
   - The project name is set to "pic18-player".
   - The version is initialized at 0.1.0.
   - A placeholder description is provided, which should be updated with a detailed description of the project.

2. **Readme File**:
   - The `readme` field points to a file named "README.md". This file likely contains more detailed information about the project and its features.

3. **Python Version Requirement**:
   - The project requires Python version 3.12 or higher, as specified by `requires-python = ">=3.12"`.

4. **Dependencies**:
   - Several external libraries are listed under `dependencies`:
     - `mido`: A library for working with MIDI files and messages.
     - `pillow`: A fork of the Python Imaging Library (PIL) that adds image processing capabilities.
     - `pyserial`: A library for serial port communication, which might be used for controlling hardware devices like LED screens.
     - `win-precise-time`: A library for precise timing on Windows systems.

These dependencies are essential for implementing the functionalities of MIDI playback, LED screen display, and video playback within the project.
# pic18-player/LEDScreen/scripts/conv.py
## relationship
### dependencies
- `PIL` (Python Imaging Library)
- `os`

### key elements
- `batch_resize`: A function to batch resize images in a source folder and save them to a target folder.

### summary
The file `conv.py` contains a script for resizing images. It uses the `PIL` library to open, process, and save images. The script defines a function `batch_resize` that takes a source folder and a target folder as arguments, resizes all supported image files in the source folder to 64x64 pixels, and saves them in the target folder.
## Logic
### objectives
The designer wants to achieve the ability to batch resize images in a specified source folder and save them in a target folder. The resizing should be done to a fixed size of 64x64 pixels, and transparency handling should be managed for PNG files.

### logics and flow
1. **Check if Target Folder Exists**: 
   - If the target folder does not exist, it is created using `os.makedirs(target_folder)`.

2. **Define Valid Image Extensions**:
   - A tuple of valid image extensions (`.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`) is defined to filter only relevant files.

3. **Initialize Count Variable**:
   - A counter variable `count` is initialized to keep track of the number of images processed.

4. **Iterate Over Files in Source Folder**:
   - The script iterates over each file in the source folder using `os.listdir(source_folder)`.

5. **Filter Valid Image Files**:
   - For each file, it checks if the filename ends with one of the valid extensions and is not already a resized version by comparing filenames.

6. **Open and Resize Images**:
   - If the file is a valid image, it opens the image using `Image.open(input_path)`.
   - If the image has a transparent background (PNG), it converts it to RGB mode.
   - The image is then resized to 64x64 pixels using `img.resize((64, 64), Image.Resampling.LANCZOS)`.

7. **Save Resized Images**:
   - The resized image is saved to the target folder with the same filename using `new_img.save(output_path)`.

8. **Handle Exceptions**:
   - If an exception occurs during the processing of any image, it prints an error message indicating which file caused the issue and continues with the next file.

9. **Completion Message**:
   - After all files are processed, a completion message is printed showing the total number of images processed.

10. **Example Usage**:
    - The script provides an example usage at the end, demonstrating how to call the `batch_resize` function by specifying the source and target folders.

This flow ensures that all valid images in the source folder are resized and saved correctly in the target folder, with proper handling of exceptions and transparency issues.
# pic18-player/assets/rolling girl.mid
# pic18-player/MidiPlayer/main.c
## relationship
### dependencies
- `xc.h`
- `main.h`

### key elements
- `UART_Initialize()`: Initializes UART communication.
- `Initialize()`: Sets up the system configuration and initializes peripherals.
- `tracks_note[]` and `tracks_timer[]`: Arrays to manage MIDI note tracking.
- `Hi_ISR()` and `Lo_ISR()`: Interrupt service routines for handling UART reception and Timer2 overflow.

### summary
The file "pic18-player/MidiPlayer/main.c" contains the main logic for a MIDI player. It initializes hardware peripherals, sets up interrupt handlers for UART communication and timer operations, and manages MIDI note tracking to control an LED display based on received MIDI data.
## Logic
### objectives
The primary objective of this code is to create a MIDI player that can receive MIDI data over UART and control an LED screen based on the received notes. The system also includes a timer-based mechanism to handle note timing.

### logics and flow
1. **Initialization**:
   - The `Initialize()` function sets up the microcontroller's oscillator, timers, UART communication, and GPIO pins.
     ```c
     OSCCONbits.IRCF = 0b111; // Set internal oscillator frequency to 8 MHz
     T2CON = 0x01; // Configure Timer2 for 1:1 prescaler
     PR2 = 49; // Set Timer2 period for a specific time interval
     UART_Initialize(); // Initialize UART communication
     IPR1bits.RCIP = 1; // Set high priority for UART receive interrupt
     IPR1bits.TMR2IP = 0; // Set low priority for Timer2 interrupt
     RCONbits.IPEN = 1; // Enable interrupt priority levels
     INTCONbits.PEIE = 1; // Enable peripheral interrupts
     INTCONbits.GIEH = 1; // Enable high-priority global interrupts
     INTCONbits.GIEL = 1; // Enable low-priority global interrupts
     PIR1bits.TMR2IF = 0; // Clear Timer2 interrupt flag
     PIE1bits.RCIE = 1; // Enable UART receive interrupt
     PIR1bits.TMR2IF = 0; // Clear Timer2 interrupt flag again
     T2CONbits.TMR2ON = 1; // Start Timer2
     PIE1bits.TMR2IE = 1; // Enable Timer2 interrupt
     TRISA = 0b11000000; // Set RA6 and RA7 as input for UART
     TRISD = 0; // Set all pins of PORTD as output
     LATA = 0;
     LATD = 0;
     ```

2. **UART Communication**:
   - The `UART_Initialize()` function configures the UART communication settings, including baud rate and enabling the UART module.
     ```c
     TRISCbits.TRISC6 = 0; // Set RC6 as TX pin
     TRISCbits.TRISC7 = 1; // Set RC7 as RX pin
     TXSTAbits.SYNC = 0; // Asynchronous mode
     BAUDCONbits.BRG16 = 1; // Use 16-bit baud rate generator
     TXSTAbits.BRGH = 1; // High-speed baud rate
     SPBRGH = ((int) (_XTAL_FREQ / BAUD / 4)) >> 8;
     SPBRG = (int) (_XTAL_FREQ / BAUD / 4);
     RCSTAbits.SPEN = 1; // Enable UART module
     TXSTAbits.TXEN = 1; // Enable transmitter
     RCSTAbits.CREN = 1; // Enable receiver
     RCSTAbits.RX9 = 0; // 8-bit reception
     ```

3. **Interrupt Handling**:
   - The `Hi_ISR()` function handles high-priority interrupts, specifically the UART receive interrupt.
     ```c
     void __interrupt(high_priority) Hi_ISR(void) {
         if (PIR1bits.RCIF) {
             if (RCSTAbits.OERR) {
                 CREN = 0;
                 Nop();
                 CREN = 1;
             }
             recv = RCREG;
             switch (recv_state) {
                 case 0:
                     midi_status = recv;
                     midi_ch = midi_status & 15;
                     recv_state++;
                     break;
                 default:
                     if (midi_ch == 15) {
                         LATDbits.LATD0 = ~LATDbits.LATD0;
                     } else if (midi_ch < 6) {
                         tracks_note[midi_ch] = recv;
                         if (midi_status<0x90) tracks_note[midi_ch] = 0;
                     }
                     recv_state = 0;
                     break;
             }
             LATDbits.LATD4 = ~LATDbits.LATD4;
         }
     }
     ```
   - The `Lo_ISR()` function handles low-priority interrupts, specifically the Timer2 interrupt.
     ```c
     void __interrupt(low_priority) Lo_ISR(void) {
         if (PIR1bits.TMR2IF) {
             PIR1bits.TMR2IF = 0; // Clear Timer2 interrupt flag
             n_lata = 0;
             check_note(0, 0x01);
             check_note(1, 0x02);
             check_note(2, 0x04);
             check_note(3, 0x08);
             check_note(4, 0x10);
             check_note(5, 0x20);
             LATA = n_lata;
         }
     }
     ```

4. **Note Timing Handling**:
   - The `check_note()` function checks the timing of notes and updates the LED screen accordingly.
     ```c
     void check_note(int track, unsigned char bit) {
         if (tracks_note[track] != 0) {
             n_lata |= bit;
         }
     }
     ```

This code effectively combines UART communication for MIDI data reception with a timer-based mechanism to control an LED screen based on the received notes.
# pic18-player/doc/20251230_062048/README.md
## relationship
### dependencies
- None

### key elements
- README.md
- Architecture Documentation.md

### summary
The file "pic18-player/doc/20251230_062048/README.md" is a documentation file generated by Docu-chan. It includes diagrams and links to other documentation files such as the main README and an architecture documentation.
## Logic
### objectives
The primary objective of this README file is to provide an overview and documentation for the project, including diagrams and links to detailed documents.

### logics and flow
1. **Introduction**: The README starts with a brief introduction generated by "Docu-chan" on 2025-12-30 06:24:42.
2. **Diagrams Section**:
   - It includes a reference to a project workflow diagram located at `charts/Project_Workflow.png`.
3. **Documentation Links**:
   - The README provides links to two detailed documentation files:
     - [README.md](docs/README.md.md)
     - [Architecture Documentation.md](docs/Architecture_Documentation.md.md)

This structure ensures that users can quickly access both high-level project information through the diagrams and more detailed technical specifications through the linked documents.
# pic18-player/LEDScreen/scripts/.gitignore
## relationship
### dependencies
- None

### key elements
- `.gitignore`

### summary
This file specifies directories to be ignored by Git, including the virtual environment and Python cache directories.
## Logic
### objectives
The `.gitignore` file is designed to specify intentionally untracked files that Git should ignore.

### logics and flow
The file contains patterns that match files and directories which Git should not track. It ensures that temporary files, virtual environments, and cached data are not included in the version control system.
- The line `.venv/` tells Git to ignore any directory named `.venv`, which is typically used for Python virtual environments.
- The line `__pycache__/` instructs Git to ignore directories named `__pycache__`, where Python stores bytecode files.
# pic18-player/assets/bad apple.mp4
# pic18-player/LEDScreen/scripts/images_original/bad_apple.png
Since the provided image (`bad_apple.png`) is unrelated to the system architecture, modules, or code structure you described (MIDI playback, LED screen display, video playback, and their associated scripts), I cannot analyze its relevance to the **system's module relationships**.

However, if this image were part of the **LED screen display module**, here’s how I would structure the analysis (for context):

---

## Relationship
### Key Elements
- **MIDI Player Module** (handles MIDI playback)
- **LED Screen Module** (handles LED animations/display, including images like `bad_apple.png`)
- **Video Playback Module** (handles video rendering)
- **Conversion Scripts** (for format/file conversions)
- **Control Scripts** (for playback synchronization)

### Summary
The **LED Screen Module** likely uses image assets (e.g., `bad_apple.png`) for visual output, possibly synchronized with MIDI or video playback. The relationship would be:
- **LED Screen Module** → Consumes image assets (e.g., `bad_apple.png`) for animations.
- **Control Scripts** → May manage timing/synchronization between MIDI/video and LED displays.
- **Conversion Scripts** → (Not directly related to this image but may process video/MIDI files for compatibility).

---
**Note:** Since the image itself is not code or a system diagram, it is **not important for analyzing module relationships**. Focus on analyzing the **directories/files** (e.g., `scripts/`, `MIDI_player/`, `LEDScreen/`) for actual dependencies.
## Logic
### objectives
Not important.

---
### logics and flow
Not applicable. This image (`bad_apple.png`) is a **static visual asset** (silhouette + text) with no discernible logic, data flow, or state transitions. It appears to be a **placeholder or decorative element** (e.g., for branding, humor, or thematic consistency) rather than a functional component. No transitions, scripts, or interactive logic are depicted.
# pic18-player/doc/20251230_062048/docs/Architecture_Documentation.md.md
## relationship
### dependencies
- None

### key elements
- Host PC control software (Python or C# UI)
- UART ports for communication
- Audio module with PIC18F4520 MCU and buzzer/speaker circuit
- LED display system with eight PIC18F4520 MCUs driving 16 WS2812 panels
- Shared oscillator for synchronized timing

### summary
The document describes the architecture of a hardware-centric system for driving a large LED screen using PIC18F4520 microcontrollers. It outlines the components, their interactions, and future improvements such as higher-speed interfaces, wireless control, and firmware updates. The system uses UART for communication between the host PC and the microcontroller subsystems, with each subsystem handling specific tasks like audio processing and LED display control.
## Logic
### objectives
The designer wants to achieve a hardware-centric system for driving a large LED screen using a fleet of PIC18F4520 microcontrollers, enabling both visual output on WS2812 LED matrices and audio feedback via a buzzer/speaker circuit.

### logics and flow
The system architecture is designed to handle communication between a host PC and multiple PIC18F4520 microcontrollers. The host PC runs control software that sends command frames over UART, which are then processed by the respective subsystems (audio module and LED display system). Each subsystem uses its own PIC18F4520 MCU to drive the corresponding components (buzzer/speaker for audio and WS2812 LED panels for visual output).

The communication between the host PC and the microcontrollers is facilitated through four UART ports, with each port managing a specific group of MCUs. The shared oscillator ensures synchronized timing for both UART communication and WS2812 signaling across all PICs.

Future improvements aim to enhance system performance by replacing UART with higher-speed interfaces, adding wireless control capabilities, implementing a scalable bus architecture, and integrating an RTOS for better task scheduling and concurrent processing.
# pic18-player/LEDScreen/scripts/images/frame1.jpg
Since the provided image (`frame1.jpg`) appears to be a simple static image (likely a frame for LED screen visualization) and does not explicitly show **system architecture, module relationships, or code**, I will analyze it in the context of **potential module relationships** in the broader project structure you described (MIDI playback, LED screen display, and video playback).

---

## **Relationship**
### **Key Elements**
1. **`LEDScreen`** – Likely responsible for rendering visuals (e.g., animations, MIDI-driven patterns) on LED screens.
2. **`scripts`** – Contains logic for processing/rendering frames (e.g., MIDI-to-visual conversion).
3. **`images/`** – Stores static/animated frames (e.g., `frame1.jpg`) used for LED screen output.
4. **`MIDIPlayer`** (implied) – Controls MIDI playback, which may influence LED visuals (e.g., syncing animations to beats).
5. **`VideoPlayer`** (implied) – May interact with LED screens if video frames are projected or mirrored.

### **Summary**
- **`frame1.jpg`** is likely a **static or dynamic frame** for LED screen rendering.
- **No direct module dependency** is visible in this single image, but it suggests:
  - The **`LEDScreen` module** uses **`scripts`** to generate/process frames (e.g., MIDI-triggered animations).
  - The **`images/` directory** stores assets (like `frame1.jpg`) that the `LEDScreen` module displays.
  - If MIDI is involved, the **`MIDIPlayer`** may feed timing/data to the `LEDScreen` for synchronized visuals.
  - **Not important**: No explicit connections to video playback or other modules are visible here.

---
**Note**: For a full system map, analyze:
- Scripts in `LEDScreen/scripts/` (e.g., how frames are generated).
- MIDI/Video player modules (e.g., if they share data with `LEDScreen`).
## Logic
### **Objectives**
- **Visual Representation**: Likely part of a **LED screen animation sequence** (e.g., for a MIDI-triggered display or synchronized video/LED show).
- **State Transition**: Frame in a **static or dynamic sequence** (e.g., part of a larger animation loop or transition effect).
- **Contextual Role**: May represent a **single frame** in a series used for:
  - A **static LED display** (e.g., logo, abstract art, or MIDI-reactive visuals).
  - A **transition effect** between other frames (e.g., fade, morph, or cutscene).
  - A **reference image** for LED mapping or video synchronization.

---

### **Logics and Flow**
1. **Static Frame Analysis**:
   - The image shows a **single static frame** (no visible motion blur or dynamic elements).
   - **Purpose**: Likely a **snapshot** in a sequence of frames (e.g., `frame1.jpg`, `frame2.jpg`, etc.) for:
     - **LED screen animation** (e.g., rendered as a grid of pixels for LED mapping).
     - **Video playback synchronization** (e.g., overlay or background for a MIDI video show).
     - **Pre-rendered visuals** for a MIDI-triggered display (e.g., reacting to tempo/notes).

2. **Potential State Transitions**:
   - **Not explicitly dynamic**: The image itself doesn’t show transitions (e.g., no arrows, motion lines, or sequential indicators).
   - **Implied transitions** (if part of a scripted sequence):
     - **Frame-by-frame animation**: Combined with other frames (e.g., via scripts like `animate_leds.py`) to create motion.
     - **Trigger-based changes**: MIDI data could alter this frame (e.g., brightness, color shifts, or LED patterns).
     - **Video overlay**: Used as a still image in a video timeline (e.g., for a countdown or static segment).

3. **Data Flow (Inferred)**:
   - **Input**: Likely generated by a script (e.g., `generate_frames.py`) or imported as a static asset.
   - **Processing**:
     - **LED Mapping**: Converted to LED grid commands (e.g., via `lib/led_utils.py`).
     - **Video Integration**: Embedded into a video file (e.g., via `ffmpeg` or `video_player.py`).
   - **Output**: Displayed on:
     - A **physical LED screen** (e.g., via `MIDIPlayer/led_driver.py`).
     - A **digital screen** (e.g., as part of a video playback loop).

4. **Not Important**:
   - No visible **data flow diagrams**, **state machines**, or **interactive elements** in the image itself.
   - No **code snippets** or **timeline markers** to analyze logic flow directly.

---
**Summary**: This is a **static frame** in a likely **LED/video animation sequence**, with transitions handled externally (e.g., by scripts or MIDI triggers). No explicit transitions are visible in the image alone.
# pic18-player/doc/20251230_062048/charts/Project_Workflow.mmd
## relationship
### dependencies
- None

### key elements
- `Project_Workflow.mmd`

### summary
The file `Project_Workflow.mmd` is a flowchart that outlines the workflow of a project, detailing the sequence of operations from power on to shutdown. It includes initialization steps for UART and LED, a main loop that handles UART reception, command validation, buffer updates, screen refreshes, and error handling.
## Logic
### objectives
The primary objective of this flowchart is to outline the sequence of operations and decision points for a system that involves UART communication, LED initialization, and screen refresh. The system aims to handle user commands through UART, validate these commands, update an internal buffer accordingly, and refresh the display based on the updated data.

### logics and flow
1. **Start**: The process begins with the start node.
2. **Power On**: The system powers on.
3. **UART Init**: UART communication is initialized to facilitate command reception.
4. **LED Init**: LED components are initialized for screen display.
5. **Main Loop**: The main loop continuously runs, waiting for user commands.
6. **UART Recv**: Commands are received via UART.
7. **Cmd Validate**: Received commands are validated.
   - If the command is valid (`"Valid"`), it proceeds to update the buffer.
   - If the command is invalid (`"Invalid"`), it handles the error.
8. **Update Buffer**: The internal buffer is updated based on the valid command.
9. **Refresh Screen**: The display screen is refreshed with the updated data.
10. **Error Handle**: Errors are handled and the system returns to the main loop.
11. **Shutdown**: If a shutdown condition is met, the process ends.

The flowchart ensures that the system can handle both valid and invalid commands, update its state accordingly, and maintain continuous operation until a shutdown condition is triggered.
# pic18-player/assets/Undertale_-_Megalovania.mid
# pic18-player/LEDScreen/scripts/README.md
## relationship
### dependencies
- Not applicable (Markdown file)

### key elements
- README.md

### summary
This is a Markdown file (`README.md`) located in the `pic18-player/LEDScreen/scripts` directory. It does not contain any code or executable content but provides documentation and instructions for the LED screen scripts.
## Logic
### objectives
The primary objective of the code in `pic18-player/LEDScreen/scripts/README.md` is to provide documentation and instructions for users on how to interact with and configure the LED screen component within the project.

### logics and flow
The README.md file serves as a guide, detailing various aspects such as installation, setup, usage, and troubleshooting. It outlines the steps required to properly set up and use the LED screen script in the `pic18-player` project. The content is structured to help users navigate through different functionalities and understand how to integrate the LED screen component effectively into their projects.

**Steps:**
1. **Overview**: Briefly introduces the purpose of the LED screen scripts.
2. **Installation**: Provides instructions on installing any necessary dependencies or libraries required for the script to function.
3. **Configuration**: Describes how to configure the LED screen settings, including resolution, brightness, and other parameters.
4. **Usage**: Explains how to run the script and control the LED screen, possibly through command-line arguments or a graphical interface.
5. **Troubleshooting**: Offers common issues and solutions related to using the LED screen scripts.

**Iconic Expression:**
"Readme is like the说明书 for your project, it tells others how to use it."
# pic18-player/.python-version
## relationship
### dependencies
- Python 3.12

### key elements
None

### summary
This file specifies the version of Python to be used for the project, which is Python 3.12.
## Logic
### objectives
Specify the Python version to be used for the project.

### logics and flow
The file `.python-version` specifies that Python version 3.12 should be used for this project. This ensures consistency across development environments, preventing compatibility issues due to differences in Python versions.
# pic18-player/doc/20251230_062048/charts/Project_Workflow.png
The flowchart in the image represents a workflow for a microcontroller-based project, likely involving communication via UART (Universal Asynchronous Receiver/Transmitter) and LED control. Here's a detailed breakdown of each step:

1. **Start**:
   - The process begins here.

2. **Power On**:
   - The system is powered on.

3. **UART Init**:
   - Initialize the UART communication module. This sets up the communication protocol and parameters for receiving and transmitting data.

4. **LED Init**:
   - Initialize the LED control module. This involves setting up the pins and registers necessary to control the LEDs.

5. **Main Loop (Main)**:
   - This is the primary loop where the system operates continuously until shutdown.

   Within the main loop, there are several subprocesses:
   - **UART Recv**:
     - Receive data via UART. This is a continuous process where the system waits for incoming data through the UART interface.
     - If valid data is received, it proceeds to **Cmd Validate**.
     - If invalid data is received, it proceeds to **Error Handle**.

   - **Cmd Validate**:
     - Validate the received command. This step checks if the command is valid and can be processed.

   - **Update Buffer**:
     - Update the buffer with the validated data. This might involve storing the data for further processing or display.

   - **Refresh Screen**:
     - Refresh or update the display based on the data in the buffer. This step likely involves updating the LED states or other visual outputs.

   - **Error Handle**:
     - Handle any errors encountered during data reception or command validation. This could involve logging errors, resetting the system, or taking other corrective actions.

6. **Shutdown**:
   - The system initiates the shutdown process. This could involve cleaning up resources, saving state, and turning off components.

7. **End**:
   - The process ends here.

In summary, this flowchart illustrates a typical embedded system workflow where UART communication is used to receive commands, validate them, update the system state, and control LEDs based on the received data. The system continuously runs in a loop until it is shut down.
The diagram you provided outlines a flowchart for a project workflow, specifically for a PIC18 microcontroller application. Here’s a detailed breakdown of each component and its role in the workflow:

1. **Start**: This is the entry point of the flowchart.

2. **Power On**: Upon powering on the system, the following steps are executed:
   - **UART Init**: Initializes the Universal Asynchronous Receiver/Transmitter (UART) communication interface, which is crucial for serial communication.

3. **Main Loop (Main)**: This is the primary loop of the program where the following actions occur:
   - **UART Recv**: Continuously checks for incoming data via UART.
   - **Cmd Validate**: Validates the received command to ensure it is correct and can be processed.
     - **Valid**: If the command is valid, it proceeds to process the command.
     - **Invalid**: If the command is invalid, it likely goes to an error handling process or returns to the UART Recv step to receive another command.

4. **Update Screen**: This step updates the display based on the validated command.

5. **Shutdown**: This is the exit point of the main loop, which might be triggered by a shutdown command or other conditions that require the system to stop.

### Detailed Workflow Explanation:

- **Initialization**:
  - The system starts and immediately initializes the UART interface to enable communication.

- **Continuous Operation**:
  - The main loop runs continuously, waiting for UART communication.
  - **UART Recv**: The system listens for incoming data through the UART interface.
  - **Cmd Validate**: The received data is validated to ensure it is a recognized command. If the command is invalid, it may be discarded or an error message may be sent back.

- **Processing Valid Commands**:
  - If the command is valid, the system processes it, which may include updating the screen or performing other actions.

- **End of Loop**:
  - The loop continues until a shutdown command or condition is met, which then leads to the shutdown process.

### Additional Notes:

- **Error Handling**: The diagram implies that there is an error handling mechanism for invalid commands, ensuring robustness in the system.

- **Feedback Loop**: The continuous nature of the main loop ensures that the system is always ready to receive new commands, providing a responsive user interface.

This workflow is typical for embedded systems where continuous monitoring and response to user input or external commands are essential. The UART interface is a common method for serial communication in microcontroller applications.
