# window.py

from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QSlider, QLabel,
    QHBoxLayout, QGridLayout, QFileDialog, QMessageBox, QPushButton
)
from PyQt6.QtCore import Qt, QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from pid_controller import PIDController
import json
import logging

# Configure logging for debugging purposes
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class DarkModeWindow(QMainWindow):
    """Main window class for displaying the PID response with a dark theme."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PID Response")
        self.setStyleSheet("background-color: #2b2b2b; color: #a9b7c6;")
        self.setGeometry(100, 100, 1000, 700)

        # Define scaling factors for each PID parameter
        self.kp_scale = 100.0    # Kp ranges from 0.00 to 10.00 with two decimal places
        self.ki_scale = 1000.0   # Ki ranges from 0.000 to 10.000 with three decimal places
        self.kd_scale = 100.0    # Kd ranges from 0.00 to 10.00 with two decimal places

        # Scales for omega_n and damping_ratio
        self.omega_n_scale = 100.0    # ωn ranges from 0.10 to 10.00
        self.damping_ratio_scale = 1000.0  # ζ ranges from 0.000 to 2.000

        # Set up the central widget and layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Configure the graph
        self.canvas = FigureCanvas(Figure(figsize=(10, 6), facecolor="#313335"))
        main_layout.addWidget(self.canvas)

        # Initialize PID controller with default values
        self.pid_controller = PIDController(
            kp=0.1, ki=0.005, kd=0.02, setpoint=200.0,
            output_limits=(0, 400), sample_time=0.01, omega_n=1.0, damping_ratio=0.7
        )

        # Initial configuration of the graph
        self.ax = self.canvas.figure.add_subplot(111)
        self._configure_graph()

        # Create sliders for PID parameters
        sliders_layout = QGridLayout()
        self.create_slider(sliders_layout, "Kp:", "slider_kp", self.pid_controller.kp, self.kp_scale, 0, min_value=0.0, max_value=10.0)
        self.create_slider(sliders_layout, "Ki:", "slider_ki", self.pid_controller.ki, self.ki_scale, 1, min_value=0.0, max_value=10.0)
        self.create_slider(sliders_layout, "Kd:", "slider_kd", self.pid_controller.kd, self.kd_scale, 2, min_value=0.0, max_value=10.0)

        # Create sliders for process parameters
        self.create_slider(sliders_layout, "ωn (Natural Freq.):", "slider_omega_n",
                           self.pid_controller.omega_n, self.omega_n_scale, 3, min_value=0.1, max_value=10.0)
        self.create_slider(sliders_layout, "ζ (Damping Rate):", "slider_damping_ratio",
                           self.pid_controller.damping_ratio, self.damping_ratio_scale, 4, min_value=0.0, max_value=2.0)

        main_layout.addLayout(sliders_layout)

        # Create setpoint slider
        self.create_setpoint_slider(main_layout)

        # Create control buttons
        self.create_control_buttons(main_layout)

        # Create performance metrics display
        self.create_metrics_display(main_layout)

        # Initialize the graph with the PID controller's response
        self.update_graph()

        # Timer for real-time simulation
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_real_time)
        self.is_running = False

    def _configure_graph(self):
        """Visual configuration of the graph with a dark theme."""
        self.ax.set_facecolor("#313335")
        self.ax.tick_params(axis='x', colors="#A9B7C6", direction='inout')
        self.ax.tick_params(axis='y', colors="#A9B7C6", direction='inout')
        self.ax.xaxis.label.set_color("#A9B7C6")
        self.ax.yaxis.label.set_color("#A9B7C6")
        self.ax.title.set_color("#A9B7C6")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Pressure (Bar)")
        self.ax.set_title("PID Step Response")
        self.ax.set_ylim(50, 410)  # Adjusted to include values from 60 to 400 bar
        self.ax.grid(True, color="#505050", linestyle="--")
        self.line, = self.ax.plot([], [], color="#CC7832", label='Output')
        self.ax.legend()

    def create_slider(self, layout, label_text, slider_name, initial_value,
                      scale, row, min_value, max_value):
        """Create sliders for parameters with correct initial settings."""
        label = QLabel(label_text, self)
        label.setStyleSheet("color: #a9b7c6; font: 10pt;")
        layout.addWidget(label, row, 0)

        slider = QSlider(Qt.Orientation.Horizontal, self)
        slider_min = int(min_value * scale)
        slider_max = int(max_value * scale)
        slider.setRange(slider_min, slider_max)
        slider.setValue(int(initial_value * scale))
        slider.valueChanged.connect(self.update_graph)
        layout.addWidget(slider, row, 1)

        # Set precision based on scale
        if scale == self.ki_scale or scale == self.damping_ratio_scale:
            precision = 3
        else:
            precision = 2
        value_label = QLabel(f"{(slider.value() / scale):.{precision}f}", self)
        value_label.setStyleSheet("color: #a9b7c6; font: 10pt;")
        layout.addWidget(value_label, row, 2)

        # Save sliders and labels as class attributes
        setattr(self, slider_name, slider)
        setattr(self, f"{slider_name}_label", value_label)

    def create_setpoint_slider(self, layout):
        """Configure the slider for setpoint adjustment."""
        setpoint_layout = QHBoxLayout()

        label = QLabel("Setpoint (Bar):", self)
        label.setStyleSheet("color: #a9b7c6; font: 10pt;")
        setpoint_layout.addWidget(label)

        self.slider_setpoint = QSlider(Qt.Orientation.Horizontal, self)
        self.slider_setpoint.setRange(60, 400)  # Updated to start from 60 bar
        self.slider_setpoint.setValue(int(self.pid_controller.setpoint))
        self.slider_setpoint.valueChanged.connect(self.update_graph)
        setpoint_layout.addWidget(self.slider_setpoint)

        self.slider_setpoint_label = QLabel(f"{self.pid_controller.setpoint:.0f}", self)
        self.slider_setpoint_label.setStyleSheet("color: #a9b7c6; font: 10pt;")
        setpoint_layout.addWidget(self.slider_setpoint_label)

        layout.addLayout(setpoint_layout)

    def create_control_buttons(self, layout):
        """Configure control buttons (Start, Stop, Reset, Save Config, Load Config)."""
        buttons_layout = QHBoxLayout()

        # Start Button
        self.button_start = QPushButton("Start", self)
        self.button_start.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 5px 15px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.button_start.clicked.connect(self.start_simulation)
        buttons_layout.addWidget(self.button_start)

        # Stop Button
        self.button_stop = QPushButton("Stop", self)
        self.button_stop.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 5px 15px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.button_stop.clicked.connect(self.stop_simulation)
        buttons_layout.addWidget(self.button_stop)

        # Reset Button
        self.button_reset = QPushButton("Reset", self)
        self.button_reset.setStyleSheet("""
            QPushButton {
                background-color: #008CBA;
                color: white;
                padding: 5px 15px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #007bb5;
            }
        """)
        self.button_reset.clicked.connect(self.reset_simulation)
        buttons_layout.addWidget(self.button_reset)

        # Save Configuration Button
        self.button_save = QPushButton("Save Config", self)
        self.button_save.setStyleSheet("""
            QPushButton {
                background-color: #e7e7e7;
                color: black;
                padding: 5px 15px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d6d6d6;
            }
        """)
        self.button_save.clicked.connect(self.save_config)
        buttons_layout.addWidget(self.button_save)

        # Load Configuration Button
        self.button_load = QPushButton("Load Config", self)
        self.button_load.setStyleSheet("""
            QPushButton {
                background-color: #e7e7e7;
                color: black;
                padding: 5px 15px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d6d6d6;
            }
        """)
        self.button_load.clicked.connect(self.load_config)
        buttons_layout.addWidget(self.button_load)

        layout.addLayout(buttons_layout)

    def create_metrics_display(self, layout):
        """Create labels to display performance metrics."""
        metrics_layout = QHBoxLayout()

        # Rise Time Label
        self.label_rise_time = QLabel("Rise Time: N/A", self)
        self.label_rise_time.setStyleSheet("color: #a9b7c6; font: 10pt;")
        metrics_layout.addWidget(self.label_rise_time)

        # Settling Time Label
        self.label_settling_time = QLabel("Settling Time: N/A", self)
        self.label_settling_time.setStyleSheet("color: #a9b7c6; font: 10pt;")
        metrics_layout.addWidget(self.label_settling_time)

        # Overshoot Label
        self.label_overshoot = QLabel("Overshoot: N/A", self)
        self.label_overshoot.setStyleSheet("color: #a9b7c6; font: 10pt;")
        metrics_layout.addWidget(self.label_overshoot)

        # Steady-State Error Label
        self.label_steady_state_error = QLabel("Steady-State Error: N/A", self)
        self.label_steady_state_error.setStyleSheet("color: #a9b7c6; font: 10pt;")
        metrics_layout.addWidget(self.label_steady_state_error)

        layout.addLayout(metrics_layout)

    def start_simulation(self):
        """Start real-time simulation."""
        if not self.is_running:
            self.timer.start(int(self.pid_controller.sample_time * 1000))  # Convert to milliseconds
            self.is_running = True
            logging.info("Simulation started.")

    def stop_simulation(self):
        """Stop real-time simulation."""
        if self.is_running:
            self.timer.stop()
            self.is_running = False
            logging.info("Simulation stopped.")

    def reset_simulation(self):
        """Reset the PID controller and clear the graph."""
        self.pid_controller.reset()
        self.ax.cla()
        self._configure_graph()
        self.update_graph()
        self.is_running = False
        self.timer.stop()
        if hasattr(self, 'current_value'):
            del self.current_value
        if hasattr(self, 'velocity'):
            del self.velocity
        logging.info("Simulation reset.")

    def update_real_time(self):
        """Update the graph in real-time during the simulation."""
        if not hasattr(self, 'current_value'):
            self.current_value = 60.0  # Starting from offset 60 bar
        if not hasattr(self, 'velocity'):
            self.velocity = 0.0

        output = self.pid_controller.update(self.current_value)

        # Second-order process model
        omega_n = self.pid_controller.omega_n
        damping_ratio = self.pid_controller.damping_ratio
        acceleration = (omega_n ** 2) * (output - self.current_value) - 2 * damping_ratio * omega_n * self.velocity
        self.velocity += acceleration * self.pid_controller.sample_time
        self.current_value += self.velocity * self.pid_controller.sample_time

        # Clamp current_value to physical limits
        self.current_value = max(0, min(self.current_value, 400))

        # Update graph data
        current_time = len(self.line.get_xdata()) * self.pid_controller.sample_time
        self.line.set_xdata(list(self.line.get_xdata()) + [current_time])
        self.line.set_ydata(list(self.line.get_ydata()) + [self.current_value])

        # Set fixed limits to prevent graph distortion
        self.ax.set_xlim(0, current_time + 1)
        self.ax.set_ylim(0, 400)
        self.canvas.draw()

    def update_graph(self):
        """Update the graph based on the current slider values for Kp, Ki, Kd,
           and setpoint."""
        # Retrieve and scale the slider values
        kp = self.slider_kp.value() / self.kp_scale
        ki = self.slider_ki.value() / self.ki_scale
        kd = self.slider_kd.value() / self.kd_scale
        omega_n = self.slider_omega_n.value() / self.omega_n_scale
        damping_ratio = self.slider_damping_ratio.value() / self.damping_ratio_scale
        setpoint = self.slider_setpoint.value()  # Already in 60 to 400

        # Update PID controller parameters
        self.pid_controller.kp = kp
        self.pid_controller.ki = ki
        self.pid_controller.kd = kd
        self.pid_controller.setpoint = setpoint
        self.pid_controller.omega_n = omega_n
        self.pid_controller.damping_ratio = damping_ratio

        # Update slider labels to reflect current values
        self.slider_kp_label.setText(f"{kp:.2f}")
        self.slider_ki_label.setText(f"{ki:.3f}")
        self.slider_kd_label.setText(f"{kd:.2f}")
        self.slider_omega_n_label.setText(f"{omega_n:.2f}")
        self.slider_damping_ratio_label.setText(f"{damping_ratio:.3f}")
        self.slider_setpoint_label.setText(f"{setpoint:.0f}")

        # Reset the PID controller for a fresh start
        self.pid_controller.reset()

        # Simulate the PID response
        simulation_time = 10.0  # Total simulation time in seconds
        time, output = self.pid_controller.simulate(simulation_time, initial_value=60.0)

        # Clamp output to physical limits
        output = [max(0, min(val, 400)) for val in output]

        # Update performance metrics based on simulation
        self.update_metrics(time, output)

        # Update the graph data
        self.line.set_xdata(time)
        self.line.set_ydata(output)
        self.ax.set_xlim(0, max(time))
        self.ax.set_ylim(50, 410)
        self.canvas.draw()

    def save_config(self):
        """Save the current PID configuration to a JSON file."""
        options = QFileDialog.Option.DontUseNativeDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save PID Configuration",
            "",
            "JSON Files (*.json)",
            options=options
        )
        if file_path:
            config = {
                'kp': self.pid_controller.kp,
                'ki': self.pid_controller.ki,
                'kd': self.pid_controller.kd,
                'setpoint': self.pid_controller.setpoint,
                'omega_n': self.pid_controller.omega_n,
                'damping_ratio': self.pid_controller.damping_ratio
            }
            try:
                with open(file_path, 'w') as f:
                    json.dump(config, f, indent=4)
                QMessageBox.information(self, "Success", "Configuration saved successfully.")
                logging.info(f"Configuration saved to {file_path}.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save configuration:\n{e}")
                logging.error(f"Failed to save configuration: {e}")

    def load_config(self):
        """Load PID configuration from a JSON file."""
        options = QFileDialog.Option.DontUseNativeDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load PID Configuration",
            "",
            "JSON Files (*.json)",
            options=options
        )
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    config = json.load(f)
                self.pid_controller.kp = config.get('kp', self.pid_controller.kp)
                self.pid_controller.ki = config.get('ki', self.pid_controller.ki)
                self.pid_controller.kd = config.get('kd', self.pid_controller.kd)
                self.pid_controller.setpoint = config.get('setpoint', self.pid_controller.setpoint)
                self.pid_controller.omega_n = config.get('omega_n', self.pid_controller.omega_n)
                self.pid_controller.damping_ratio = config.get('damping_ratio', self.pid_controller.damping_ratio)

                # Update sliders to reflect loaded configuration
                self.slider_kp.setValue(int(self.pid_controller.kp * self.kp_scale))
                self.slider_ki.setValue(int(self.pid_controller.ki * self.ki_scale))
                self.slider_kd.setValue(int(self.pid_controller.kd * self.kd_scale))
                self.slider_setpoint.setValue(int(self.pid_controller.setpoint))
                self.slider_omega_n.setValue(int(self.pid_controller.omega_n * self.omega_n_scale))
                self.slider_damping_ratio.setValue(int(self.pid_controller.damping_ratio * self.damping_ratio_scale))

                # Update the graph with new configuration
                self.update_graph()

                QMessageBox.information(self, "Success", "Configuration loaded successfully.")
                logging.info(f"Configuration loaded from {file_path}.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load configuration:\n{e}")
                logging.error(f"Failed to load configuration: {e}")

    def update_metrics(self, time, output):
        """
        Update performance metrics based on the simulation output.

        Parameters:
            time (list): Time steps of the simulation.
            output (list): Output values from the simulation.
        """
        if not output:
            self.label_rise_time.setText("Rise Time: N/A")
            self.label_settling_time.setText("Settling Time: N/A")
            self.label_overshoot.setText("Overshoot: N/A")
            self.label_steady_state_error.setText("Steady-State Error: N/A")
            return

        final_value = output[-1]

        # Calculate Rise Time (time to reach 90% of setpoint)
        try:
            rise_time_index = next(i for i, val in enumerate(output) if val >= 0.9 * self.pid_controller.setpoint)
            rise_time = time[rise_time_index]
        except StopIteration:
            rise_time = None

        # Calculate Settling Time (time to stay within 2% of setpoint)
        try:
            settling_time_index = next(
                i for i in range(len(output))
                if all(abs(val - self.pid_controller.setpoint) <= 0.02 * self.pid_controller.setpoint for val in output[i:])
            )
            settling_time = time[settling_time_index]
        except StopIteration:
            settling_time = None

        # Calculate Overshoot
        overshoot = max(output) - self.pid_controller.setpoint

        # Calculate Steady-State Error
        steady_state_error = abs(self.pid_controller.setpoint - final_value)

        # Update labels
        self.label_rise_time.setText(f"Rise Time: {rise_time:.2f}s" if rise_time is not None else "Rise Time: N/A")
        self.label_settling_time.setText(f"Settling Time: {settling_time:.2f}s" if settling_time is not None else "Settling Time: N/A")
        self.label_overshoot.setText(f"Overshoot: {overshoot:.2f}")
        self.label_steady_state_error.setText(f"Steady-State Error: {steady_state_error:.2f}")
