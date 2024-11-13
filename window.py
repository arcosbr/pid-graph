# window.py

from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QSlider, QLabel,
    QHBoxLayout, QGridLayout, QFileDialog, QMessageBox, QPushButton, QComboBox
)
from PyQt6.QtCore import Qt, QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from pid_controller import PIDController
import json
import logging
from typing import List
import numpy as np  # Ensure numpy is imported for noise simulation


class DarkModeWindow(QMainWindow):
    """Main window class for displaying the PID response with a dark theme."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PID Controller Simulation")
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
            kp=1.0, ki=0.1, kd=0.05, setpoint=200.0,  # Updated default values
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

        # Create additional settings
        self.create_additional_settings(main_layout)

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

        # Data storage for real-time plotting
        self.time_data: List[float] = []
        self.output_data: List[float] = []

    def _configure_graph(self) -> None:
        """Visual configuration of the graph with a dark theme."""
        self.ax.clear()  # Clear the axes to prevent duplication
        self.ax.set_facecolor("#313335")
        self.ax.tick_params(axis='x', colors="#A9B7C6", direction='inout')
        self.ax.tick_params(axis='y', colors="#A9B7C6", direction='inout')
        self.ax.xaxis.label.set_color("#A9B7C6")
        self.ax.yaxis.label.set_color("#A9B7C6")
        self.ax.title.set_color("#A9B7C6")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Process Variable")
        self.ax.set_title("PID Controller Response")
        self.ax.set_ylim(50, 410)
        self.ax.grid(True, color="#505050", linestyle="--")

        # Initialize lines if they don't exist
        if not hasattr(self, 'line_output'):
            self.line_output, = self.ax.plot([], [], color="#CC7832", label='Process Variable')
            self.line_setpoint, = self.ax.plot([], [], color="#6A8759", linestyle='--', label='Setpoint')
        else:
            # Clear data from lines
            self.line_output.set_data([], [])
            self.line_setpoint.set_data([], [])

        self.ax.legend()

    def create_slider(
        self,
        layout: QGridLayout,
        label_text: str,
        slider_name: str,
        initial_value: float,
        scale: float,
        row: int,
        min_value: float,
        max_value: float
    ) -> None:
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

    def create_setpoint_slider(self, layout: QVBoxLayout) -> None:
        """Configure the slider for setpoint adjustment."""
        setpoint_layout = QHBoxLayout()

        label = QLabel("Setpoint:", self)
        label.setStyleSheet("color: #a9b7c6; font: 10pt;")
        setpoint_layout.addWidget(label)

        self.slider_setpoint = QSlider(Qt.Orientation.Horizontal, self)
        self.slider_setpoint.setRange(60, 400)
        self.slider_setpoint.setValue(int(self.pid_controller.setpoint))
        self.slider_setpoint.valueChanged.connect(self.update_graph)
        setpoint_layout.addWidget(self.slider_setpoint)

        self.slider_setpoint_label = QLabel(f"{self.pid_controller.setpoint:.0f}", self)
        self.slider_setpoint_label.setStyleSheet("color: #a9b7c6; font: 10pt;")
        setpoint_layout.addWidget(self.slider_setpoint_label)

        layout.addLayout(setpoint_layout)

    def create_additional_settings(self, layout: QVBoxLayout) -> None:
        """Create additional settings for simulation."""
        settings_layout = QHBoxLayout()

        # Model Type ComboBox
        model_label = QLabel("Process Model:", self)
        model_label.setStyleSheet("color: #a9b7c6; font: 10pt;")
        settings_layout.addWidget(model_label)

        self.model_combo = QComboBox(self)
        self.model_combo.addItems(["Second Order", "First Order"])
        self.model_combo.setStyleSheet("color: #a9b7c6; font: 10pt;")
        self.model_combo.currentIndexChanged.connect(self.update_graph)
        settings_layout.addWidget(self.model_combo)

        # Disturbance Slider
        self.create_slider_in_layout(
            settings_layout,
            label_text="Disturbance:",
            slider_name="slider_disturbance",
            initial_value=0.0,
            scale=100.0,
            precision=2,
            min_value=-50.0,
            max_value=50.0
        )

        # Noise Slider
        self.create_slider_in_layout(
            settings_layout,
            label_text="Noise Std Dev:",
            slider_name="slider_noise",
            initial_value=0.0,
            scale=1000.0,
            precision=2,
            min_value=0.0,
            max_value=10.0
        )

        layout.addLayout(settings_layout)

    def create_slider_in_layout(
        self,
        layout: QHBoxLayout,
        label_text: str,
        slider_name: str,
        initial_value: float,
        scale: float,
        precision: int,
        min_value: float,
        max_value: float
    ) -> None:
        """Helper function to create sliders in a given layout."""
        label = QLabel(label_text, self)
        label.setStyleSheet("color: #a9b7c6; font: 10pt;")
        layout.addWidget(label)

        slider = QSlider(Qt.Orientation.Horizontal, self)
        slider_min = int(min_value * scale)
        slider_max = int(max_value * scale)
        slider.setRange(slider_min, slider_max)
        slider.setValue(int(initial_value * scale))
        slider.valueChanged.connect(self.update_graph)
        layout.addWidget(slider)

        value_label = QLabel(f"{(slider.value() / scale):.{precision}f}", self)
        value_label.setStyleSheet("color: #a9b7c6; font: 10pt;")
        layout.addWidget(value_label)

        setattr(self, slider_name, slider)
        setattr(self, f"{slider_name}_label", value_label)

    def create_control_buttons(self, layout: QVBoxLayout) -> None:
        """Configure control buttons
           (Start, Pause, Reset, Save Config, Load Config)."""
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

        # Pause Button
        self.button_pause = QPushButton("Pause", self)
        self.button_pause.setStyleSheet("""
            QPushButton {
                background-color: #f0ad4e;
                color: white;
                padding: 5px 15px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ec971f;
            }
        """)
        self.button_pause.clicked.connect(self.pause_simulation)
        buttons_layout.addWidget(self.button_pause)

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

    def create_metrics_display(self, layout: QVBoxLayout) -> None:
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

    def start_simulation(self) -> None:
        """Start real-time simulation."""
        if not self.is_running:
            self.timer.start(int(self.pid_controller.sample_time * 1000))  # Convert to milliseconds
            self.is_running = True
            logging.info("Simulation started.")

    def pause_simulation(self) -> None:
        """Pause the simulation."""
        if self.is_running:
            self.timer.stop()
            self.is_running = False
            logging.info("Simulation paused.")

    def reset_simulation(self) -> None:
        """Reset the PID controller and clear the graph."""
        self.pid_controller.reset()
        self.time_data = []
        self.output_data = []
        self.is_running = False
        self.timer.stop()
        if hasattr(self, 'current_value'):
            del self.current_value
        if hasattr(self, 'velocity'):
            del self.velocity
        logging.info("Simulation reset.")

        # Clear the data from the lines
        self.line_output.set_data([], [])
        self.line_setpoint.set_data([], [])

        # Clear the axes without re-adding labels
        self.ax.relim()
        self.ax.autoscale_view()

        # Update sliders to default positions
        self.slider_kp.setValue(int(self.pid_controller.kp * self.kp_scale))
        self.slider_ki.setValue(int(self.pid_controller.ki * self.ki_scale))
        self.slider_kd.setValue(int(self.pid_controller.kd * self.kd_scale))
        self.slider_setpoint.setValue(int(self.pid_controller.setpoint))
        self.slider_omega_n.setValue(int(self.pid_controller.omega_n * self.omega_n_scale))
        self.slider_damping_ratio.setValue(int(self.pid_controller.damping_ratio * self.damping_ratio_scale))
        self.slider_disturbance.setValue(0)
        self.slider_noise.setValue(0)

        # Update labels to reflect reset values
        self.update_graph()

        # Redraw the canvas
        self.canvas.draw()

    def update_real_time(self) -> None:
        """Update the graph in real-time during the simulation."""
        if not hasattr(self, 'current_value'):
            self.current_value = 60.0  # Starting from 60
        if not hasattr(self, 'velocity'):
            self.velocity = 0.0

        # Read disturbance and noise values
        disturbance = self.slider_disturbance.value() / 100.0
        noise_std = self.slider_noise.value() / 1000.0

        # Model type
        model_type = "second_order" if self.model_combo.currentText() == "Second Order" else "first_order"

        # Measurement noise
        measurement = self.current_value + np.random.normal(0, noise_std)

        output = self.pid_controller.update(measurement)

        # Apply disturbance at half simulation time
        if len(self.time_data) * self.pid_controller.sample_time >= 5.0:
            disturbance_value = disturbance
        else:
            disturbance_value = 0.0

        # Process model
        if model_type == "second_order":
            # Second-order process model
            omega_n = self.pid_controller.omega_n
            damping_ratio = self.pid_controller.damping_ratio
            acceleration = (omega_n ** 2) * (output - self.current_value) - 2 * damping_ratio * omega_n * self.velocity
            self.velocity += acceleration * self.pid_controller.sample_time
            self.current_value += self.velocity * self.pid_controller.sample_time
        else:
            # First-order process model
            tau = 1 / self.pid_controller.omega_n  # Time constant
            self.current_value += (output - self.current_value) / tau * self.pid_controller.sample_time

        # Add disturbance
        self.current_value += disturbance_value * self.pid_controller.sample_time

        # Clamp current_value to physical limits
        self.current_value = max(0, min(self.current_value, 400))

        # Update data lists
        current_time = len(self.time_data) * self.pid_controller.sample_time
        self.time_data.append(current_time)
        self.output_data.append(self.current_value)

        # Update lines
        self.line_output.set_xdata(self.time_data)
        self.line_output.set_ydata(self.output_data)

        # Update setpoint line
        self.line_setpoint.set_xdata(self.time_data)
        self.line_setpoint.set_ydata([self.pid_controller.setpoint] * len(self.time_data))

        # Adjust axes
        self.ax.set_xlim(0, max(self.time_data) + 1)
        self.ax.set_ylim(50, 410)

        # Redraw canvas
        self.canvas.draw()

    def update_graph(self) -> None:
        """Update the graph based on the current slider values for Kp, Ki, Kd, and setpoint."""
        # Retrieve and scale the slider values
        kp = self.slider_kp.value() / self.kp_scale
        ki = self.slider_ki.value() / self.ki_scale
        kd = self.slider_kd.value() / self.kd_scale
        omega_n = self.slider_omega_n.value() / self.omega_n_scale
        damping_ratio = self.slider_damping_ratio.value() / self.damping_ratio_scale
        setpoint = self.slider_setpoint.value()

        disturbance = self.slider_disturbance.value() / 100.0
        noise_std = self.slider_noise.value() / 1000.0
        model_type = "second_order" if self.model_combo.currentText() == "Second Order" else "first_order"

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

        self.slider_disturbance_label.setText(f"{disturbance:.2f}")
        self.slider_noise_label.setText(f"{noise_std:.2f}")

        # Reset the PID controller for a fresh start
        self.pid_controller.reset()

        # Simulate the PID response
        simulation_time = 10.0  # Total simulation time in seconds
        time, output = self.pid_controller.simulate(
            simulation_time,
            initial_value=60.0,
            disturbance=disturbance,
            noise_std=noise_std,
            model_type=model_type
        )

        # Clamp output to physical limits
        output = [max(0, min(val, 400)) for val in output]

        # Update performance metrics based on simulation
        self.update_metrics(time, output)

        # Update the graph data
        self.line_output.set_xdata(time)
        self.line_output.set_ydata(output)

        # Update setpoint line
        self.line_setpoint.set_xdata(time)
        self.line_setpoint.set_ydata([setpoint] * len(time))

        self.ax.set_xlim(0, max(time))
        self.ax.set_ylim(50, 410)
        self.canvas.draw()

    def save_config(self) -> None:
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
                'damping_ratio': self.pid_controller.damping_ratio,
                'disturbance': self.slider_disturbance.value() / 100.0,
                'noise_std': self.slider_noise.value() / 1000.0,
                'model_type': self.model_combo.currentText()
            }
            try:
                with open(file_path, 'w') as f:
                    json.dump(config, f, indent=4)
                QMessageBox.information(self, "Success", "Configuration saved successfully.")
                logging.info(f"Configuration saved to {file_path}.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save configuration:\n{e}")
                logging.error(f"Failed to save configuration: {e}")

    def load_config(self) -> None:
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
                disturbance = config.get('disturbance', 0.0)
                noise_std = config.get('noise_std', 0.0)
                model_type = config.get('model_type', 'Second Order')

                # Update sliders to reflect loaded configuration
                self.slider_kp.setValue(int(self.pid_controller.kp * self.kp_scale))
                self.slider_ki.setValue(int(self.pid_controller.ki * self.ki_scale))
                self.slider_kd.setValue(int(self.pid_controller.kd * self.kd_scale))
                self.slider_setpoint.setValue(int(self.pid_controller.setpoint))
                self.slider_omega_n.setValue(int(self.pid_controller.omega_n * self.omega_n_scale))
                self.slider_damping_ratio.setValue(int(self.pid_controller.damping_ratio * self.damping_ratio_scale))
                self.slider_disturbance.setValue(int(disturbance * 100.0))
                self.slider_noise.setValue(int(noise_std * 1000.0))

                index = self.model_combo.findText(model_type)
                if index != -1:
                    self.model_combo.setCurrentIndex(index)

                # Update the graph with new configuration
                self.update_graph()

                QMessageBox.information(self, "Success", "Configuration loaded successfully.")
                logging.info(f"Configuration loaded from {file_path}.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load configuration:\n{e}")
                logging.error(f"Failed to load configuration: {e}")

    def update_metrics(self, time: List[float], output: List[float]) -> None:
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

        setpoint = self.pid_controller.setpoint
        final_value = output[-1]

        # Calculate Rise Time (time to reach 90% of setpoint)
        try:
            rise_time_index = next(i for i, val in enumerate(output) if val >= 0.9 * setpoint)
            rise_time = time[rise_time_index]
        except StopIteration:
            rise_time = None

        # Calculate Settling Time (time to stay within 2% of setpoint)
        try:
            settling_time_index = next(
                i for i in range(len(output))
                if all(abs(val - setpoint) <= 0.02 * setpoint for val in output[i:])
            )
            settling_time = time[settling_time_index]
        except StopIteration:
            settling_time = None

        # Calculate Overshoot
        overshoot = max(output) - setpoint

        # Calculate Steady-State Error
        steady_state_error = abs(setpoint - final_value)

        # Update labels
        self.label_rise_time.setText(f"Rise Time: {rise_time:.2f}s" if rise_time is not None else "Rise Time: N/A")
        self.label_settling_time.setText(f"Settling Time: {settling_time:.2f}s" if settling_time is not None else "Settling Time: N/A")
        self.label_overshoot.setText(f"Overshoot: {overshoot:.2f}")
        self.label_steady_state_error.setText(f"Steady-State Error: {steady_state_error:.2f}")
