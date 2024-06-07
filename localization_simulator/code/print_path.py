import customtkinter
from tkintermapview import TkinterMapView
import tkinter
from set_path import wanted_marker
from to_broker import messages
from datetime import datetime
from PIL import Image, ImageTk
import os
import shutil
import json
import ast
from tkinter import filedialog

customtkinter.set_default_color_theme("blue")


class App(customtkinter.CTk):

    APP_NAME = "Localization Simulator - Press Ctl+Q to quit"
    WIDTH = 1200
    HEIGHT = 650

    def __init__(self,  icon: tkinter.PhotoImage = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title(App.APP_NAME)
        self.geometry(str(App.WIDTH) + "x" + str(App.HEIGHT))
        self.minsize(App.WIDTH, App.HEIGHT)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind("<Control-q>", self.on_closing)

        # ============ create two CTkFrames ============

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.frame_left = customtkinter.CTkFrame(master=self, width=150, corner_radius=0, fg_color=None)
        self.frame_left.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

        self.frame_right = customtkinter.CTkFrame(master=self, corner_radius=0)
        self.frame_right.grid(row=0, column=1, rowspan=1, pady=0, padx=0, sticky="nsew")

        # ============ frame_left ============

        self.frame_left.grid_rowconfigure(2, weight=1)

        self.broker_button = customtkinter.CTkEntry(master=self.frame_left, placeholder_text="Broker IP")
        self.broker_button.grid(pady=(10, 0), padx=(5, 0), row=0, column=0)

        self.source_id_button = customtkinter.CTkEntry(master=self.frame_left, placeholder_text="source ID")
        self.source_id_button.grid(pady=(10, 0), padx=(5, 0), row=2, column=0, sticky = "n")  

        self.send_image = customtkinter.CTkImage(light_image=Image.open(os.path.join("./", "send2.png")), size=(20, 20))

        self.send = customtkinter.CTkButton(master=self.frame_left, text="send to broker", command = self.send_message, fg_color="green", hover_color="light green", image=self.send_image, state = "normal")
        self.send.grid(pady=(10, 0), padx=(5, 0), row=4, column=0)

        self.save_image = customtkinter.CTkImage(light_image=Image.open(os.path.join("./", "disk2.png")), size=(20, 20))
        
        self.save = customtkinter.CTkButton(master=self.frame_left, text="save session", command = self.save_message, fg_color="purple", hover_color="magenta", image=self.save_image)
        self.save.grid(pady=(10, 0), padx=(5, 0), row=4, column=1)

        self.load_image = customtkinter.CTkImage(light_image=Image.open(os.path.join("./", "load4.png")), size=(20, 20))

        self.load = customtkinter.CTkButton(master=self.frame_left, text="load session", command = self.load_message, fg_color="purple", hover_color="magenta", image=self.load_image)
        self.load.grid(pady=(10, 0), padx=(5, 0), row=5, column=1)


        self.map_label = customtkinter.CTkLabel(self.frame_left, text="Tile Server:", anchor="w")
        self.map_label.grid(row=5, column=0, padx=(5, 0), pady=(20, 0))
        self.map_option_menu = customtkinter.CTkOptionMenu(self.frame_left, values=["OpenStreetMap", "Google normal", "Google satellite", "Paint", "Black and White", "Terrain"],
                                                                       command=self.change_map)
        self.map_option_menu.grid(row=6, column=0, padx=(5, 0), pady=(10, 0))

        self.appearance_mode_label = customtkinter.CTkLabel(self.frame_left, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=7, column=0, padx=(5, 0), pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.frame_left, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode)
        self.appearance_mode_optionemenu.grid(row=8, column=0, padx=(5, 0), pady=(10, 0))

        self.switches = customtkinter.CTkLabel(self.frame_left, text="Enable noise") 
        self.switches.grid(row=9, column=1, padx=(50, 0), pady=(40, 0))   
        self.tools = customtkinter.CTkLabel(self.frame_left, text="Choose tool(s)") 
        self.tools.grid(row=9, column=0, padx=(50, 0), pady=(40, 0)) 

        self.var1 = tkinter.IntVar()
        self.var2 = tkinter.IntVar()
        self.var3 = tkinter.IntVar()
        self.var4 = tkinter.IntVar()
        self.switch_visual = customtkinter.StringVar(value="off")
        self.switch_inertio = customtkinter.StringVar(value="off")
        self.switch_galileo = customtkinter.StringVar(value="off")
        self.switch_fusion = customtkinter.StringVar(value="off")

        self.visual_button = customtkinter.CTkCheckBox(master=self.frame_left, 
                                                  text = "visual",
                                                  command=self.hi,
                                                  variable=self.var1, onvalue=1, offvalue=0)
        self.visual_button.grid(pady=(10, 0), padx=(0, 10), row=10, column=0)
        self.time_visual = customtkinter.CTkEntry(master=self.frame_left, placeholder_text="time diff (s)", width = 90)
        self.time_visual.grid(pady=(10, 0), padx=(150, 10), row=10, column=0)
        self.visual_noise = customtkinter.CTkSwitch(master=self.frame_left, 
                                                  text = "",
                                                  command=self.hi,
                                                  variable=self.switch_visual, onvalue="on", offvalue="off", progress_color="green")
        self.visual_noise.grid(pady=(10, 0), padx=(20, 50), row=10, column=1)
        self.visual_std = customtkinter.CTkEntry(master=self.frame_left, placeholder_text="noise std", width = 90)
        self.visual_std.grid(pady=(10, 0), padx=(100, 40), row=10, column=1)


        self.inertio_button = customtkinter.CTkCheckBox(master=self.frame_left, 
                                                  text="inertio",
                                                  command=self.hi,
                                                  variable=self.var2, onvalue=1, offvalue=0)
        self.inertio_button.grid(pady=(10, 0), padx=(0, 10), row=11, column=0)
        self.time_inertio = customtkinter.CTkEntry(master=self.frame_left, placeholder_text="time diff (s)", width = 90)
        self.time_inertio.grid(pady=(10, 0), padx=(150, 10), row=11, column=0)
        self.inertio_noise = customtkinter.CTkSwitch(master=self.frame_left, 
                                                  text = "",
                                                  command=self.hi,
                                                  variable=self.switch_inertio, onvalue="on", offvalue="off", progress_color="green")
        self.inertio_noise.grid(pady=(10, 0), padx=(20, 50), row=11, column=1)
        self.inertio_std = customtkinter.CTkEntry(master=self.frame_left, placeholder_text="noise std", width = 90)
        self.inertio_std.grid(pady=(10, 0), padx=(100, 40), row=11, column=1)


        self.galileo_button = customtkinter.CTkCheckBox(master=self.frame_left, 
                                                  text="galileo",
                                                  command=self.hi,
                                                  variable=self.var3, onvalue=1, offvalue=0)
        self.galileo_button.grid(pady=(10, 0), padx=(0, 10), row=12, column=0)
        self.time_galileo = customtkinter.CTkEntry(master=self.frame_left, placeholder_text="time diff (s)", width = 90)
        self.time_galileo.grid(pady=(10, 0), padx=(150, 10), row=12, column=0)
        self.galileo_noise = customtkinter.CTkSwitch(master=self.frame_left, 
                                                  text = "",
                                                  command=self.hi,
                                                  variable=self.switch_galileo, onvalue="on", offvalue="off", progress_color="green")
        self.galileo_noise.grid(pady=(10, 0), padx=(20, 50), row=12, column=1)
        self.galileo_std = customtkinter.CTkEntry(master=self.frame_left, placeholder_text="noise std", width = 90)
        self.galileo_std.grid(pady=(10, 0), padx=(100, 40), row=12, column=1)


        self.fusion_button = customtkinter.CTkCheckBox(master=self.frame_left, 
                                                  text="fusion",
                                                  command=self.hi,
                                                  variable=self.var4, onvalue=1, offvalue=0)
        self.fusion_button.grid(pady=(10, 0), padx=(0, 10), row=13, column=0)
        self.time_fusion = customtkinter.CTkEntry(master=self.frame_left, placeholder_text="time diff (s)", width = 90)
        self.time_fusion.grid(pady=(10, 0), padx=(150, 10), row=13, column=0)
        self.fusion_noise = customtkinter.CTkSwitch(master=self.frame_left, 
                                                  text = "",
                                                  command=self.hi,
                                                  variable=self.switch_fusion, onvalue="on", offvalue="off", progress_color="green")
        self.fusion_noise.grid(pady=(10, 0), padx=(20, 50), row=13, column=1)
        self.fusion_std = customtkinter.CTkEntry(master=self.frame_left, placeholder_text="noise std", width = 90)
        self.fusion_std.grid(pady=(10, 0), padx=(100, 40), row=13, column=1)

        self.speed = customtkinter.CTkEntry(master=self.frame_left, placeholder_text="speed (m/s)", width = 90)
        self.speed.grid(pady=(20, 20), padx=(0, 10), row=14, column=0)

        # ============ frame_right ============

        self.frame_right.grid_rowconfigure(1, weight=1)
        self.frame_right.grid_rowconfigure(0, weight=0)
        self.frame_right.grid_columnconfigure(0, weight=1)
        self.frame_right.grid_columnconfigure(1, weight=0)
        self.frame_right.grid_columnconfigure(2, weight=1)

        self.map_widget = TkinterMapView(self.frame_right, corner_radius=0)
        self.map_widget.grid(row=1, rowspan=1, column=0, columnspan=3, sticky="nswe", padx=(0, 0), pady=(0, 0))

        self.entry = customtkinter.CTkEntry(master=self.frame_right,
                                            placeholder_text="type address")
        self.entry.grid(row=0, column=0, sticky="we", padx=(12, 0), pady=12)
        self.entry.bind("<Return>", self.search_event)

        self.button_8 = customtkinter.CTkButton(master=self.frame_right,
                                                text="Search",
                                                width=90,
                                                command=self.search_event)
        self.button_8.grid(row=0, column=1, sticky="w", padx=(12, 0), pady=12)

        # Set default values
        self.map_widget.set_address("Thessaloniki")
        self.map_option_menu.set("OpenStreetMap")
        self.appearance_mode_optionemenu.set("Light")
        self.new_marker_1 = [] #list of every coordinate, both the ones added by the user and the wanted ones
        self.markers=[]
        self.map_widget.add_right_click_menu_command(label="Add Marker",
                                        command=self.add_marker_event,
                                        pass_coords=True)
        
        self.progress = customtkinter.CTkLabel(self.frame_left, text="Progress") 
        self.progress.grid(row=15, column=0, padx=(300, 0), pady=(10, 40)) 
        self.progress_button = customtkinter.CTkLabel(master=self.frame_left, width = 20, height = 20, text="0%")
        self.progress_button.grid(pady=(10, 40), padx=(0, 200), row=15, column=1)
                 
        self.visual_marker = wanted_marker()
        self.inertio_marker = wanted_marker()
        self.galileo_marker = wanted_marker()
        self.fusion_marker = wanted_marker()

    def search_event(self, event=None):
        self.map_widget.set_address(self.entry.get())

  
# The user enters the path, P1 with the wanted coordinates is created
    def add_marker_event(self, coords = (0,0)):
        print("Add marker:", coords)
    
        new_marker = self.map_widget.set_marker(coords[0], coords[1], text = "("+ str(coords[0]) +","+ str(coords[1])+")", font = "Tahoma 9", text_color = '#e61212')
        self.markers.append(new_marker)

            # Check the values of variables and execute the corresponding code
        while True:
            if (self.var1.get() == 0) & (self.var2.get() == 0) & (self.var3.get() == 0) & (self.var4.get() == 0):
                tkinter.messagebox.showerror(title=None, message="No tool selected. Please restart.")
                assert ((self.var1.get() == 1) or (self.var2.get() == 1) or (self.var3.get() == 1) or (self.var4.get() == 1)), "No tool selected"

            elif (self.var1.get() == 0) & (self.var2.get() == 0) & (self.var3.get() == 0) & (self.var4.get() == 1):
                print("fusion")          
                self.fusion_marker.new_marker_1.append(new_marker.position)
                self.fusion_marker.set_marker(dt = self.time_fusion.get(), speed = self.speed.get(), noise = self.switch_fusion.get(), std = self.fusion_std.get())
                break

            elif (self.var1.get() == 1) & (self.var2.get() == 1) & (self.var3.get() == 1) & (self.var4.get() == 0):
                print("visual")
                self.visual_marker.new_marker_1.append(new_marker.position)
                self.visual_marker.set_marker(dt = self.time_visual.get(), speed = self.speed.get(), noise = self.switch_visual.get(), std = self.visual_std.get())
                print("inertio")
                self.inertio_marker.new_marker_1.append(new_marker.position)
                self.inertio_marker.set_marker(dt = self.time_inertio.get(), speed = self.speed.get(), noise = self.switch_inertio.get(), std = self.inertio_std.get())
                print("galileo")          
                self.galileo_marker.new_marker_1.append(new_marker.position)
                self.galileo_marker.set_marker(dt = self.time_galileo.get(), speed = self.speed.get(), noise = self.switch_galileo.get(), std = self.galileo_std.get())
                break

            elif (self.var1.get() == 1) & (self.var2.get() == 1) & (self.var3.get() == 1) & (self.var4.get() == 1):
                print("visual")
                self.visual_marker.new_marker_1.append(new_marker.position)
                self.visual_marker.set_marker(dt = self.time_visual.get(), speed = self.speed.get(), noise = self.switch_visual.get(), std = self.visual_std.get())
                print("inertio")
                self.inertio_marker.new_marker_1.append(new_marker.position)
                self.inertio_marker.set_marker(dt = self.time_inertio.get(), speed = self.speed.get(), noise = self.switch_inertio.get(), std = self.inertio_std.get())
                print("galileo")          
                self.galileo_marker.new_marker_1.append(new_marker.position)
                self.galileo_marker.set_marker(dt = self.time_galileo.get(), speed = self.speed.get(), noise = self.switch_galileo.get(), std = self.galileo_std.get())
                print("fusion")          
                self.fusion_marker.new_marker_1.append(new_marker.position)
                self.fusion_marker.set_marker(dt = self.time_fusion.get(), speed = self.speed.get(), noise = self.switch_fusion.get(), std = self.fusion_std.get())
                break            

            elif (self.var1.get() == 1) & (self.var2.get() == 1) & (self.var3.get() == 0) & (self.var4.get() == 0):
                print("visual")
                self.visual_marker.new_marker_1.append(new_marker.position)
                self.visual_marker.set_marker(dt = self.time_visual.get(), speed = self.speed.get(), noise = self.switch_visual.get(), std = self.visual_std.get())
                print("inertio")
                self.inertio_marker.new_marker_1.append(new_marker.position)
                self.inertio_marker.set_marker(dt = self.time_inertio.get(), speed = self.speed.get(), noise = self.switch_inertio.get(), std = self.inertio_std.get())
                break

            elif (self.var1.get() == 1) & (self.var2.get() == 1) & (self.var3.get() == 0) & (self.var4.get() == 1):
                print("visual")
                self.visual_marker.new_marker_1.append(new_marker.position)
                self.visual_marker.set_marker(dt = self.time_visual.get(), speed = self.speed.get(), noise = self.switch_visual.get(), std = self.visual_std.get())
                print("inertio")
                self.inertio_marker.new_marker_1.append(new_marker.position)
                self.inertio_marker.set_marker(dt = self.time_inertio.get(), speed = self.speed.get(), noise = self.switch_inertio.get(), std = self.inertio_std.get())
                print("fusion")          
                self.fusion_marker.new_marker_1.append(new_marker.position)
                self.fusion_marker.set_marker(dt = self.time_fusion.get(), speed = self.speed.get(), noise = self.switch_fusion.get(), std = self.fusion_std.get())                
                break

            elif (self.var1.get() == 1) & (self.var2.get() == 0) & (self.var3.get() == 1) & (self.var4.get() == 0):
                print("visual")
                self.visual_marker.new_marker_1.append(new_marker.position)
                self.visual_marker.set_marker(dt = self.time_visual.get(), speed = self.speed.get(), noise = self.switch_visual.get(), std = self.visual_std.get())
                print("galileo")
                self.galileo_marker.new_marker_1.append(new_marker.position)
                self.galileo_marker.set_marker(dt = self.time_galileo.get(), speed = self.speed.get(), noise = self.switch_galileo.get(), std = self.galileo_std.get())
                break

            elif (self.var1.get() == 1) & (self.var2.get() == 0) & (self.var3.get() == 1) & (self.var4.get() == 1):
                print("visual")
                self.visual_marker.new_marker_1.append(new_marker.position)
                self.visual_marker.set_marker(dt = self.time_visual.get(), speed = self.speed.get(), noise = self.switch_visual.get(), std = self.visual_std.get())
                print("galileo")
                self.galileo_marker.new_marker_1.append(new_marker.position)
                self.galileo_marker.set_marker(dt = self.time_galileo.get(), speed = self.speed.get(), noise = self.switch_galileo.get(), std = self.galileo_std.get())
                print("fusion")          
                self.fusion_marker.new_marker_1.append(new_marker.position)
                self.fusion_marker.set_marker(dt = self.time_fusion.get(), speed = self.speed.get(), noise = self.switch_fusion.get(), std = self.fusion_std.get())   
                break

            elif (self.var1.get() == 0) & (self.var2.get() == 1) & (self.var3.get() == 1) & (self.var4.get() == 0):
                print("inertio")
                self.inertio_marker.new_marker_1.append(new_marker.position)
                self.inertio_marker.set_marker(dt = self.time_inertio.get(), speed = self.speed.get(), noise = self.switch_inertio.get(), std = self.inertio_std.get())
                print("galileo")
                self.galileo_marker.new_marker_1.append(new_marker.position)
                self.galileo_marker.set_marker(dt = self.time_galileo.get(), speed = self.speed.get(), noise = self.switch_galileo.get(), std = self.galileo_std.get())
                break  

            elif (self.var1.get() == 0) & (self.var2.get() == 1) & (self.var3.get() == 1) & (self.var4.get() == 1):
                print("inertio")
                self.inertio_marker.new_marker_1.append(new_marker.position)
                self.inertio_marker.set_marker(dt = self.time_inertio.get(), speed = self.speed.get(), noise = self.switch_inertio.get(), std = self.inertio_std.get())
                print("galileo")
                self.galileo_marker.new_marker_1.append(new_marker.position)
                self.galileo_marker.set_marker(dt = self.time_galileo.get(), speed = self.speed.get(), noise = self.switch_galileo.get(), std = self.galileo_std.get())
                print("fusion")          
                self.fusion_marker.new_marker_1.append(new_marker.position)
                self.fusion_marker.set_marker(dt = self.time_fusion.get(), speed = self.speed.get(), noise = self.switch_fusion.get(), std = self.fusion_std.get())   
                break  

            elif (self.var1.get() == 1) & (self.var2.get() == 0) & (self.var3.get() == 0) & (self.var4.get() == 0):
                print("visual")
                self.visual_marker.new_marker_1.append(new_marker.position)
                print(new_marker.position)
                self.visual_marker.set_marker(dt = self.time_visual.get(), speed = self.speed.get(), noise = self.switch_visual.get(), std = self.visual_std.get())
                break

            elif (self.var1.get() == 1) & (self.var2.get() == 0) & (self.var3.get() == 0) & (self.var4.get() == 1):
                print("visual")
                self.visual_marker.new_marker_1.append(new_marker.position)
                self.visual_marker.set_marker(dt = self.time_visual.get(), speed = self.speed.get(), noise = self.switch_visual.get(), std = self.visual_std.get())
                print("fusion")          
                self.fusion_marker.new_marker_1.append(new_marker.position)
                self.fusion_marker.set_marker(dt = self.time_fusion.get(), speed = self.speed.get(), noise = self.switch_fusion.get(), std = self.fusion_std.get()) 
                break

            elif (self.var1.get() == 0) & (self.var2.get() == 1) & (self.var3.get() == 0) & (self.var4.get() == 0):
                print("inertio")
                self.inertio_marker.new_marker_1.append(new_marker.position)
                self.inertio_marker.set_marker(dt = self.time_inertio.get(), speed = self.speed.get(), noise = self.switch_inertio.get(), std = self.inertio_std.get())
                break
        
            elif (self.var1.get() == 0) & (self.var2.get() == 1) & (self.var3.get() == 0) & (self.var4.get() == 1):
                print("inertio")
                self.inertio_marker.new_marker_1.append(new_marker.position)
                self.inertio_marker.set_marker(dt = self.time_inertio.get(), speed = self.speed.get(), noise = self.switch_inertio.get(), std = self.inertio_std.get())
                print("fusion")          
                self.fusion_marker.new_marker_1.append(new_marker.position)
                self.fusion_marker.set_marker(dt = self.time_fusion.get(), speed = self.speed.get(), noise = self.switch_fusion.get(), std = self.fusion_std.get()) 
                break

            elif (self.var1.get() == 0) & (self.var2.get() == 0) & (self.var3.get() == 1) & (self.var4.get() == 0):
                print("galileo")
                self.galileo_marker.new_marker_1.append(new_marker.position)
                self.galileo_marker.set_marker(dt = self.time_galileo.get(), speed = self.speed.get(), noise = self.switch_galileo.get(), std = self.galileo_std.get())
                break

            elif (self.var1.get() == 0) & (self.var2.get() == 0) & (self.var3.get() == 1) & (self.var4.get() == 1):
                print("galileo")
                self.galileo_marker.new_marker_1.append(new_marker.position)
                self.galileo_marker.set_marker(dt = self.time_galileo.get(), speed = self.speed.get(), noise = self.switch_galileo.get(), std = self.galileo_std.get())
                print("fusion")          
                self.fusion_marker.new_marker_1.append(new_marker.position)
                self.fusion_marker.set_marker(dt = self.time_fusion.get(), speed = self.speed.get(), noise = self.switch_fusion.get(), std = self.fusion_std.get())                 
                break


    def change_appearance_mode(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_map(self, new_map: str):
        if new_map == "OpenStreetMap":
            self.map_widget.set_tile_server("https://a.tile.openstreetmap.org/{z}/{x}/{y}.png")
        elif new_map == "Google normal":
            self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
        elif new_map == "Google satellite":
            self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
        elif new_map == "Paint":
            self.map_widget.set_tile_server("http://c.tile.stamen.com/watercolor/{z}/{x}/{y}.png",)
        elif new_map == "Black and White":
            self.map_widget.set_tile_server("http://a.tile.stamen.com/toner/{z}/{x}/{y}.png",)
        elif new_map == "Terrain":
            self.map_widget.set_tile_server("http://a.tile.stamen.com/terrain/{z}/{x}/{y}.png",)     


    def send_message(self):
        self.send.configure(state = "disabled")
        broker_messages = messages(brokerip = self.broker_button.get(), sourceid=self.source_id_button.get(), dateandtime=datetime.utcnow())

        while True:
            if (self.var1.get() == 1) & (self.var2.get() == 1) & (self.var3.get() == 1) & (self.var4.get() == 0):
                print("visual")
                vis = broker_messages.threads_visual(
                    visual_latitude = [self.visual_marker.P1[i][0] for i in range(len(self.visual_marker.P1))], 
                    visual_longitude = [self.visual_marker.P1[i][1] for i in range(len(self.visual_marker.P1))], 
                    visual_heading = [self.visual_marker.heading[i] for i in range(len(self.visual_marker.heading))],
                    visual_timediff= float(self.time_visual.get()), 
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get())
                print("inertio")
                iner = broker_messages.threads_inertio(
                    inertio_latitude = [self.inertio_marker.P1[i][0] for i in range(len(self.inertio_marker.P1))], 
                    inertio_longitude = [self.inertio_marker.P1[i][1] for i in range(len(self.inertio_marker.P1))], 
                    inertio_heading = [self.inertio_marker.heading[i] for i in range(len(self.inertio_marker.heading))],
                    inertio_timediff=float(self.time_inertio.get()),
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get())               
                print("galileo")
                gali = broker_messages.threads_galileo(
                    galileo_latitude = [self.galileo_marker.P1[i][0] for i in range(len(self.galileo_marker.P1))], 
                    galileo_longitude = [self.galileo_marker.P1[i][1] for i in range(len(self.galileo_marker.P1))], 
                    galileo_heading = [self.galileo_marker.heading[i] for i in range(len(self.galileo_marker.heading))],
                    galileo_timediff=float(self.time_galileo.get()),
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get())  
                broker_messages.send_messages_with_progress(messages = [vis, iner, gali], progress_button = self.progress_button, windowclass = self)
                break

            elif (self.var1.get() == 1) & (self.var2.get() == 1) & (self.var3.get() == 1) & (self.var4.get() == 1):
                print("visual")
                vis = broker_messages.threads_visual(
                    visual_latitude = [self.visual_marker.P1[i][0] for i in range(len(self.visual_marker.P1))], 
                    visual_longitude = [self.visual_marker.P1[i][1] for i in range(len(self.visual_marker.P1))], 
                    visual_heading = [self.visual_marker.heading[i] for i in range(len(self.visual_marker.heading))],
                    visual_timediff= float(self.time_visual.get()), 
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get())
                print("inertio")
                iner = broker_messages.threads_inertio(
                    inertio_latitude = [self.inertio_marker.P1[i][0] for i in range(len(self.inertio_marker.P1))], 
                    inertio_longitude = [self.inertio_marker.P1[i][1] for i in range(len(self.inertio_marker.P1))], 
                    inertio_heading = [self.inertio_marker.heading[i] for i in range(len(self.inertio_marker.heading))],
                    inertio_timediff=float(self.time_inertio.get()),
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get())               
                print("galileo")
                gali = broker_messages.threads_galileo(
                    galileo_latitude = [self.galileo_marker.P1[i][0] for i in range(len(self.galileo_marker.P1))], 
                    galileo_longitude = [self.galileo_marker.P1[i][1] for i in range(len(self.galileo_marker.P1))], 
                    galileo_heading = [self.galileo_marker.heading[i] for i in range(len(self.galileo_marker.heading))],
                    galileo_timediff=float(self.time_galileo.get()),
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get())  
                print("fusion")
                fus = broker_messages.threads_fusion(
                    fusion_latitude = [self.fusion_marker.P1[i][0] for i in range(len(self.fusion_marker.P1))], 
                    fusion_longitude = [self.fusion_marker.P1[i][1] for i in range(len(self.fusion_marker.P1))], 
                    fusion_heading = [self.fusion_marker.heading[i] for i in range(len(self.fusion_marker.heading))],
                    fusion_timediff=float(self.time_fusion.get()),
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get())  
                broker_messages.send_messages_with_progress(messages = [vis, iner, gali, fus], progress_button = self.progress_button, windowclass = self)
                break

            elif (self.var1.get() == 1) & (self.var2.get() == 1) & (self.var3.get() == 0) & (self.var4.get() == 0):
                print("visual")
                vis = broker_messages.threads_visual(
                    visual_latitude = [self.visual_marker.P1[i][0] for i in range(len(self.visual_marker.P1))], 
                    visual_longitude = [self.visual_marker.P1[i][1] for i in range(len(self.visual_marker.P1))], 
                    visual_heading = [self.visual_marker.heading[i] for i in range(len(self.visual_marker.heading))],
                    visual_timediff= float(self.time_visual.get()), 
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get())                
                print("inertio")
                iner = broker_messages.threads_inertio(
                    inertio_latitude = [self.inertio_marker.P1[i][0] for i in range(len(self.inertio_marker.P1))], 
                    inertio_longitude = [self.inertio_marker.P1[i][1] for i in range(len(self.inertio_marker.P1))],
                    inertio_heading = [self.inertio_marker.heading[i] for i in range(len(self.inertio_marker.heading))], 
                    inertio_timediff=float(self.time_inertio.get()),
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get()) 
                broker_messages.send_messages_with_progress(messages = [vis, iner], progress_button = self.progress_button, windowclass = self)
                break

            elif (self.var1.get() == 1) & (self.var2.get() == 1) & (self.var3.get() == 0) & (self.var4.get() == 1):
                print("visual")
                vis = broker_messages.threads_visual(
                    visual_latitude = [self.visual_marker.P1[i][0] for i in range(len(self.visual_marker.P1))], 
                    visual_longitude = [self.visual_marker.P1[i][1] for i in range(len(self.visual_marker.P1))], 
                    visual_heading = [self.visual_marker.heading[i] for i in range(len(self.visual_marker.heading))],
                    visual_timediff= float(self.time_visual.get()), 
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get())                
                print("inertio")
                iner = broker_messages.threads_inertio(
                    inertio_latitude = [self.inertio_marker.P1[i][0] for i in range(len(self.inertio_marker.P1))], 
                    inertio_longitude = [self.inertio_marker.P1[i][1] for i in range(len(self.inertio_marker.P1))], 
                    inertio_heading = [self.inertio_marker.heading[i] for i in range(len(self.inertio_marker.heading))],
                    inertio_timediff=float(self.time_inertio.get()),
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get()) 
                print("fusion")
                fus = broker_messages.threads_fusion(
                    fusion_latitude = [self.fusion_marker.P1[i][0] for i in range(len(self.fusion_marker.P1))], 
                    fusion_longitude = [self.fusion_marker.P1[i][1] for i in range(len(self.fusion_marker.P1))], 
                    fusion_heading = [self.fusion_marker.heading[i] for i in range(len(self.fusion_marker.heading))],
                    fusion_timediff=float(self.time_fusion.get()),
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get())  
                broker_messages.send_messages_with_progress(messages = [vis, iner, fus], progress_button = self.progress_button, windowclass = self)
                break

            elif (self.var1.get() == 1) & (self.var2.get() == 0) & (self.var3.get() == 1) & (self.var4.get() == 0):
                print("visual")
                vis = broker_messages.threads_visual(
                    visual_latitude = [self.visual_marker.P1[i][0] for i in range(len(self.visual_marker.P1))], 
                    visual_longitude = [self.visual_marker.P1[i][1] for i in range(len(self.visual_marker.P1))], 
                    visual_heading = [self.visual_marker.heading[i] for i in range(len(self.visual_marker.heading))],
                    visual_timediff= float(self.time_visual.get()), 
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get())                
                print("galileo")
                gali = broker_messages.threads_galileo(
                    galileo_latitude = [self.galileo_marker.P1[i][0] for i in range(len(self.galileo_marker.P1))], 
                    galileo_longitude = [self.galileo_marker.P1[i][1] for i in range(len(self.galileo_marker.P1))], 
                    galileo_heading = [self.galileo_marker.heading[i] for i in range(len(self.galileo_marker.heading))],
                    galileo_timediff=float(self.time_galileo.get()),
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get()) 
                broker_messages.send_messages_with_progress(messages = [vis, gali], progress_button = self.progress_button, windowclass = self)                 
                break

            elif (self.var1.get() == 1) & (self.var2.get() == 0) & (self.var3.get() == 1) & (self.var4.get() == 1):
                print("visual")
                vis = broker_messages.threads_visual(
                    visual_latitude = [self.visual_marker.P1[i][0] for i in range(len(self.visual_marker.P1))], 
                    visual_longitude = [self.visual_marker.P1[i][1] for i in range(len(self.visual_marker.P1))], 
                    visual_heading = [self.visual_marker.heading[i] for i in range(len(self.visual_marker.heading))],
                    visual_timediff= float(self.time_visual.get()), 
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get())                
                print("galileo")
                gali = broker_messages.threads_galileo(
                    galileo_latitude = [self.galileo_marker.P1[i][0] for i in range(len(self.galileo_marker.P1))], 
                    galileo_longitude = [self.galileo_marker.P1[i][1] for i in range(len(self.galileo_marker.P1))], 
                    galileo_heading = [self.galileo_marker.heading[i] for i in range(len(self.galileo_marker.heading))],
                    galileo_timediff=float(self.time_galileo.get()),
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get()) 
                print("fusion")
                fus = broker_messages.threads_fusion(
                    fusion_latitude = [self.fusion_marker.P1[i][0] for i in range(len(self.fusion_marker.P1))], 
                    fusion_longitude = [self.fusion_marker.P1[i][1] for i in range(len(self.fusion_marker.P1))], 
                    fusion_heading = [self.fusion_marker.heading[i] for i in range(len(self.fusion_marker.heading))],
                    fusion_timediff=float(self.time_fusion.get()),
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get())
                broker_messages.send_messages_with_progress(messages = [vis, gali, fus], progress_button = self.progress_button, windowclass = self)                 
                break

            elif (self.var1.get() == 0) & (self.var2.get() == 1) & (self.var3.get() == 1) & (self.var4.get() == 0):
                print("inertio")
                iner = broker_messages.threads_inertio(
                    inertio_latitude = [self.inertio_marker.P1[i][0] for i in range(len(self.inertio_marker.P1))], 
                    inertio_longitude = [self.inertio_marker.P1[i][1] for i in range(len(self.inertio_marker.P1))], 
                    inertio_heading = [self.inertio_marker.heading[i] for i in range(len(self.inertio_marker.heading))],
                    inertio_timediff=float(self.time_inertio.get()),
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get())           
                print("galileo")
                gali = broker_messages.threads_galileo(
                    galileo_latitude = [self.galileo_marker.P1[i][0] for i in range(len(self.galileo_marker.P1))], 
                    galileo_longitude = [self.galileo_marker.P1[i][1] for i in range(len(self.galileo_marker.P1))], 
                    galileo_heading = [self.galileo_marker.heading[i] for i in range(len(self.galileo_marker.heading))],
                    galileo_timediff=float(self.time_galileo.get()),
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get()) 
                broker_messages.send_messages_with_progress(messages = [iner, gali], progress_button = self.progress_button, windowclass = self)                
                break 

            elif (self.var1.get() == 0) & (self.var2.get() == 1) & (self.var3.get() == 1) & (self.var4.get() == 1):
                print("inertio")
                iner = broker_messages.threads_inertio(
                    inertio_latitude = [self.inertio_marker.P1[i][0] for i in range(len(self.inertio_marker.P1))], 
                    inertio_longitude = [self.inertio_marker.P1[i][1] for i in range(len(self.inertio_marker.P1))], 
                    inertio_heading = [self.inertio_marker.heading[i] for i in range(len(self.inertio_marker.heading))],
                    inertio_timediff=float(self.time_inertio.get()),
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get())           
                print("galileo")
                gali = broker_messages.threads_galileo(
                    galileo_latitude = [self.galileo_marker.P1[i][0] for i in range(len(self.galileo_marker.P1))], 
                    galileo_longitude = [self.galileo_marker.P1[i][1] for i in range(len(self.galileo_marker.P1))], 
                    galileo_heading = [self.galileo_marker.heading[i] for i in range(len(self.galileo_marker.heading))],
                    galileo_timediff=float(self.time_galileo.get()),
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get()) 
                print("fusion")
                fus = broker_messages.threads_fusion(
                    fusion_latitude = [self.fusion_marker.P1[i][0] for i in range(len(self.fusion_marker.P1))], 
                    fusion_longitude = [self.fusion_marker.P1[i][1] for i in range(len(self.fusion_marker.P1))], 
                    fusion_heading = [self.fusion_marker.heading[i] for i in range(len(self.fusion_marker.heading))],
                    fusion_timediff=float(self.time_fusion.get()),
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get())
                broker_messages.send_messages_with_progress(messages = [iner, gali, fus], progress_button = self.progress_button, windowclass = self)                
                break              

            elif (self.var1.get() == 1) & (self.var2.get() == 0) & (self.var3.get() == 0) & (self.var4.get() == 0):
                print("visual")
                vis = broker_messages.threads_visual(
                    visual_latitude = [self.visual_marker.P1[i][0] for i in range(len(self.visual_marker.P1))], 
                    visual_longitude = [self.visual_marker.P1[i][1] for i in range(len(self.visual_marker.P1))], 
                    visual_heading = [self.visual_marker.heading[i] for i in range(len(self.visual_marker.heading))],
                    visual_timediff= float(self.time_visual.get()), 
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get())
                broker_messages.send_messages_with_progress(messages = [vis], progress_button = self.progress_button, windowclass = self)              
                break

            elif (self.var1.get() == 1) & (self.var2.get() == 0) & (self.var3.get() == 0) & (self.var4.get() == 1):
                print("visual")
                vis = broker_messages.threads_visual(
                    visual_latitude = [self.visual_marker.P1[i][0] for i in range(len(self.visual_marker.P1))], 
                    visual_longitude = [self.visual_marker.P1[i][1] for i in range(len(self.visual_marker.P1))], 
                    visual_heading = [self.visual_marker.heading[i] for i in range(len(self.visual_marker.heading))],
                    visual_timediff= float(self.time_visual.get()), 
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get())
                print("fusion")
                fus = broker_messages.threads_fusion(
                    fusion_latitude = [self.fusion_marker.P1[i][0] for i in range(len(self.fusion_marker.P1))], 
                    fusion_longitude = [self.fusion_marker.P1[i][1] for i in range(len(self.fusion_marker.P1))], 
                    fusion_heading = [self.fusion_marker.heading[i] for i in range(len(self.fusion_marker.heading))],
                    fusion_timediff=float(self.time_fusion.get()),
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get())
                broker_messages.send_messages_with_progress(messages = [vis, fus], progress_button = self.progress_button, windowclass = self)              
                break

            elif (self.var1.get() == 0) & (self.var2.get() == 1) & (self.var3.get() == 0) & (self.var4.get() == 0):
                print("inertio")
                iner = broker_messages.threads_inertio(
                    inertio_latitude = [self.inertio_marker.P1[i][0] for i in range(len(self.inertio_marker.P1))], 
                    inertio_longitude = [self.inertio_marker.P1[i][1] for i in range(len(self.inertio_marker.P1))], 
                    inertio_heading = [self.inertio_marker.heading[i] for i in range(len(self.inertio_marker.heading))],
                    inertio_timediff=float(self.time_inertio.get()),
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get()) 
                broker_messages.send_messages_with_progress(messages = [iner], progress_button = self.progress_button, windowclass = self)               
                break

            elif (self.var1.get() == 0) & (self.var2.get() == 1) & (self.var3.get() == 0) & (self.var4.get() == 1):
                print("inertio")
                iner = broker_messages.threads_inertio(
                    inertio_latitude = [self.inertio_marker.P1[i][0] for i in range(len(self.inertio_marker.P1))], 
                    inertio_longitude = [self.inertio_marker.P1[i][1] for i in range(len(self.inertio_marker.P1))], 
                    inertio_heading = [self.inertio_marker.heading[i] for i in range(len(self.inertio_marker.heading))],
                    inertio_timediff=float(self.time_inertio.get()),
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get()) 
                print("fusion")
                fus = broker_messages.threads_fusion(
                    fusion_latitude = [self.fusion_marker.P1[i][0] for i in range(len(self.fusion_marker.P1))], 
                    fusion_longitude = [self.fusion_marker.P1[i][1] for i in range(len(self.fusion_marker.P1))], 
                    fusion_heading = [self.fusion_marker.heading[i] for i in range(len(self.fusion_marker.heading))],
                    fusion_timediff=float(self.time_fusion.get()),
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get())
                broker_messages.send_messages_with_progress(messages = [iner, fus], progress_button = self.progress_button, windowclass = self)               
                break

            elif (self.var1.get() == 0) & (self.var2.get() == 0) & (self.var3.get() == 1) & (self.var4.get() == 0):
                print("galileo")
                gali = broker_messages.threads_galileo(
                    galileo_latitude = [self.galileo_marker.P1[i][0] for i in range(len(self.galileo_marker.P1))], 
                    galileo_longitude = [self.galileo_marker.P1[i][1] for i in range(len(self.galileo_marker.P1))], 
                    galileo_heading = [self.galileo_marker.heading[i] for i in range(len(self.galileo_marker.heading))],
                    galileo_timediff=float(self.time_galileo.get()),
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get()) 
                broker_messages.send_messages_with_progress(messages = [gali], progress_button = self.progress_button, windowclass = self)            
                break

            elif (self.var1.get() == 0) & (self.var2.get() == 0) & (self.var3.get() == 1) & (self.var4.get() == 1):
                print("galileo")
                gali = broker_messages.threads_galileo(
                    galileo_latitude = [self.galileo_marker.P1[i][0] for i in range(len(self.galileo_marker.P1))], 
                    galileo_longitude = [self.galileo_marker.P1[i][1] for i in range(len(self.galileo_marker.P1))], 
                    galileo_heading = [self.galileo_marker.heading[i] for i in range(len(self.galileo_marker.heading))],
                    galileo_timediff=float(self.time_galileo.get()),
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get()) 
                print("fusion")
                fus = broker_messages.threads_fusion(
                    fusion_latitude = [self.fusion_marker.P1[i][0] for i in range(len(self.fusion_marker.P1))], 
                    fusion_longitude = [self.fusion_marker.P1[i][1] for i in range(len(self.fusion_marker.P1))], 
                    fusion_heading = [self.fusion_marker.heading[i] for i in range(len(self.fusion_marker.heading))],
                    fusion_timediff=float(self.time_fusion.get()),
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get())                
                broker_messages.send_messages_with_progress(messages = [gali, fus], progress_button = self.progress_button, windowclass = self)            
                break

            elif (self.var1.get() == 0) & (self.var2.get() == 0) & (self.var3.get() == 0) & (self.var4.get() == 1):            
                print("fusion")
                fus = broker_messages.threads_fusion(
                    fusion_latitude = [self.fusion_marker.P1[i][0] for i in range(len(self.fusion_marker.P1))], 
                    fusion_longitude = [self.fusion_marker.P1[i][1] for i in range(len(self.fusion_marker.P1))], 
                    fusion_heading = [self.fusion_marker.heading[i] for i in range(len(self.fusion_marker.heading))],
                    fusion_timediff=float(self.time_fusion.get()),
                    brokerip = self.broker_button.get(), 
                    sourceid=self.source_id_button.get())                
                broker_messages.send_messages_with_progress(messages = [fus], progress_button = self.progress_button, windowclass = self)        
                break
        self.send.configure(state = "normal")

    def on_closing(self, event=0):
        self.destroy()
    

    def start(self):
        #self.wait_click()
        self.mainloop()
    
    def hi(self):
        pass

    def save_message(self):
        #Remove the existing folders
        if os.path.exists("visual"):
            shutil.rmtree("visual")
        if os.path.exists("inertio"):
            shutil.rmtree("inertio")
        if os.path.exists("galileo"):
            shutil.rmtree("galileo")
        if os.path.exists("fusion"):
            shutil.rmtree("fusion")     
        #Create new ones
        folder = filedialog.askdirectory(initialdir=os.getcwd() ,title='Select folder to save results')
        print(folder)
        if self.var1.get() == 1:
            os.makedirs("{}/visual".format(folder))
            with open("{}/visual/vis_data.txt".format(folder), 'w') as file:
                file.write(str(self.visual_marker.P1) + 
                           "\n" + str(self.visual_marker.heading) + 
                           "\n" + str(float(self.time_visual.get())) +
                           "\n" + str(float(self.speed.get())) +
                           "\n" + str(self.switch_visual.get()) +
                           "\n" + (' ' if self.visual_std.get()=='' else str(float(self.visual_std.get()))) +
                           "\n" + str([ast.literal_eval(self.markers[i].text) for i in range(len(self.markers))]))
        if self.var2.get() == 1:
            os.makedirs("{}/inertio".format(folder))
            with open("{}/inertio/iner_data.txt".format(folder), 'w') as file:
                file.write(str(self.inertio_marker.P1) + 
                           "\n" + str(self.inertio_marker.heading) + 
                           "\n" + str(float(self.time_inertio.get())) +
                           "\n" + str(float(self.speed.get())) +
                           "\n" + str(self.switch_inertio.get()) +
                           "\n" + (' ' if self.inertio_std.get()=='' else str(float(self.inertio_std.get())))+
                           "\n" + str([ast.literal_eval(self.markers[i].text) for i in range(len(self.markers))]))
        if self.var3.get() == 1:
            os.makedirs("{}/galileo".format(folder))
            with open("{}/galileo/gali_data.txt".format(folder), 'w') as file:
                file.write(str(self.galileo_marker.P1) + 
                           "\n" + str(self.galileo_marker.heading) + 
                           "\n" + str(float(self.time_galileo.get())) +
                           "\n" + str(float(self.speed.get())) +
                           "\n" + str(self.switch_galileo.get()) +
                           "\n" + (' ' if self.galileo_std.get()=='' else str(float(self.galileo_std.get())))+
                           "\n" + str([ast.literal_eval(self.markers[i].text) for i in range(len(self.markers))]))
        if self.var4.get() == 1:
            os.makedirs("{}/fusion".format(folder))
            with open("{}/fusion/fus_data.txt".format(folder), 'w') as file:
                file.write(str(self.fusion_marker.P1) + 
                           "\n" + str(self.fusion_marker.heading) + 
                           "\n" + str(float(self.time_fusion.get())) +
                           "\n" + str(float(self.speed.get())) +
                           "\n" + str(self.switch_fusion.get()) +
                           "\n" + (' ' if self.fusion_std.get()=='' else str(float(self.fusion_std.get())))+
                           "\n" + str([ast.literal_eval(self.markers[i].text) for i in range(len(self.markers))]))

    def load_message(self):
        self.var1.set(0)
        self.var2.set(0)
        self.var3.set(0)
        self.var4.set(0)
        self.speed.delete(0, tkinter.END)
        self.time_visual.delete(0, tkinter.END)
        self.time_inertio.delete(0, tkinter.END)
        self.time_galileo.delete(0, tkinter.END)
        self.time_fusion.delete(0, tkinter.END)
        self.visual_std.delete(0, tkinter.END)
        self.inertio_std.delete(0, tkinter.END)
        self.galileo_std.delete(0, tkinter.END)
        self.fusion_std.delete(0, tkinter.END)
        broker_messages = messages(brokerip = self.broker_button.get(), sourceid=self.source_id_button.get(), dateandtime=datetime.utcnow())
        filename = filedialog.askdirectory(initialdir=os.getcwd())
        print(filename)
        if os.path.exists("{}/visual".format(filename)):
            self.var1.set(1)
            with open("{}/visual/vis_data.txt".format(filename), "r") as f:    lines = [ line.rstrip() for line in f ]
            self.visual_marker.P1 = ast.literal_eval(lines[0])
            self.visual_marker.heading = json.loads(lines[1])
            self.time_visual.insert(0,lines[2])
            if self.speed.get()=='': self.speed.insert(0,lines[3]) 
            self.switch_visual.set(lines[4])
            self.visual_std.insert(0, "") if lines[5].strip() == ' ' else self.visual_std.insert(0, lines[5])
            pin = ast.literal_eval(lines[6])
            for i in range(len(pin)):
                self.map_widget.set_marker(pin[i][0], pin[i][1], text = "("+ str(pin[i][0]) +","+ str(pin[i][1])+")", font = "Tahoma 9", text_color = '#e61212')

        if os.path.exists("{}/inertio".format(filename)):
            self.var2.set(1)
            with open("{}/inertio/iner_data.txt".format(filename), 'r') as f:    lines = [ line.strip() for line in f ]
            self.inertio_marker.P1 = ast.literal_eval(lines[0])
            self.inertio_marker.heading = json.loads(lines[1])
            self.time_inertio.insert(0,lines[2])
            if self.speed.get()=='': self.speed.insert(0,lines[3]) 
            self.switch_inertio.set(lines[4])
            self.inertio_std.insert(0, "") if lines[5].strip() == ' ' else self.inertio_std.insert(0, lines[5])
            pin = ast.literal_eval(lines[6])
            for i in range(len(pin)):
                self.map_widget.set_marker(pin[i][0], pin[i][1], text = "("+ str(pin[i][0]) +","+ str(pin[i][1])+")", font = "Tahoma 9", text_color = '#e61212')


        if os.path.exists("{}/galileo".format(filename)):
            self.var3.set(1)
            with open("{}/galileo/gali_data.txt".format(filename), 'r') as f:    lines = [ line.strip() for line in f ]
            self.galileo_marker.P1 = ast.literal_eval(lines[0])
            self.galileo_marker.heading = json.loads(lines[1])
            self.time_galileo.insert(0,lines[2])
            if self.speed.get()=='': self.speed.insert(0,lines[3]) 
            self.switch_galileo.set(lines[4])
            self.galileo_std.insert(0, "") if lines[5].strip() == ' ' else self.galileo_std.insert(0, lines[5])
            pin = ast.literal_eval(lines[6])
            for i in range(len(pin)):
                self.map_widget.set_marker(pin[i][0], pin[i][1], text = "("+ str(pin[i][0]) +","+ str(pin[i][1])+")", font = "Tahoma 9", text_color = '#e61212') 

        if os.path.exists("{}/fusion".format(filename)):
            self.var4.set(1)
            with open("{}/fusion/fus_data.txt".format(filename), 'r') as f:    lines = [ line.strip() for line in f ]
            self.fusion_marker.P1 = ast.literal_eval(lines[0])
            self.fusion_marker.heading = json.loads(lines[1])
            self.time_fusion.insert(0,lines[2])
            if self.speed.get()=='': self.speed.insert(0,lines[3]) 
            self.switch_fusion.set(lines[4])
            self.fusion_std.insert(0, "") if lines[5].strip() == ' ' else self.fusion_std.insert(0, lines[5])
            pin = ast.literal_eval(lines[6])
            for i in range(len(pin)):
                self.map_widget.set_marker(pin[i][0], pin[i][1], text = "("+ str(pin[i][0]) +","+ str(pin[i][1])+")", font = "Tahoma 9", text_color = '#e61212')


if __name__ == "__main__":
    app = App()
    app.start()

