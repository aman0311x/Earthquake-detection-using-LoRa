

import sys
import serial
import serial.tools.list_ports
from datetime import datetime
from collections import deque
import re

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QComboBox, 
                             QTextEdit, QGroupBox, QGridLayout, QFrame)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QPalette, QColor

import pyqtgraph as pg
from pyqtgraph import PlotWidget


class SerialThread(QThread):
    """Background thread for reading serial data"""
    data_received = pyqtSignal(str)
    
    def __init__(self, port, baudrate=115200):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.running = False
        self.serial_conn = None
    
    def run(self):
        try:
            
            self.serial_conn = serial.Serial()
            self.serial_conn.port = self.port
            self.serial_conn.baudrate = self.baudrate
            self.serial_conn.timeout = 1
            
            
            self.serial_conn.dtr = False
            self.serial_conn.rts = False
            
            
            self.serial_conn.open()
            self.running = True
            
            while self.running:
                if self.serial_conn.in_waiting:
                    try:
                        line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                        if line:
                            self.data_received.emit(line)
                    except Exception as e:
                        print(f"Read error: {e}")
        except Exception as e:
            print(f"Serial connection error: {e}")
    
    def stop(self):
        self.running = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()

class EarthquakeMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LoRa Earthquake Monitoring System")
        self.setGeometry(100, 100, 1400, 900)
        
        
        self.max_points = 500
        self.time_data = deque(maxlen=self.max_points)
        self.vibration_data = deque(maxlen=self.max_points)
        self.start_time = datetime.now()
        
        
        self.local_alerts = 0
        self.remote_alerts = 0
        self.current_vibration = 0
        self.max_vibration = 0
        
        
        self.serial_thread = None
        
        
        self.init_ui()
        
        
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self.update_ui)
        self.ui_timer.start(100)  
    
    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Set dark theme
        self.set_dark_theme()
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Connection controls
        connection_group = self.create_connection_controls()
        main_layout.addWidget(connection_group)
        
        # Statistics panels
        stats_layout = QHBoxLayout()
        stats_layout.addWidget(self.create_stats_panel())
        stats_layout.addWidget(self.create_alert_panel())
        main_layout.addLayout(stats_layout)
        
        # Graph
        graph_group = self.create_graph()
        main_layout.addWidget(graph_group)
        
        # Log console
        log_group = self.create_log_console()
        main_layout.addWidget(log_group)
    
    def set_dark_theme(self):
        """Apply dark theme to the application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QGroupBox {
                border: 2px solid #3d3d3d;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 15px;
                font-weight: bold;
                background-color: #2a2a2a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #4CAF50;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
            QComboBox {
                background-color: #3d3d3d;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 8px;
                color: #e0e0e0;
            }
            QComboBox:hover {
                border: 1px solid #4CAF50;
            }
            QComboBox::drop-down {
                border: none;
            }
            QTextEdit {
                background-color: #252525;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                color: #e0e0e0;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
            }
            QLabel {
                color: #e0e0e0;
            }
        """)
    
    def create_header(self):
        """Create header section"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2E7D32, stop:1 #4CAF50);
                border-radius: 10px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(header_frame)
        
        title = QLabel("🌍 LoRa Earthquake Monitoring System")
        title.setFont(QFont('Segoe UI', 24, QFont.Bold))
        title.setStyleSheet("color: white;")
        
        subtitle = QLabel("Real-time Seismic Activity Monitoring & Alert Network")
        subtitle.setFont(QFont('Segoe UI', 12))
        subtitle.setStyleSheet("color: #e8f5e9;")
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        return header_frame
    
    def create_connection_controls(self):
        """Create connection control panel"""
        group = QGroupBox("🔌 Serial Connection")
        layout = QHBoxLayout()
        
        # Port selection
        port_label = QLabel("Port:")
        port_label.setStyleSheet("font-weight: bold;")
        self.port_combo = QComboBox()
        self.refresh_ports()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_ports)
        refresh_btn.setStyleSheet("background-color: #2196F3;")
        
        # Connect button
        self.connect_btn = QPushButton("▶️ Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        
        # Status label
        self.status_label = QLabel("● Disconnected")
        self.status_label.setStyleSheet("color: #f44336; font-weight: bold; font-size: 13px;")
        
        layout.addWidget(port_label)
        layout.addWidget(self.port_combo)
        layout.addWidget(refresh_btn)
        layout.addWidget(self.connect_btn)
        layout.addWidget(self.status_label)
        layout.addStretch()
        
        group.setLayout(layout)
        return group
    
    def create_stats_panel(self):
        """Create statistics panel"""
        group = QGroupBox("📊 Live Statistics")
        layout = QGridLayout()
        
        # Current vibration
        self.vibration_label = QLabel("0")
        self.vibration_label.setFont(QFont('Segoe UI', 28, QFont.Bold))
        self.vibration_label.setStyleSheet("color: #4CAF50;")
        
        vibration_title = QLabel("Current Vibration Level")
        vibration_title.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        
        # Max vibration
        self.max_vibration_label = QLabel("Max: 0")
        self.max_vibration_label.setFont(QFont('Segoe UI', 14))
        self.max_vibration_label.setStyleSheet("color: #FFC107;")
        
        # Uptime
        self.uptime_label = QLabel("Uptime: 00:00:00")
        self.uptime_label.setFont(QFont('Segoe UI', 12))
        self.uptime_label.setStyleSheet("color: #2196F3;")
        
        layout.addWidget(vibration_title, 0, 0, 1, 2)
        layout.addWidget(self.vibration_label, 1, 0, 1, 2)
        layout.addWidget(self.max_vibration_label, 2, 0)
        layout.addWidget(self.uptime_label, 2, 1)
        
        group.setLayout(layout)
        return group
    
    def create_alert_panel(self):
        """Create alert statistics panel"""
        group = QGroupBox("🚨 Alert Summary")
        layout = QGridLayout()
        
        # Local alerts
        local_title = QLabel("Local Detections")
        local_title.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        self.local_alert_label = QLabel("0")
        self.local_alert_label.setFont(QFont('Segoe UI', 28, QFont.Bold))
        self.local_alert_label.setStyleSheet("color: #FF5722;")
        
        # Remote alerts
        remote_title = QLabel("Remote Alerts Received")
        remote_title.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        self.remote_alert_label = QLabel("0")
        self.remote_alert_label.setFont(QFont('Segoe UI', 28, QFont.Bold))
        self.remote_alert_label.setStyleSheet("color: #FF9800;")
        
        layout.addWidget(local_title, 0, 0)
        layout.addWidget(self.local_alert_label, 1, 0)
        layout.addWidget(remote_title, 0, 1)
        layout.addWidget(self.remote_alert_label, 1, 1)
        
        group.setLayout(layout)
        return group
    
    def create_graph(self):
        """Create vibration graph"""
        group = QGroupBox("📈 Real-time Vibration Graph")
        layout = QVBoxLayout()
        
        # Create plot widget
        self.plot_widget = PlotWidget()
        self.plot_widget.setBackground('#1e1e1e')
        self.plot_widget.setTitle("Vibration Magnitude Over Time", 
                                  color='#4CAF50', size='14pt')
        
        # Configure axes
        self.plot_widget.setLabel('left', 'Vibration Level', color='#e0e0e0')
        self.plot_widget.setLabel('bottom', 'Time (seconds)', color='#e0e0e0')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # Add threshold line
        self.threshold_line = pg.InfiniteLine(
            pos=25000, 
            angle=0, 
            pen=pg.mkPen(color='r', width=2, style=Qt.DashLine),
            label='Alert Threshold'
        )
        self.plot_widget.addItem(self.threshold_line)
        
        # Create plot curve
        self.curve = self.plot_widget.plot(
            pen=pg.mkPen(color='#4CAF50', width=2),
            symbol='o',
            symbolSize=4,
            symbolBrush='#4CAF50'
        )
        
        layout.addWidget(self.plot_widget)
        group.setLayout(layout)
        return group
    
    def create_log_console(self):
        """Create log console"""
        group = QGroupBox("📝 System Log")
        layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        
        # Clear button
        clear_btn = QPushButton("🗑️ Clear Log")
        clear_btn.clicked.connect(self.log_text.clear)
        clear_btn.setStyleSheet("background-color: #757575;")
        
        layout.addWidget(self.log_text)
        layout.addWidget(clear_btn)
        
        group.setLayout(layout)
        return group
    
    def refresh_ports(self):
        """Refresh available serial ports"""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(f"{port.device} - {port.description}")
    
    def toggle_connection(self):
        """Toggle serial connection"""
        if self.serial_thread and self.serial_thread.running:
            # Disconnect
            self.serial_thread.stop()
            self.serial_thread.wait()
            self.serial_thread = None
            
            self.connect_btn.setText("▶️ Connect")
            self.status_label.setText("● Disconnected")
            self.status_label.setStyleSheet("color: #f44336; font-weight: bold; font-size: 13px;")
            self.log_message("Disconnected from serial port", "warning")
        else:
            # Connect
            port_text = self.port_combo.currentText()
            if not port_text:
                self.log_message("No port selected!", "error")
                return
            
            port = port_text.split(' - ')[0]
            
            self.serial_thread = SerialThread(port)
            self.serial_thread.data_received.connect(self.process_serial_data)
            self.serial_thread.start()
            
            self.connect_btn.setText("⏹️ Disconnect")
            self.status_label.setText("● Connected")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 13px;")
            self.log_message(f"Connected to {port}", "success")
    
    def process_serial_data(self, line):
        """Process incoming serial data"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Parse vibration level
        vibration_match = re.search(r'Vibration Level:\s*([\d.]+)', line)
        if vibration_match:
            try:
                vibration = float(vibration_match.group(1))
                elapsed = (datetime.now() - self.start_time).total_seconds()
                
                self.time_data.append(elapsed)
                self.vibration_data.append(vibration)
                self.current_vibration = vibration
                
                if vibration > self.max_vibration:
                    self.max_vibration = vibration
            except ValueError:
                pass
        
        # Detect local earthquake
        if "LOCAL EARTHQUAKE DETECTED" in line:
            self.local_alerts += 1
            self.log_message("🚨 LOCAL EARTHQUAKE DETECTED!", "alert")
        
        # Detect remote alert
        if "RECEIVED ALERT FROM REMOTE NODE" in line:
            self.remote_alerts += 1
            self.log_message("⚠️ REMOTE NODE ALERT RECEIVED!", "alert")
        
        # Log all important messages
        if any(keyword in line for keyword in ["ALERT", "EARTHQUAKE", "Started", "Ready", "Alarm"]):
            self.log_message(line, "info")
    
    def log_message(self, message, msg_type="info"):
        """Add message to log console with color coding"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        colors = {
            "info": "#2196F3",
            "success": "#4CAF50",
            "warning": "#FFC107",
            "error": "#f44336",
            "alert": "#FF5722"
        }
        
        color = colors.get(msg_type, "#e0e0e0")
        
        html = f'<span style="color: #888888;">[{timestamp}]</span> ' \
               f'<span style="color: {color};">{message}</span>'
        
        self.log_text.append(html)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def update_ui(self):
        """Update UI elements"""
        # Update vibration display
        self.vibration_label.setText(f"{int(self.current_vibration):,}")
        self.max_vibration_label.setText(f"Max: {int(self.max_vibration):,}")
        
        # Update alert counts
        self.local_alert_label.setText(str(self.local_alerts))
        self.remote_alert_label.setText(str(self.remote_alerts))
        
        # Update uptime
        uptime = datetime.now() - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        self.uptime_label.setText(f"Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}")
        
        # Update graph
        if len(self.time_data) > 0:
            self.curve.setData(list(self.time_data), list(self.vibration_data))
        
        # Change vibration color based on level
        if self.current_vibration > 25000:
            self.vibration_label.setStyleSheet("color: #f44336;")  # Red
        elif self.current_vibration > 15000:
            self.vibration_label.setStyleSheet("color: #FFC107;")  # Yellow
        else:
            self.vibration_label.setStyleSheet("color: #4CAF50;")  # Green
    
    def closeEvent(self, event):
        """Clean up on application close"""
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread.wait()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    
    window = EarthquakeMonitor()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
