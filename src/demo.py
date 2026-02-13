from user_security.operator import Operator
from machines_sensors.machine import Machine

def demo_basic_control():
    operator = Operator(1, "op", "op123")
    machine = Machine(101)

    user = input("Enter userID: ")
    password = input("Enter password: ")

    if operator.login(user, password):
        print("Operator logged in")

        if machine.validateCommand("START"):
            machine.start()
            print("Machine started")
    else:
        print("Login failed")

    print("Demo complete")

if __name__ == "__main__":
    demo_basic_control()
