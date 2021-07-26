# packages for accessing and processing seismic data
from obspy.clients.fdsn import Client

import folium # make maps
from matplotlib import pyplot as plt # plotting
import numpy as np # facilitated math

class StationData: 
    def __init__(self, station_list, network, station, start_time, end_time): 
        self.network_code = network
        self.station_code = station
        self.P_arrival_time = None
        self.S_arrival_time = None
        self.epicenter_distance = None

        # get network and station objects
        network = next(network for network in station_list if network.code == self.network_code)
        station = next(station for station in network if station.code == self.station_code)

        self.latitude = station.latitude
        self.longitude = station.longitude

        # set the data source 
        client = Client("IRIS")
        waveform_data = [] # initialize an empty list to hold data

        # vertical component
        try: 
          waveform_data.append(client.get_waveforms(self.network_code, self.station_code, "*", "HHZ", start_time, end_time)[0])
        except: 
          waveform_data.append(client.get_waveforms(self.network_code, self.station_code, "*", "HH3", start_time, end_time)[0])

        # horizontal E-W component
        try: 
          waveform_data.append(client.get_waveforms(self.network_code, self.station_code, "*", "HHE", start_time, end_time)[0])
        except: 
          waveform_data.append(client.get_waveforms(self.network_code, self.station_code, "*", "HH1", start_time, end_time)[0])
        
        # horizontal N-S component
        try: 
          waveform_data.append(client.get_waveforms(self.network_code, self.station_code, "*", "HHN", start_time, end_time)[0])
        except: 
          waveform_data.append(client.get_waveforms(self.network_code, self.station_code, "*", "HH2", start_time, end_time)[0])
        

        # filter the data
        for i in range(len(waveform_data)): # loop through the three components
          waveform_data[i] = waveform_data[i].filter('lowpass', freq=1.0, corners=2, zerophase=True)

        self.data = waveform_data

    def plot(self):

        # create plot
        fig, axs = plt.subplots(nrows=3, ncols=1, figsize=(16, 6), sharex=True)

        # plot each component
        for i in range(len(axs)):
          # define array for x-axis of plot
          t = np.arange(0, self.data[i].stats.npts / self.data[i].stats.sampling_rate, self.data[i].stats.delta)

          axs[i].plot(t, self.data[i].data, 'k')
          if self.P_arrival_time:
              axs[i].axvline(self.P_arrival_time, color='b')
          if self.S_arrival_time: 
              axs[i].axvline(self.S_arrival_time, color='r')

        axs[i].set_xlabel('Time (s)')
        axs[i].xaxis.set_major_locator(plt.MultipleLocator(50))
        axs[i].xaxis.set_minor_locator(plt.MultipleLocator(10))

        # display the plot
        plt.show()

    def addToMap(self, map): 
        # add circle whose circumference indicates possible epicenter locations
        folium.Circle(
            location=[self.latitude, self.longitude], # set marker position
            icon=folium.Icon(), 
            radius = self.epicenter_distance * 1e3 # [m]
        ).add_to(map)

def getStations(latitude_range, longitude_range, start_time, end_time): 
    # set the data source 
    client = Client("IRIS")

    # enact the above constraints (and a few others) and get the available stations
    inventory = client.get_stations(minlatitude=latitude_range[0], 
                                    maxlatitude=latitude_range[1],
                                    minlongitude=longitude_range[0],
                                    maxlongitude=longitude_range[1],
                                    starttime=start_time,
                                    endtime=end_time,
                                    channel="HHZ,HHN,HHE",
                                    level="channel",
                                    includeavailability=True,
                                    includerestricted=False,
                                    matchtimeseries=True)  
    return inventory

def createMapWithStations(station_list): 
    # create map 
    station_map = folium.Map(location=[13.3333, -61.1833]) # center on La Soufriere

    # add red marker for La Soufriere 
    folium.Marker( 
                location=[13.3333, -61.1833], # set marker position
                popup="La Soufriere", # create label for the marker
                icon=folium.Icon(color="red")
            ).add_to(station_map);

    # add seismic stations
    for network in station_list: # loop through networks
        for station in network:  # loop throug stations in network
            folium.Marker(
                location=[station.latitude, station.longitude], # set marker position
                popup=f"network: {network.code} \n station: {station.code}", # create label for the marker
                icon=folium.Icon()
            ).add_to(station_map)

    return station_map