from tkinter import *
from tkinter import ttk
import customtkinter


class app:
    def __init__(self, master):
        self.master = master
        self.master.geometry("900x500")
        self.master.resizable(False, False)
        self.master.title("HOSA Canada Marking Software")
        self.home()

    def generalFrame(self):
        self.frame1 = customtkinter.CTkFrame(master = self.master, width= 880, height= 480, corner_radius= 5, fg_color="#404258", )
        self.frame1.place(x = 10, y = 10)
        self.soilCollectionControls = customtkinter.CTkFrame(master = self.frame1, width= 200, height= 390, corner_radius= 5, fg_color="#474E68", )
        self.soilCollectionControls.place(x = 15, y = 80)
        self.weatherStationContols = customtkinter.CTkFrame(master = self.frame1, width= 200, height= 390, corner_radius= 5, fg_color="#474E68", )
        self.weatherStationContols.place(x = 230, y = 80)
        self.vacuumTubeControls = customtkinter.CTkFrame(master = self.frame1, width= 200, height= 390, corner_radius= 5, fg_color="#474E68", )
        self.vacuumTubeControls.place(x = 445, y = 80)
        self.soilTestingControls = customtkinter.CTkFrame(master = self.frame1, width= 200, height= 390, corner_radius= 5, fg_color="#474E68", )
        self.soilTestingControls.place(x = 660, y = 80)
        #self.logo = customtkinter.CTkImage(light_image=Image.open("images/logo.png"), size=(160, 160 * 0.37))
        #self.logoLabel = customtkinter.CTkLabel(master= self.frame1, image=self.logo, text='')
        #self.logoLabel.place(x = 20, y = 10)
        self.title = customtkinter.CTkTextbox(master = self.frame1, width= 250, height= 60, font= ("CTkFont", 40, 'bold'), fg_color= "#474E68")
        self.title.place(x = 20, y = 7)
        self.title.insert("0.0", "LD Controls")
        self.event = customtkinter.CTkTextbox(master = self.frame1, width= 70, height= 20, font= ("CTkFont", 20, 'bold'), fg_color= "#474E68")
        self.event.place(x = 760, y = 10)
        self.event.insert("0.0", "Temp")
        self.event.configure(state = DISABLED)
        self.title.configure(state = DISABLED)

    def home(self):
        for i in self.master.winfo_children():
            i.destroy()
        self.generalFrame()
        controls = []
        self.soilCollectionControlsTitle = customtkinter.CTkTextbox(master = self.soilCollectionControls, width= 180, height= 20, font= ("CTkFont", 20, 'bold'), fg_color= "#474E68")
        self.soilCollectionControlsTitle.place(x = 10, y = 7)
        self.soilCollectionControlsTitle.insert("0.0", "Soil Collection")
        self.soilCollectionControlsTitle.configure(state = DISABLED)
        self.vacuumTubeControlsTitle = customtkinter.CTkTextbox(master = self.vacuumTubeControls, width= 180, height= 20, font= ("CTkFont", 20, 'bold'), fg_color= "#474E68")
        self.vacuumTubeControlsTitle.place(x = 10, y = 7)
        self.vacuumTubeControlsTitle.insert("0.0", "Vacuum Tube")
        self.vacuumTubeControlsTitle.configure(state = DISABLED)
        self.soilTestingControlsTitle = customtkinter.CTkTextbox(master = self.soilTestingControls, width= 180, height= 20, font= ("CTkFont", 20, 'bold'), fg_color= "#474E68")
        self.soilTestingControlsTitle.place(x = 10, y = 7)
        self.soilTestingControlsTitle.insert("0.0", "Soil Testing")
        self.soilTestingControlsTitle.configure(state = DISABLED)
        self.weatherStationContolsTitle = customtkinter.CTkTextbox(master = self.weatherStationContols, width= 180, height= 20, font= ("CTkFont", 20, 'bold'), fg_color= "#474E68")
        self.weatherStationContolsTitle.place(x = 10, y = 7)
        self.weatherStationContolsTitle.insert("0.0", "Weather Station")
        self.weatherStationContolsTitle.configure(state = DISABLED)

        self.soilCollectionButton = customtkinter.CTkButton(master = self.soilCollectionControls, width = 180, height = 50, fg_color="#50577A", font= ("CTkFont", 20), text="Collect Cache")
        self.soilCollectionButton.place(x = 10, y = 60)
        self.soilDataButton = customtkinter.CTkButton(master = self.soilCollectionControls, width = 180, height = 50, fg_color="#50577A", font= ("CTkFont", 20), text="Soil Data")
        self.soilDataButton.place(x = 10, y = 120)

        self.soilDataMoistureTitle = customtkinter.CTkTextbox(master = self.soilCollectionControls, width = 180, height = 50, font= ("CTkFont", 20), fg_color= "#474E68")
        self.soilDataMoistureTitle.insert("0.0", "Moisture:")
        self.soilDataMoistureTitle.place(x = 10, y = 180)
        self.soilDataMoisture = customtkinter.CTkTextbox(master = self.soilCollectionControls, width = 180, height = 50, font= ("CTkFont", 20), fg_color="#50577A")
        self.soilDataMoisture.place(x = 10, y = 220)
        self.soilDataTemperatureTitle = customtkinter.CTkTextbox(master = self.soilCollectionControls, width = 180, height = 50, font= ("CTkFont", 20), fg_color= "#474E68")
        self.soilDataTemperatureTitle.insert("0.0", "Temperature:")
        self.soilDataTemperatureTitle.place(x = 10, y = 280)
        self.soilDataTemperature = customtkinter.CTkTextbox(master = self.soilCollectionControls, width = 180, height = 50, font= ("CTkFont", 20), fg_color="#50577A")
        self.soilDataTemperature.place(x = 10, y = 320)

        self.weatherDataButton = customtkinter.CTkButton(master = self.weatherStationContols, width = 180, height = 50, fg_color="#50577A", font= ("CTkFont", 20), text="Weather Data")
        self.weatherDataButton.place(x = 10, y = 60)

        self.weatherTemperatureTitle = customtkinter.CTkTextbox(master = self.weatherStationContols, width = 180, height = 50, font= ("CTkFont", 15), fg_color= "#474E68")
        self.weatherTemperatureTitle.insert("0.0", "Temperature:")
        self.weatherTemperatureTitle.place(x = 10, y = 110)
        self.weatherTemperature = customtkinter.CTkTextbox(master = self.weatherStationContols, width = 180, height = 30, font= ("CTkFont", 15), fg_color="#50577A")
        self.weatherTemperature.place(x = 10, y = 140)

        self.weatherHumidityTitle = customtkinter.CTkTextbox(master = self.weatherStationContols, width = 180, height = 30, font= ("CTkFont", 15), fg_color= "#474E68")
        self.weatherHumidityTitle.insert("0.0", "Humidity:")
        self.weatherHumidityTitle.place(x = 10, y = 170)
        self.weatherHumidity = customtkinter.CTkTextbox(master = self.weatherStationContols, width = 180, height = 30, font= ("CTkFont", 15), fg_color="#50577A")
        self.weatherHumidity.place(x = 10, y = 200)

        self.weatherVisLightTitle = customtkinter.CTkTextbox(master = self.weatherStationContols, width = 180, height = 50, font= ("CTkFont", 15), fg_color= "#474E68")
        self.weatherVisLightTitle.insert("0.0", "Visible Light:")
        self.weatherVisLightTitle.place(x = 10, y = 230)
        self.weatherVisLight = customtkinter.CTkTextbox(master = self.weatherStationContols, width = 180, height = 30, font= ("CTkFont", 15), fg_color="#50577A")
        self.weatherVisLight.place(x = 10, y = 260)

        self.weatherUVLightTitle = customtkinter.CTkTextbox(master = self.weatherStationContols, width = 180, height = 30, font= ("CTkFont", 15), fg_color= "#474E68")
        self.weatherUVLightTitle.insert("0.0", "UV Light:")
        self.weatherUVLightTitle.place(x = 10, y = 290)
        self.weatherUVLight = customtkinter.CTkTextbox(master = self.weatherStationContols, width = 180, height = 30, font= ("CTkFont", 15), fg_color="#50577A")
        self.weatherUVLight.place(x = 10, y = 320)

        self.VacuumUpButton = customtkinter.CTkButton(master = self.vacuumTubeControls, width = 180, height = 50, fg_color="#50577A", font= ("CTkFont", 20), text="Move Up")
        self.VacuumUpButton.place(x = 10, y = 60)
        self.VacuumDownButton = customtkinter.CTkButton(master = self.vacuumTubeControls, width = 180, height = 50, fg_color="#50577A", font= ("CTkFont", 20), text="Move Down")
        self.VacuumDownButton.place(x = 10, y = 120)
        self.VacuumStartButton = customtkinter.CTkButton(master = self.vacuumTubeControls, width = 180, height = 50, fg_color="#50577A", font= ("CTkFont", 20), text="Toggle On/Off")
        self.VacuumStartButton.place(x = 10, y = 180)
root = customtkinter.CTk()
app(root)
root.mainloop()