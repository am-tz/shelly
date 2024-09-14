from importlib.util import find_spec
if find_spec("RPi"):
    print("Setting GPIO Pins (for real)")
    import RPi.GPIO as GPIO
    MOCKUP: bool = False
else:
    # Workaround to make the app run on Windows
    print("Using fake GPIO setup")
    from infra.log.loggable import Loggable
    from typing import List, Any

    MOCKUP: bool = True

    class GPIO:
        LOW: str = "LOW"
        HIGH: str = "HIGH"

        IN: str = "IN"
        OUT: str = "OUT"

        BOARD: str = "BOARD"

        class GPIOMockup(Loggable):

            def __init__(self):
                super().__init__()

            def log(self, message: str):
                self._logger.debug(message)

        @staticmethod
        def setmode(mode: Any) -> None:
            GPIO.GPIOMockup().log(f"Set mode to {mode}")

        @staticmethod
        def setup(pins: List[int], mode_in_out: Any, initial: Any) -> None:
            pin_names: List[str] = [str(pin) for pin in pins]
            GPIO.GPIOMockup().log(f"Set pins {', '.join(pin_names)} to '{mode_in_out}', with initial value '{initial}'")

        @staticmethod
        def cleanup() -> None:
            GPIO.GPIOMockup().log("Cleaning up")

        @staticmethod
        def output(pin: int, value: Any) -> None:
            GPIO.GPIOMockup().log(f"Set pin {pin} to '{value}'")
