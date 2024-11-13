# PID Graph Controller

A graphical application for simulating and visualizing the behavior of a PID (Proportional-Integral-Derivative) controller. This tool allows users to adjust PID parameters in real-time and observe the effects on the system's response through interactive graphs.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Performance Metrics](#performance-metrics)
- [Dependencies](#dependencies)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Features

- **Interactive Sliders:** Adjust `Kp`, `Ki`, `Kd`, setpoint values, **natural frequency (ωn)**, and **damping ratio (ζ)** with precision.
- **Real-Time Simulation:** Start, stop, and reset the PID simulation to observe immediate effects.
- **Performance Metrics:** View key metrics such as Rise Time, Settling Time, Overshoot, and Steady-State Error.
- **Save & Load Configurations:** Persist and retrieve PID settings using JSON files.
- **Dynamic Graphing:** Visualize the PID controller's response with a real-time updating graph.
- **Dark Theme:** User-friendly dark mode interface for reduced eye strain and enhanced visual appeal.

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/arcosbr/pid-graph.git
   cd pid-grap
   ```

2. **Create and Activate a Virtual Environment (Recommended):**

   ```bash
   # Create a virtual environment named 'venv'
   python -m venv venv

   # Activate the virtual environment
   # On Windows:
   venv\Scripts\activate

   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies:**

   Ensure you have Python 3.7 or higher installed. Then install required packages using `pip`:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application by executing `main.py`:

```bash
python main.py
```

Upon launching, you'll see the PID Controller Simulator window with the following components:

- **Sliders:** Adjust `Kp`, `Ki`, `Kd`, and setpoint values.
- **Graph:** Visual representation of the PID response.
- **Performance Metrics:** Displays Rise Time, Settling Time, Overshoot, and Steady-State Error.
- **Control Buttons:**
  - **Start:** Begin the real-time simulation.
  - **Stop:** Pause the simulation.
  - **Reset:** Reset the simulation and clear the graph.
  - **Save Config:** Save current PID settings to a JSON file.
  - **Load Config:** Load PID settings from a JSON file.

## Configuration

### Saving Configuration

1. Adjust the `Kp`, `Ki`, `Kd`, and setpoint sliders to your desired values.
2. Click the **"Save Config"** button.
3. In the file dialog, choose a location and filename (e.g., `config1.json`) and save.

### Loading Configuration

1. Click the **"Load Config"** button.
2. In the file dialog, navigate to and select a previously saved JSON configuration file.
3. The sliders and graph will update to reflect the loaded PID parameters.

## Performance Metrics

The application calculates and displays the following metrics based on the simulation:

- **Rise Time:** Time taken for the process variable to reach 90% of the setpoint.
- **Settling Time:** Time taken for the process variable to remain within 2% of the setpoint.
- **Overshoot:** The amount by which the process variable exceeds the setpoint.
- **Steady-State Error:** The absolute difference between the setpoint and the final value of the process variable.

These metrics provide insights into the performance and stability of the PID controller.

## Dependencies

The project relies on the following Python packages:

- [PyQt6](https://pypi.org/project/PyQt6/) >= 6.0.0
- [matplotlib](https://pypi.org/project/matplotlib/) >= 3.0.0

Ensure that these dependencies are installed via the provided `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Contributing

Contributions are welcome! If you'd like to contribute to this project, please follow these steps:

1. **Fork the Repository:**

   Click the **Fork** button at the top right of the repository page.

2. **Create a Feature Branch:**

   ```bash
   git checkout -b feature/YourFeatureName
   ```

3. **Commit Your Changes:**

   ```bash
   git commit -m "Add your detailed description of the changes"
   ```

4. **Push to the Branch:**

   ```bash
   git push origin feature/YourFeatureName
   ```

5. **Open a Pull Request:**

   Navigate to the original repository and click on **Compare & pull request**.

## License

This project is licensed under the [MIT License](LICENSE).
