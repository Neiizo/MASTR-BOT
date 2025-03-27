import numpy as np
import json
import matplotlib

matplotlib.use("TkAgg")  # Ensure Matplotlib uses the TkAgg backend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import logging

from constants import *
from robot_definition import Map

GENERATE_MAP = True


class ctkApp(ctk.CTk):
    def __init__(self):
        ## Move the entire class into its own file.
        super().__init__()

        self.title("Conveyor simulation")
        self.geometry("1200x750")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.map = Map()  # Create an instance of the Map class

        self.displayButtonCoordFrame()
        self.displayRailStatus()

        # self.reset_button = ctk.CTkButton(master=self, text='Reset', command=self.init_map_plot)
        # self.reset_button.pack(side=ctk.BOTTOM)

        # Call the function to initialize the Matplotlib plot
        self.init_map_plot()

    def displayButtonCoordFrame(self):
        self.rowSelection = []
        self.sliderButtons = []
        self.selectedRow = ctk.IntVar()

        self.buttonFrame = ctk.CTkFrame(self, fg_color="transparent")
        self.buttonFrame.place(
            relx=0.5, rely=0.9, relheight=0.2, relwidth=0.4, anchor="center"
        )

        self.buttonLabel = ctk.CTkLabel(
            master=self.buttonFrame, text="Select a slider to see its position"
        )
        self.buttonLabel.pack(pady=5)

        self.rowButtonFrame = ctk.CTkFrame(self.buttonFrame, fg_color="transparent")
        self.rowButtonFrame.pack()

        nbRails = self.map.param["beam"]["nbYAxis"]
        nbRails = (
            nbRails * 2 if self.map.param["beam"]["isDualRailPerAxis"] else nbRails
        )
        for id in range(nbRails):
            self.rowSelection.append(
                ctk.CTkRadioButton(
                    master=self.rowButtonFrame,
                    text="Row {}".format(id),
                    variable=self.selectedRow,
                    value=id,
                )
            )
            self.rowSelection[-1].grid(row=0, column=id, pady=3)

        self.buttonPosFrame = ctk.CTkFrame(self.buttonFrame, fg_color="transparent")
        self.buttonPosFrame.pack()

        for i in range(self.map.param["beam"]["nbSliderPerRail"]):
            self.sliderButtons.append(
                ctk.CTkButton(
                    master=self.buttonPosFrame,
                    text="Slider {}".format(i),
                    command=lambda idx=i: self.showSliderPos(idx),
                )
            )
            self.sliderButtons[-1].grid(row=1, column=i, pady=3)

        self.update_button = ctk.CTkButton(
            master=self.buttonFrame, text="Update Map", command=self.update_map
        )
        self.update_button.pack(side=ctk.BOTTOM, pady=10)

    def displayRailStatus(self):

        self.railsStatesText = ctk.CTkFrame(master=self, fg_color="transparent")
        self.railsStatesText.place(relx=0, rely=0.8, relheight=0.2, relwidth=0.3)

        self.railsStates = []
        self.railsStatesVar = []

        nbRails = self.map.param["beam"]["nbYAxis"]
        nbRails = (
            nbRails * 2 if self.map.param["beam"]["isDualRailPerAxis"] else nbRails
        )
        for id in range(nbRails):
            self.railsStates.append(
                ctk.CTkLabel(master=self.railsStatesText, text="Row {}".format(id))
            )
            self.railsStates[-1].grid(row=id, column=0, padx=20)
            self.railsStatesVar.append(ctk.StringVar())
            self.railsStates.append(
                ctk.CTkLabel(
                    master=self.railsStatesText, textvariable=self.railsStatesVar[id]
                )
            )
            self.railsStates[-1].grid(row=id, column=1, padx=20)

    def showSliderPos(self, idx):
        row = self.selectedRow.get()
        slider = self.map.sliders[row][idx]
        xEnd = slider.xPos + self.map.param["slider"]["armLength"] * np.cos(
            slider.armAngle
        )
        yEnd = slider.yPos + self.map.param["slider"]["armLength"] * np.sin(
            slider.armAngle
        )

        print(
            "Slider {} of row {} is at position: x={}, y={}, angle={:.2f}, Target at x={:.2f}, y={:.2f}".format(
                idx, row, slider.xPos, slider.yPos, slider.armAngle, xEnd, yEnd
            )
        )

    def init_map_plot(self):
        ## Maybe move all of these plot function inside plot.py
        self.fig, self.axis = plt.subplots()
        minX = self.map.param["map"]["minX"]
        maxX = self.map.param["map"]["maxX"]
        minY = self.map.param["map"]["minY"]
        maxY = self.map.param["map"]["maxY"]

        self.axis.set_xlim(minX, maxX)
        self.axis.set_ylim(minY, maxY)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.place(relx=0, rely=0, relwidth=1, relheight=0.8)

        # Plot initial data
        self.update_map()
        self.canvas.draw_idle()

    def update_map(self):
        logging.basicConfig(level=logging.DEBUG)
        self.map.update(5)
        self.update_robot_plot()
        self.plot_robot_arm()
        self.plot_drop_locations()
        self.canvas.draw_idle()

        for i in range(len(self.railsStatesVar)):
            if self.map.railStatus[i] == CAN_PICK:
                self.railsStatesVar[i].set("CAN_PICK")
            elif self.map.railStatus[i] == PICKING:
                self.railsStatesVar[i].set("PICKING")
            elif self.map.railStatus[i] == CAN_PLACE:
                self.railsStatesVar[i].set("CAN_PLACE")
            elif self.map.railStatus[i] == PLACING:
                self.railsStatesVar[i].set("PLACING")

    def update_robot_plot(self):
        """Give the correct color to each point, and will plot each arm of the robot."""
        self.axis.cla()  # Clear the current axis to redraw points with updated colors

        # Redraw rail regions for visual context
        minX = self.map.param["map"]["minX"]
        maxX = self.map.param["map"]["maxX"]
        minY = self.map.param["map"]["minY"]
        maxY = self.map.param["map"]["maxY"]
        self.axis.set_xlim(minX, maxX)
        self.axis.set_ylim(minY, maxY)
        YPickUpArea = (
            self.map.param["slider"]["armLength"]
            + self.map.param["beam"]["railOffset"]
            - self.map.pickUpSafetyMargin / 2
        )
        for i in range(len(self.map.axisYPosList)):
            if i % 2 == 0:
                yStart = (
                    self.map.axisYPosList[i] - self.map.param["slider"]["armLength"]
                )
            else:
                yStart = (
                    self.map.axisYPosList[i]
                    - self.map.param["beam"]["railOffset"]
                    + self.map.pickUpSafetyMargin / 2
                )
            rail = patches.Rectangle(
                (minX, yStart),
                maxX - minX,
                YPickUpArea,
                edgecolor="r",
                facecolor="red",
                alpha=0.2,
                label="Rail region",
            )
            self.axis.add_patch(rail)
            self.axis.axhline(
                y=self.map.axisYPosList[i], color="black", linestyle="--", linewidth=1
            )
            self.axis.text(
                minX - 50, self.map.axisYPosList[i] - 7, "Rail {}".format(i + 1)
            )

        dropRegion = patches.Rectangle(
            (self.map.param["dropRegion"]["startXPosition"], minY),
            self.map.param["dropRegion"]["width"],
            maxY - minY,
            edgecolor="g",
            facecolor="green",
            alpha=0.2,
            label="Drop region",
        )
        self.axis.add_patch(dropRegion)

        conveyor = patches.Rectangle(
            (
                self.map.param["conveyor"]["endXPosition"]
                - self.map.param["conveyor"]["width"],
                minY,
            ),
            self.map.param["conveyor"]["width"],
            maxY - minY,
            edgecolor="g",
            facecolor="green",
            alpha=0.2,
            label="Drop region",
        )
        self.axis.add_patch(conveyor)

        # Iterate through each target point and plot with the correct color
        for i, point in enumerate(self.map.listTarget):
            if self.map.targetStatus[i] == FREE or self.map.targetStatus[i] == SKIPPED:
                self.axis.scatter(point[0], point[1], color="blue", s=50)
                self.map.targetStatus[i] = FREE
            elif self.map.targetStatus[i] == ASSIGNED:
                self.axis.scatter(point[0], point[1], color="red", s=50)
                self.map.targetStatus[i] = GONE
            elif self.map.targetStatus[i] == GONE:
                pass

    def plot_robot_arm(self):
        """Plot the arms of the robot."""
        armLength = self.map.param["slider"]["armLength"]
        carriageWidth = self.map.param["slider"]["carriageWidth"]
        safetyMargin = self.map.param["slider"]["safetyMargin"]

        for rows in self.map.sliders:
            for i, slider in enumerate(rows):
                xEnd = slider.xPos + armLength * np.cos(slider.armAngle)
                yEnd = slider.yPos + armLength * np.sin(slider.armAngle)

                self.axis.plot(
                    [slider.xPos, xEnd], [slider.yPos, yEnd], color="blue", linewidth=2
                )
                self.axis.scatter(slider.xPos, slider.yPos, color="black", s=50)
                sliderRect = patches.Rectangle(
                    (slider.xPos - carriageWidth / 2, slider.yPos - carriageWidth / 2),
                    carriageWidth,
                    carriageWidth,
                    edgecolor="black",
                    facecolor="black",
                    alpha=0.5,
                    label="Carriage",
                )
                self.axis.text(
                    slider.xPos - 30, slider.yPos + 30, "Slider {}".format(i)
                )
                self.axis.add_patch(sliderRect)

                circle = patches.Circle(
                    (xEnd, yEnd),
                    self.map.param["slider"]["pickUpArea"] / 2,
                    edgecolor="red",
                    facecolor="red",
                    alpha=0.2,
                    label="Pickup area",
                )
                self.axis.add_patch(circle)

                ## Representation of the safety margin surrounding the sliders
                safetyMarginRect = patches.Rectangle(
                    (
                        slider.xPos - self.map.carriageSafetyMargin / 2,
                        slider.yPos - self.map.carriageSafetyMargin / 2,
                    ),
                    self.map.carriageSafetyMargin,
                    self.map.carriageSafetyMargin,
                    edgecolor="black",
                    alpha=0.3,
                    label="Carriage",
                )
                safetyMarginRect.set_facecolor("none")
                safetyMarginRect.set_linestyle("-.")
                self.axis.add_patch(safetyMarginRect)

                safetyMarginCircle = patches.Circle(
                    (xEnd, yEnd),
                    self.map.param["slider"]["pickUpArea"] / 2 + safetyMargin / 2,
                    edgecolor="red",
                    alpha=0.2,
                    label="Pickup area",
                )
                safetyMarginCircle.set_facecolor("none")
                safetyMarginCircle.set_linestyle(":")
                self.axis.add_patch(safetyMarginCircle)

    def plot_drop_locations(self):
        for i, rows in enumerate(self.map.listDrop):
            for j, drop in enumerate(rows):
                if self.map.dropStatus[i, j] == ASSIGNED:
                    self.axis.scatter(drop[0], drop[1], color="blue", s=50)
                    self.map.dropStatus[i, j] = GONE
                elif self.map.dropStatus[i, j] == GONE:
                    self.axis.scatter(drop[0], drop[1], color="blue", s=50)
                else:
                    self.map.dropStatus[i, j] = FREE
                circle = patches.Circle(
                    (drop[0], drop[1]),
                    self.map.param["slider"]["pickUpArea"] / 3,
                    edgecolor="green",
                    facecolor="green",
                    alpha=0.2,
                    label="Drop area",
                )
                self.axis.add_patch(circle)

    def on_closing(self):
        plt.close("all")  # Close all Matplotlib plots
        self.destroy()  # Destroy the Tkinter window


if __name__ == "__main__":

    ### If you want to generate new data, set GENERATE_MAP to True.
    if GENERATE_MAP:
        ### ------------ Defines the environement ------------ ###
        param = {}
        param["map"] = {}
        param["map"]["minX"] = 0
        param["map"]["maxX"] = 1520
        param["map"]["minY"] = 0
        param["map"]["maxY"] = 920

        param["dropRegion"] = {}
        param["dropRegion"]["startXPosition"] = 50
        param["dropRegion"]["width"] = 650

        param["conveyor"] = {}
        param["conveyor"]["width"] = 650
        param["conveyor"]["endXPosition"] = param["map"]["maxX"] - 100

        ### -------- Simulate the detection algorithm -------- ###

        param["target"] = {}
        param["target"]["targetPerRow"] = 8
        param["target"]["targetXSpacing"] = 65
        param["target"]["targetYSpacing"] = 25
        param["target"]["xOffset"] = 40

        param["dropTarget"] = {}
        param["dropTarget"]["pattern"] = "circle"  # 'line' or 'circle' for now
        param["dropTarget"]["nbPatternPerRow"] = 2
        param["dropTarget"]["patternSpacing"] = 250
        param["dropTarget"]["xOffset"] = 200  ## maybe remove this and do it dynamically
        param["dropTarget"]["nbTargetPerPattern"] = 5
        param["dropTarget"]["patternWidth"] = 200

        ## make it so we can also provide a list of position, that would represent a single pattern

        ### ---------------- Defines the robot --------------- ###
        # try to add a parameter that would determine the orientation of the sliders and the conveyors
        param["slider"] = {}
        param["slider"]["armLength"] = 70
        param["slider"]["carriageWidth"] = 100
        param["slider"]["firstCableLength"] = 1200  ## TBD
        param["slider"]["cableLength"] = 300
        param["slider"]["safetyMargin"] = 10
        param["slider"]["pickUpArea"] = 32

        param["beam"] = {}
        param["beam"]["nbYAxis"] = 1
        param["beam"]["isDualRailPerAxis"] = True
        param["beam"]["railOffset"] = 60
        param["beam"]["axisSpacing"] = 400  ## TBD
        param["beam"]["firstAxisYPos"] = 200
        param["beam"]["nbSliderPerRail"] = 2
        ###  WARNING !! make sure the side of the first carriage in the installation fits the code !! Right now, it's the first on the x coord

        with open("ExcenterAlgoPython/map_param.json", "w") as f:
            json.dump(param, f, indent=4)

    ###----------------------------------------------------------------------###

    ctk.set_appearance_mode("System")  # Modes: system (default), light, dark
    ctk.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

    app = ctkApp()
    app.mainloop()


# TODO
"""
Check for unexpected behavior, for instance when we set the wrong axis limit, it triggers the error
Add a reset button

bad handling when we go to limit. You can test this whent he first cable length is 1000
"""
