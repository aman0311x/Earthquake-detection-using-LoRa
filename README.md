# 🌍 AI-Powered LoRa P2P Earthquake Monitoring System

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![C++](https://img.shields.io/badge/C%2B%2B-Arduino-00979D)
![TensorFlow Lite](https://img.shields.io/badge/TensorFlow_Lite-Micro-FF6F00)
![LoRa](https://img.shields.io/badge/Communication-LoRa_433MHz-orange)
![License](https://img.shields.io/badge/License-MIT-green)

A decentralized, edge-AI integrated IoT system designed to detect seismic activities in real-time. This project utilizes ESP32 microcontrollers, MPU6050 accelerometers, and SX1278 LoRa modules to establish a Peer-to-Peer (P2P) early warning network. A custom PyQt5-based desktop dashboard provides real-time visualization of vibration data and remote alerts.

---

## 📌 Table of Contents
- [Introduction](#-introduction)
- [Key Features](#-key-features)
- [Equipments & Hardware](#-equipments--hardware)
- [System Architecture (How it Works)](#-how-it-works)
- [Circuit & Wiring](#-circuit--wiring)
- [Installation & Setup](#-installation--setup)
- [Demo & Links](https://www.youtube.com/shorts/u_B2SPIGAwg)
- [Contributors](#-contributors)

---

## 📖 Introduction
Traditional earthquake monitoring systems rely on centralized servers, which can fail during severe natural disasters due to internet or power outages. This project introduces a **decentralized (P2P)** approach. By running a **TensorFlow Lite (Micro)** machine learning model directly on the Edge (ESP32), the system can intelligently distinguish between normal background noise and actual seismic tremors. If an earthquake is detected, the node instantly triggers a local alarm and broadcasts an alert via a Long-Range (LoRa) radio network to warn surrounding nodes.

---

## ✨ Key Features
* **Edge AI Detection:** Uses a custom trained INT8 quantized Neural Network (TFLite) to analyze 3-axis accelerometer data in real-time, preventing false alarms.
* **Peer-to-Peer LoRa Network:** Operates completely offline without the need for Wi-Fi or cellular networks using 433MHz SX1278 transceivers.
* **Non-Blocking Architecture:** Hardware timer (`millis()`) based multitasking ensures the system never misses an incoming LoRa packet while processing sensor data or sounding the alarm.
* **Smart Alerting:** Implements a 4-second cooldown mechanism and 1-second auto-timeout buzzer to prevent network congestion and hardware degradation.
* **Professional Desktop Dashboard:** A custom-built Python GUI (PyQt5 + PyQtGraph) for real-time serial data visualization, system logging, and alert tracking.

---

## 🛠 Equipments & Hardware
To build a complete two-way communicating system, you will need **two sets** of the following components:

| Component | Description | Quantity (per node) |
| :--- | :--- | :--- |
| **ESP32** | Main Microcontroller (NodeMCU/DevKit V1) | 1 |
| **SX1278** | LoRa Transceiver Module (433 MHz) | 1 |
| **MPU6050** | 3-Axis Accelerometer & Gyroscope | 1 |
| **Buzzer** | 5V Active/Passive Buzzer for Audio Alert | 1 |
| **Antenna** | 433MHz Spring/Copper Antenna | 1 |
| **Jumper Wires** | For connecting components | As needed |

---

## ⚙️ How It Works

1. **Data Acquisition:** The MPU6050 sensor continuously samples X, Y, and Z-axis acceleration data at a high frequency.
2. **Edge AI Inference / Thresholding:** The raw data is passed into the ESP32's memory. The embedded TFLite model evaluates the windowed data (or calculates the magnitude: `√(Ax² + Ay² + Az²)`). 
3. **Local Actuation:** If the AI confidence score exceeds the predefined threshold (e.g., > 0.5 or Magnitude > 25000), the ESP32 immediately triggers the local buzzer using PWM signals.
4. **LoRa Transmission:** Simultaneously, the ESP32 sends an `"ALERT"` string via the SPI bus to the SX1278 LoRa module, which broadcasts the signal over the 433MHz frequency.
5. **Remote Reception:** The secondary node(s), constantly listening in `LoRa.receive()` mode, intercepts the `"ALERT"`. It bypasses its local sensor logic and instantly sounds its own buzzer, providing an early warning.
6. **Data Visualization:** The master node connected to the PC sends real-time string data via USB Serial. The Python Desktop App parses this data (handling DTR/RTS properly to prevent auto-reset) and plots it live on the dashboard.

---

## 🔌 Circuit & Wiring

### ESP32 to MPU6050 (I2C)
* **VCC** ➔ 3.3V
* **GND** ➔ GND
* **SDA** ➔ GPIO 21
* **SCL** ➔ GPIO 22

### ESP32 to SX1278 LoRa (SPI)
* **VCC** ➔ 3.3V *(Strictly 3.3V!)*
* **GND** ➔ GND
* **SCK** ➔ GPIO 18
* **MISO** ➔ GPIO 19
* **MOSI** ➔ GPIO 23
* **NSS (CS)** ➔ GPIO 5
* **RST** ➔ GPIO 14
* **DIO0** ➔ GPIO 2

### ESP32 to Buzzer
* **VCC** ➔ VIN / 5V
* **GND** ➔ GND
* **Signal** ➔ GPIO 26 *(Moved from 19 to avoid SPI conflict)*

---

## 💻 Installation & Setup

### 1. Arduino IDE Setup (Microcontroller)
1. Install the [ESP32 Board Package](https://github.com/espressif/arduino-esp32) in Arduino IDE.
2. Install the following libraries from the Library Manager:
   * `LoRa` by Sandeep Mistry
   * `TensorFlowLite_ESP32` (if using the AI model integration)
3. Connect your ESP32, select the correct COM port, and upload `sketch_feb21a.ino`.

### 2. Python Dashboard Setup (PC)
1. Ensure Python 3.8+ is installed.
2. Open terminal/command prompt and install the required dependencies:
   ```bash
   pip install pyserial PyQt5 pyqtgraph
