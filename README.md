# MASTR BOT
<p align="center">
  ![Preview](/img/videoexamplegithub.gif)
</p>
## What is MASTR-BOT ?

MASTR-BOT stands for multi-axis simultaneous transportation system, and is a master's thesis, conducted with Isochronic, on their novel technology.

In this project, user interface has been developped using Typescript (with React.JS + Next.JS). This user interface incorporates a tab that allows the user to edit any parameter of this project, and change the layout of this machine. Additionally, a visualisation tool has been developped to visualize the simulations. The visualisation is not live, but rather reads a json the program wrote. The user can go forward and backward through the simulation, as well as change the play speed.

The entire control software for this project was also fully developped, using Python.

There are a few explanation of how the program works, but for better understanding, I recommend reading the master's thesis report, which is available here.

## Installation

This project was made using python 3.10.0.

The libraries required for this project are `ruckig`, `numpy` and `pandas`. If the users wants to visualize the simulation with the python script instead, the old code was kept and uses `matplotlib`.
Finally, the user can install all of the required libraries with

```bash
pip install -r scripts/requirements.txt
```

### How to run the python script

The python script can be launched by running :

```bash
python script/main.py
```

to run it with the default settings, or

```bash
python script/main.py -buidHelper
```

to be guided through the different running parameter.

The different parameters are :

- -pre_move : Activate the premove
- -state_bouncing : Activate the state-bouncing
- -single_run : Make a single simulation run, instead of multiple one
- -save_hist : To save the simulation in a .json. This is necessary to visualize the simulation in the user interface
- -no_csv : Prevent the program from saving the data in a .csv. This is used to analyse the simulation in the jupter notebook
- -name : Name under which to save the .json or the .csv
- -seed : seed to use if required.

### How to run the user interface

To run the user interface, the user needs to install [Node.JS](https://nodejs.org/en).

Then, everything can be installed by running :

```bash
npm install
```

After that, the page can be launched by running :

```bash
npm run dev
```

Finally, to be able to run the python script from the web page, you'll need to start a python server using :
```bash
python server.py
```

## In depth look

The goal of this project is to provide a control algorithm for the Isochronic's novel kinematic.
This robot consist of a beam, with a set of rail on each side, and multiple sliders per side. It was programmed have two sliders work together at the same time.
![The robot's beam](/img/ExcenterBeam.PNG)
![The robot's slider](/img/miniDelta2D.png)
With the current configuration, the layout consists of two conveyors, one for the inflow, and one for the outflow, in a counter-current configuration.

This entire project was also made to be modular. Right now, the conveyors and the beams can be changed with the parameters, to fit the customer's need. However, it has mostly been tested with the current configuration and may present some bugs, which should be reported using a github issue.

Ideally, in a later time, different kind of machine should be usable with this simulation tool, such as delta robots, for instance.

### What does the python script do

The python script runs the simulation offline, according to the specification from `params.json`. Then, it will run, by computing the robot's situation at every time step. It uses [ruckig](https://github.com/pantor/ruckig) as a profile generator. <br />
In the control loop, there is a hierarchical state machine, with the first one being the state of the rails.
![rail state loop](/img/RAILSTATE.drawio.png)
Then, and only then, do we look at the state of the sliders, on said beam.
The state machine can get a little complex, this decision flow chart explains the working fundamental of the code, for a slider. As mentionned previously, two sliders always work together, so their states are somewhat linked
![Decision diagram](/img/NewSearchAlgo.drawio.png)

An important notion to grasp to understand this code is the first and second slider.
When looking at the list of available targets, we sort the said list using the scheduling. The higher a target is in the list, the higher its priority is. Using the same idea, we can define a first and second slider. The first slider should never ever block the second slider, unless it is picking the last item in a row, in which case the second slider is skipped. Following this logic, if the lowest x-value target is considered the highest priority, then the lowest x-value slider on a rail is considered the first slider.<br />
This is a decision taken to ease the target assignment. Furthermore, the target assignment on the first slider is always permanent. The second isn't. When a target is given to the second slider, only then do we check for collisions, and then decide whether to keep the assigned target or not.<br />
Finally, if only one of the two sliders has been assigned a target at a given timeframe, then the other slider's is set to be positionned next to the assigned slider, in order to avoid any possible collision.

### The state-bouncing

The state-bouncing is an improvement brought to the control algorithm after visually inspecting the simulations. The goal of this method is to prevent idle time when we can by attempting both picking and placing at the same time.<br />
<br />
<video src="https://github.com/user-attachments/assets/e8cd0e13-5613-48cd-ba36-d255a9e199ea"></video>
<br />
As seen in the video above, there are scenarios where only one of the two sliders pick a target, and then, we wait for the others to finally find a suitable target. However, in some cases, we may have time to go place the first target, and come back to the current conveyor, before the next one is available. To determine whether we can, we first try to do the current action, here picking, with a larger looking range which simulates a back and forth movement to the other conveyor. Then, if it wasn't succesful, we check whether we can do the other action, which is, here, placing the current target.

By enabling the state-bouncing, the following happens (look at slider 13 & 14) :
<br />
<video src="https://github.com/user-attachments/assets/686fbdf5-8b8c-4227-8ff8-56a4ccd98b18"></video>
<br />

### The pre-move
The pre-move is another method which aims to improve to responsiveness of the system. When both slider have either picked/placed an item, we know that the next action will be to place/pick an item respectively. Therefore, we can already move the slider to the other conveyor.

This is best seen when looked at the start routine :
<br />
<video src="https://github.com/user-attachments/assets/8f9b08fd-f119-49b1-b5b3-25b4fd6133d4"></video>
<br />

and with the pre-move enabled, this is the result :
<br />
<video src="https://github.com/user-attachments/assets/8f9e2240-a659-4165-89f6-14999b625601"></video>
<br />

With later modifications, this method has proven to be close to non impactful. The function responsible of looking for target candidate now has a similar behavior, where it looks for target with an additionnal range, which simulate the travel time from one conveyor to the other. However, the pre-move method was kept into the code, in case it is needed in the future.

## Future work 
Even though this master's project is done, the project itself can still be improved upon. It lays the foundation for future work to be done, and is available for anyone to use, under the specified license.

Some possible improvement that could be brought to the code are :
- [ ] A better start routine : Currently, the start routine isn't ideal. A lot of loss are created during this start routine, until the system stabilizes. One possible way to fix this would be to change the code so that the conveyor could start and stop, to avoid any loss, which brings to the next point :
- [ ] To avoid any possible loss, the best way to be to have the conveyor start and stop, on demand. However, this approach isn't compatible with the `findViableTarget` function. This target makes the assumption the conveyor has a constant speed, and tries to find a meeting point between the slider and the target using this assumption. If the conveyor can now stop on demand, this function won't predict it, and it could lead to system's stalling, or even bricking. This should be kept in mind when trying to enable to the start/stop method. Furthermore, we would need to take into account the conveyor's acceleration and possibly the jerk too with this, which could change a lot of things.
- [ ] Different scheduling options could be found, or a better analysis of the scheduling combination, to find a pattern and determine a rule of thumb, which would help decide which scheduling to use where, in which scenario.
- [ ] A second layer of strategy could also be used, for instance to assign the target to each beam, as soon as they appear, as it was done in this [paper](https://ieeexplore.ieee.org/abstract/document/7301450?casa_token=yLKB8oO0aq4AAAAA:4Z4372dm-heJp0Yxi5GdeotyAFSdSkHB7RpAiZK7c0szd5nJMagHpaVIIeczfBGNn8QIARtqZA).
- [ ] The program was mainly tested with the current layout. The goal of this software is to be flexible, and it should be tested, to find any bugs or unexpected behaviors.
- [ ] Additionally, we could add different machines to the software, such as delta robot, to improve the flexibility of the firmware.

These are only a few ideas, and there a certainly a lot more. You are welcome to try and improve this firmware however you want, and contribute to this github's page.

I will personally try to keep working on it on my free time.