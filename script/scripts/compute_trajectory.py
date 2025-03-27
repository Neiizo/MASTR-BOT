from typing import List
from ruckig import InputParameter, OutputParameter, Ruckig, Trajectory, ControlInterface

from description.objects import Object
from description.constants import *
import description.config as cfg


def initRuckig(*args: Object):
    ## right now it cannot take a nested list, such as the sliders list. Fix this
    for obj in args:
        obj.otg = Ruckig(obj.DoF, cfg.dt)
        obj.dt = cfg.dt

        obj.inp = InputParameter(obj.DoF)
        obj.out = OutputParameter(obj.DoF)

        # Set input parameters
        obj.inp.current_position = [
            round(num * MM_TO_M, ROUNDING_DECIMALS) for num in obj.position
        ]
        obj.inp.current_velocity = [
            round(num * MM_TO_M, ROUNDING_DECIMALS) for num in obj.currentVelocity
        ]

        obj.inp.target_position = [
            round(num * MM_TO_M, ROUNDING_DECIMALS) for num in obj.targetPosition
        ]

        obj.inp.max_velocity = [
            round(num * MM_TO_M, ROUNDING_DECIMALS) for num in obj.maxVelocity
        ]
        obj.inp.max_acceleration = [
            round(num * MM_TO_M, ROUNDING_DECIMALS) for num in obj.maxAccel
        ]

        try:  
            obj.inp.max_jerk = [round(num * MM_TO_M) for num in obj.maxJerk]
            obj.inp.current_acceleration = obj.currentAcceleration
            obj.inp.target_acceleration = obj.currentAcceleration
        except AttributeError:
            pass

        obj.trajectory = Trajectory(obj.DoF)


def updateRuckig(obj: Object):
    """Compute the trajectory of the objects in the simulation. Only for sliders"""
    # print("Updating Ruckig")
    #
    obj.inp.current_position = [
        round(num, ROUNDING_DECIMALS) for num in obj.inp.current_position
    ]
    obj.inp.current_velocity = [
        round(num, ROUNDING_DECIMALS) for num in obj.inp.current_velocity
    ]
    obj.inp.current_acceleration = [
        round(num, ROUNDING_DECIMALS) for num in obj.inp.current_acceleration
    ]
    obj.inp.target_position = [
        round(num * MM_TO_M, ROUNDING_DECIMALS) for num in obj.targetPosition
    ]

    obj.moveStatus = obj.otg.update(obj.inp, obj.out)
    obj.position = [num * M_TO_MM for num in obj.out.new_position]
    obj.currentVelocity = [num * M_TO_MM for num in obj.out.new_velocity]
    obj.currentAcceleration = [num * M_TO_MM for num in obj.out.new_acceleration]
    obj.out.pass_to_input(obj.inp)


def computeWholeTrajectory(obj: Object, targetPos: List[float]):

    obj.inp.target_position = [
        round(num * MM_TO_M, ROUNDING_DECIMALS) for num in targetPos
    ]
    obj.inp.current_velocity = [
        round(num * MM_TO_M, ROUNDING_DECIMALS) for num in obj.currentVelocity
    ]
    obj.moveStatus = obj.otg.calculate(obj.inp, obj.trajectory)

    travel_time = obj.trajectory.duration
    return travel_time
