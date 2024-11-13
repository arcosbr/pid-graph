# pid_controller.py

from typing import Tuple, List
import numpy as np


class PIDController:
    """
    PID Controller class with anti-windup and derivative kick prevention.
    """

    def __init__(
        self,
        kp: float = 0.2,
        ki: float = 0.01,
        kd: float = 0.05,
        setpoint: float = 200.0,
        output_limits: Tuple[float, float] = (0, 400),
        sample_time: float = 0.01,
        omega_n: float = 1.0,
        damping_ratio: float = 0.7,
        derivative_filter: float = 0.0,
    ):
        """
        Initialize the PID controller with configurable parameters.

        Parameters:
            kp (float): Proportional gain.
            ki (float): Integral gain.
            kd (float): Derivative gain.
            setpoint (float): Desired target value.
            output_limits (tuple): Lower and upper limits for the output.
            sample_time (float): Time interval between control updates in seconds.
            omega_n (float): Natural frequency of the process.
            damping_ratio (float): Damping ratio of the process.
            derivative_filter (float): Derivative filter coefficient (0 to 1), 0 means no filtering.
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.output_limits = output_limits
        self.sample_time = sample_time

        self.omega_n = omega_n
        self.damping_ratio = damping_ratio
        self.derivative_filter = derivative_filter

        self._integral = 0.0
        self._last_output = 0.0
        self._last_input = None  # For derivative calculation

    def reset(self) -> None:
        """
        Reset the PID controller's integral term and last input.
        """
        self._integral = 0.0
        self._last_output = 0.0
        self._last_input = None

    def update(self, current_value: float) -> float:
        """
        Calculate the PID controller output based on the current value.

        Parameters:
            current_value (float): The current measurement of the process variable.

        Returns:
            float: The controller output.
        """
        error = self.setpoint - current_value
        proportional = self.kp * error

        self._integral += self.ki * error * self.sample_time

        # Anti-windup via integrator clamping
        min_output, max_output = self.output_limits
        if self._integral > max_output:
            self._integral = max_output
        elif self._integral < min_output:
            self._integral = min_output

        # Derivative term (using measurement derivative to prevent derivative kick)
        if self._last_input is None:
            derivative = 0.0
        else:
            derivative = -(current_value - self._last_input) / self.sample_time

            # Apply derivative filter if specified
            if self.derivative_filter > 0.0:
                derivative = self.derivative_filter * derivative + (1 - self.derivative_filter) * self._last_derivative

        derivative_term = self.kd * derivative
        self._last_derivative = derivative
        self._last_input = current_value

        # Compute total output
        output = proportional + self._integral + derivative_term

        # Clamp output to limits
        if output > max_output:
            output = max_output
        elif output < min_output:
            output = min_output

        self._last_output = output
        return output

    def simulate(
        self,
        simulation_time: float,
        initial_value: float = 60.0,
        initial_velocity: float = 0.0,
        disturbance: float = 0.0,
        noise_std: float = 0.0,
        model_type: str = "second_order",
    ) -> Tuple[List[float], List[float]]:
        """
        Simulate the PID controller response over a specified time using a process model.

        Parameters:
            simulation_time (float): Total simulation time in seconds.
            initial_value (float): Initial value of the process variable.
            initial_velocity (float): Initial rate of change of the process variable.
            disturbance (float): External disturbance to the process variable.
            noise_std (float): Standard deviation of measurement noise.
            model_type (str): Type of process model ('first_order' or 'second_order').

        Returns:
            tuple: (time_steps, output_values) representing the PID response over time.
        """
        num_steps = int(simulation_time / self.sample_time)
        current_value = initial_value
        velocity = initial_velocity
        time_steps = []
        output_values = []

        for step in range(num_steps):
            current_time = step * self.sample_time

            # Measurement noise
            measurement = current_value + np.random.normal(0, noise_std)

            output = self.update(measurement)

            # Apply disturbance at half simulation time
            if current_time >= simulation_time / 2:
                disturbance_value = disturbance
            else:
                disturbance_value = 0.0

            # Process model
            if model_type == "second_order":
                # Second-order process model
                omega_n = self.omega_n
                damping_ratio = self.damping_ratio
                acceleration = (omega_n ** 2) * (output - current_value) - 2 * damping_ratio * omega_n * velocity
                velocity += acceleration * self.sample_time
                current_value += velocity * self.sample_time
            elif model_type == "first_order":
                # First-order process model
                tau = 1 / self.omega_n  # Time constant
                current_value += (output - current_value) / tau * self.sample_time
            else:
                raise ValueError("Invalid model_type. Choose 'first_order' or 'second_order'.")

            # Add disturbance
            current_value += disturbance_value * self.sample_time

            # Clamp current_value to physical limits
            current_value = max(0, min(current_value, max(self.output_limits)))

            time_steps.append(current_time)
            output_values.append(current_value)

        return time_steps, output_values
