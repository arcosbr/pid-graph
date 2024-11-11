# pid_controller.py

class PIDController:
    def __init__(self, kp=0.2, ki=0.01, kd=0.05, setpoint=200.0,
                 output_limits=(0, 400), sample_time=0.01):
        """
        Initialize the PID controller with configurable parameters.

        Parameters:
            kp (float): Proportional gain.
            ki (float): Integral gain.
            kd (float): Derivative gain.
            setpoint (float): Desired target value.
            output_limits (tuple): Lower and upper limits for the output.
            sample_time (float): Time interval between control updates in secs.
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.output_limits = output_limits
        self.sample_time = sample_time

        self._integral = 0.0
        self._last_error = 0.0
        self._last_output = 0.0

    def reset(self):
        """
        Reset the PID controller's integral and derivative terms.
        """
        self._integral = 0.0
        self._last_error = 0.0
        self._last_output = 0.0

    def update(self, current_value):
        """
        Calculate the PID controller output based on the current value.

        Parameters:
            current_value (float): The current measurement of the process
                                   variable.

        Returns:
            float: The controller output.
        """
        error = self.setpoint - current_value
        proportional = self.kp * error
        self._integral += self.ki * error * self.sample_time

        # Anti-windup: Clamp the integral term
        lower_limit, upper_limit = self.output_limits
        self._integral = max(lower_limit, min(self._integral, upper_limit))

        derivative = self.kd * (error - self._last_error) / self.sample_time
        output = proportional + self._integral + derivative

        # Clamp output to limits
        output = max(lower_limit, min(output, upper_limit))

        self._last_error = error
        self._last_output = output

        return output

    def simulate(self, simulation_time, initial_value=0.0, tau=1.0):
        """
        Simulate the PID controller response over a specified time using a
        first-order process model.

        Parameters:
            simulation_time (float): Total simulation time in seconds.
            initial_value (float): Initial value of the process variable.
            tau (float): Time constant of the process (in seconds).

        Returns:
            tuple: (time_steps, output_values) representing the PID response
                                               over time.
        """
        num_steps = int(simulation_time / self.sample_time)
        current_value = initial_value
        time_steps = []
        output_values = []

        for step in range(num_steps):
            current_time = step * self.sample_time
            output = self.update(current_value)
            # First-order process model: dPV/dt = (Output - PV) / tau
            current_value += (output - current_value) * (self.sample_time / tau)
            time_steps.append(current_time)
            output_values.append(current_value)

        return time_steps, output_values
