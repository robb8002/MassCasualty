#IMPORTS
import math
import numpy
from numpy import random
from numpy import mean
import scipy
from scipy import stats
from scipy.stats import lognorm
import pandas
import simpy

#Class representing...
#VARIABLES AND PARAMETERS
#Global variables and a parameters are tweaked here.
class VariablesAndParameters:
    #Sim Details
    warm_up = 3
    number_of_runs = 10
    run_number = 0
    duration_of_simulation_in_minutes = 500
    simulation_time = (duration_of_simulation_in_minutes * 60)
    #SIMULATION TIME IS IN SECONDS

    #People Involved
    #We are calculating how many Marines we can handle before resources are swamped or strained. Therefore, marine_counter starts and stays at 0.
    marine_counter = 0
    number_of_water_pickup_triage_personnel = 10
    number_of_red_dedicated_doctors = 281
    number_of_yellow_dedicated_doctors = 260
    number_of_green_dedicated_corpsmen = 239
    number_of_black_dedicated_corpsmen = 239

    #Location Occupancy
    main_bds_maximum_occupancy = 92
    holding_area_maximum_occupancy = 280
    auxillary_treatment_area_maximum_occupancy = 370
    other_location_maximum_occupancy = 270

    #How Long It Takes To Do Things
    #Gonna want to mess around with a lognormal calculator and see what some acceptable samples could be.
    interarrival_mean = 1
    water_pickup_triage_mean_time = 1.2
    water_pickup_triage_stdev_time = 1
    red_mean_doctor_main_bds_consultation = 4
    red_stdev_doctor_main_bds_consultation = 1
    yellow_mean_doctor_holding_area_consultation = 3
    yellow_stdev_doctor_holding_area_consultation = 1
    green_mean_corpsman_auxillary_treatment_area_consultation = 2
    green_stdev_corpsman_auxillary_treatment_area_consultation = 1
    black_mean_corpsman_other_location_consultation = 2
    black_stdev_corpsman_other_location_consultation = 1

    #INSIGHTS
    #How Long It Takes From Water to Color-Coded Area
    wait_time_of_inital_triage_water_pickup = []
    red_wait_time_between_triage_to_main_bds = []
    yellow_wait_time_between_triage_to_holding_area = []
    green_wait_time_between_triage_to_auxillary_treatment_area = []
    black_wait_time_between_triage_to_other_location = []

    #How Long It Takes Once In Color-Coded To Get A Provider
    red_wait_for_doctor_main_bds = []
    yellow_wait_for_doctor_holding_area = []
    green_wait_for_corpsman_auxillary_treatment_area = []
    black_wait_for_corpsman_other_location = []

    #How Long It Takes In Color-Coded Area For Care
    red_time_in_main_bds = []
    yellow_time_in_holding_area = []
    green_time_in_aux_treatment_area = []
    black_time_in_other_location = []

#Class representing...
#A MARINE
class InstanceOfMarine:
    #ID and Time In System
    def __init__(self):
        self.time_in_system_start = 0
        self.id = VariablesAndParameters.marine_counter
        #DEBUGGING
        print("ID: ", self.id)
        print("Start Time In System: ", self.time_in_system_start)

        #Give Them Priority Number and Color
        self.set_priority()
        self.set_triage_color()

        VariablesAndParameters.marine_counter += 1

        #DEBUGGING
        print("Marine Counter: ", VariablesAndParameters.marine_counter)

    #Priority Number To Correspond With Color
    def set_priority(self):
        self.set_priority_number = numpy.random.choice([1, 2, 3, 4])

        #DEBUGGING
        print("Priority Number: ", self.set_priority_number)

    #Priority Color That Corresponds To Priority Number
    def set_triage_color(self):
        if self.set_priority_number == 1:
            self.triage_color = "Red"
            #Add To Data
            if VariablesAndParameters.run_number > VariablesAndParameters.warm_up:
                Track.individual_marines_priority_count_dictionary["Priority 1: Red"].append(self.id)
            
        if self.set_priority_number == 2:
            self.triage_color = "Yellow"
            #Add To Data
            if VariablesAndParameters.run_number > VariablesAndParameters.warm_up:
                Track.individual_marines_priority_count_dictionary["Priority 2: Yellow"].append(self.id)
            
        if self.set_priority_number == 3:
            self.triage_color = "Green"
            #Add To Data
            if VariablesAndParameters.run_number > VariablesAndParameters.warm_up:
                Track.individual_marines_priority_count_dictionary["Priority 3: Green"].append(self.id)
            
        if self.set_priority_number == 4:
            self.triage_color = "Black"
            #Add To Data
            if VariablesAndParameters.run_number > VariablesAndParameters.warm_up:
                Track.individual_marines_priority_count_dictionary["Priority 4: Black"].append(self.id)
                
        #DEBUGGING
        print("Triage Color: ", self.triage_color)


#Class representing...
#DATA
#Where we put data as the simulation runs.
class Track:

    #Store Individual IDs of Marines With Each Priority
    #Used during execution for storage of priorities as they are assigned.
    individual_marines_priority_count_dictionary = {
        "Priority 1: Red": [],
        "Priority 2: Yellow": [],
        "Priority 3: Green": [],
        "Priority 4: Black": []
    }

    #Store Number of Each Priority
    #Used at the end to hold calculated values.
    total_priority_count_dictionary = {
        "Priority 1: Red": [],
        "Priority 2: Yellow": [],
        "Priority 3: Green": [],
        "Priority 4: Black": []

    }

    #Store Individual Times at Location in a List
    #Used during execution to store times of Marines at locations as they go through the system.
    individual_times_at_locations_dictionary = {
        "Initial Triage/Water Pickup": [],
        "Main Battle Dressing Station": [],
        "Holding Area": [],
        "Auxillary Treatment Area": [],
        "Other Location": [],
        "Waiting For Red Doctor": [],
        "Waiting For Yellow Doctor": [],
        "Waiting for Green Corpsman": [],
        "Waiting for Black Corpsman": [],
        "With Red Dedicated Doctor": [],
        "With Yellow Dedicated Doctor": [],
        "With Green Dedicated Corpsman": [],
        "With Black Dedicated Corpsman": []
    }

    #Store Average Time At Locations
    #Used at the end for calculations.
    average_times_at_locations_dictionary = {
        "Initial Triage/Water Pickup": [],
        "Main Battle Dressing Station": [],
        "Holding Area": [],
        "Auxillary Treatment Area": [],
        "Other Location": [],
        "Waiting For Red Doctor": [],
        "Waiting For Yellow Doctor": [],
        "Waiting for Green Corpsman": [],
        "Waiting for Black Corpsman": [],
        "With Red Dedicated Doctor": [],
        "With Yellow Dedicated Doctor": [],
        "With Green Dedicated Corpsman": [],
        "With Black Dedicated Corpsman": []
    }

#Class representing...
#MASS CASUALTY TRIAGE
#How things are actually being gonkulated.
class MassCasualtySystem:
    #Setup The Simulation Environment

    def __init__(self):
        self.env = simpy.Environment()
        #Define Our Simulation Resources
        #People
        self.initial_triage_resource_definition = simpy.PriorityResource(self.env, capacity = VariablesAndParameters.number_of_water_pickup_triage_personnel)
        self.red_doctor_resource_definition = simpy.PriorityResource(self.env, capacity = VariablesAndParameters.number_of_red_dedicated_doctors)
        self.yellow_doctor_resource_definition = simpy.PriorityResource(self.env, capacity = VariablesAndParameters.number_of_yellow_dedicated_doctors)
        self.green_corpsman_resource_definition = simpy.Resource(self.env, capacity = VariablesAndParameters.number_of_green_dedicated_corpsmen)
        self.black_corpsman_resource_definition = simpy.Resource(self.env, capacity = VariablesAndParameters.number_of_black_dedicated_corpsmen)

        #Locations
        self.main_bds_resource_definition = simpy.PriorityResource(self.env, capacity = VariablesAndParameters.main_bds_maximum_occupancy)
        self.holding_area_resource_definition = simpy.PriorityResource(self.env, capacity = VariablesAndParameters.holding_area_maximum_occupancy)
        self.aux_treatment_area_resource_definition = simpy.Resource(self.env, capacity = VariablesAndParameters.auxillary_treatment_area_maximum_occupancy)
        self.other_location_resource_definition = simpy.Resource(self.env, capacity = VariablesAndParameters.other_location_maximum_occupancy)
   
    def pickup_and_care_procedures(self):
        #IMPORTANT NOTE TO SELF: regular yield is for events (like resources). Yield timeout is for duration (units of time)
        while VariablesAndParameters.run_number < VariablesAndParameters.number_of_runs:
            #Generate Marine
            self.marine = InstanceOfMarine()
            #self.marine = InstanceOfMarine(VariablesAndParameters.marine_counter)

            #Decide How Long Until We Generate The Next Marine
            self.sampled_interarrival = numpy.random.exponential(VariablesAndParameters.interarrival_mean)
            print("Time Till Next Marine: ", self.sampled_interarrival)
        
            #Wait For Random (Within Average) Amount of Time Before Generating Next Marine
            yield self.env.timeout(self.sampled_interarrival)

            #INITIAL TRIAGE/WATER PICKUP
            #Start Initial Triage Timer
            self.initial_triage_water_pickup_start_time = self.env.now
            print("Initial Triage/Water Pickup Start Time: ", self.initial_triage_water_pickup_start_time)

            #Request Initial Triage/Water Pickup
            self.initial_request = self.initial_triage_resource_definition.request()

            #Wait Until Request Is Fulfilled And Marine Is Picked Up
            yield self.initial_request
            #yield self.env.timeout(initial_request)og

            #Calculate How Long This Initial Triage Will Take
            self.sampled_triage_time = numpy.random.lognormal(VariablesAndParameters.water_pickup_triage_mean_time, VariablesAndParameters.water_pickup_triage_stdev_time, 1)
            print("Calculation of Initial Triage Duration: ", self.sampled_triage_time)

            #Wait For That Initial Triage Time
            yield self.env.timeout(self.sampled_triage_time)

            #End Initial Triage Timer
            self.initial_triage_water_pickup_end_time = self.env.now
            print("Initial Triage/Water Pickup End Time: ", self.initial_triage_water_pickup_end_time)

            #Calculate Initial Triage Elapsed Time
            self.initial_triage_elapsed_time = (self.initial_triage_water_pickup_end_time - self.initial_triage_water_pickup_start_time)
            print("Initial Triage/Water Pickup Elapsed Time: ", self.initial_triage_elapsed_time)

            #Add To Data
            if VariablesAndParameters.run_number > VariablesAndParameters.warm_up:
                Track.individual_times_at_locations_dictionary["Initial Triage/Water Pickup"].append(self.initial_triage_elapsed_time)

            #Give The Resource Back To The System For Another Marine To Use
            self.initial_triage_resource_definition.release(self.initial_request)
            
            #CARE BY TRIAGE PRIORITY/COLOR-CODE

            #RED
            if self.marine.triage_color == "Red":
                #LOCATION
                #Start Red Location Timer
                self.red_main_bds_location_timer_start = self.env.now
                print("Red Location Start Time: ", self.red_main_bds_location_timer_start)

                #Request Main BDS Location
                main_bds_request = self.main_bds_resource_definition.request()

                #Wait Until Request Can Be Fulfilled
                yield main_bds_request

                #End Red Location Timer
                self.red_main_bds_location_timer_end = self.env.now
                print("Red Location End Time: ", self.red_main_bds_location_timer_end)

                #Calculate Red Location Elapsed Time
                self.red_main_bds_location_elapsed_time = (self.red_main_bds_location_timer_end - self.red_main_bds_location_timer_start)
                print("Red Location Elapsed Time: ", self.red_main_bds_location_elapsed_time)

                #Add To Data
                if VariablesAndParameters.run_number > VariablesAndParameters.warm_up:
                    Track.individual_times_at_locations_dictionary["Main Battle Dressing Station"].append(self.red_main_bds_location_elapsed_time)

                #Give The Resource Back To The System For Another Marine To Use
                self.main_bds_resource_definition.release(main_bds_request)

                #WAIT FOR CARE
                #Start Red Doctor Wait Timer
                self.red_doctor_wait_timer_start = self.env.now
                print("Red Doc Wait Time Start: ", self.red_doctor_wait_timer_start)

                #Request Red Doctor
                red_doctor_request = self.red_doctor_resource_definition.request()

                #Wait Until Request Can Be Fulfilled
                yield red_doctor_request

                #End Red Doctor Wait Timer
                self.red_doctor_wait_timer_end = self.env.now
                print("Red Doc Wait End Time: ", self.red_doctor_wait_timer_end)

                #Calculate Red Doctor Wait Time
                self.red_doctor_wait_elapsed_time = (self.red_doctor_wait_timer_end - self.red_doctor_wait_timer_start)
                print("Red Doc Elapsed Time: ", self.red_doctor_wait_elapsed_time)

                #Add To Data
                if VariablesAndParameters.run_number > VariablesAndParameters.warm_up:
                    Track.individual_times_at_locations_dictionary["Waiting For Red Doctor"].append(self.red_doctor_wait_elapsed_time)

                #Give The Resource Back To The System For Another Marine To Use
                self.red_doctor_resource_definition.release(red_doctor_request)
                
                #CARE
                #Start Care Timer
                self.red_doctor_care_timer_start = self.env.now
                print("Red Care Start Time: ", self.red_doctor_care_timer_start)

                #Calculate How Long Care Will Take
                red_care_time = numpy.random.lognormal(VariablesAndParameters.red_mean_doctor_main_bds_consultation, VariablesAndParameters.red_stdev_doctor_main_bds_consultation)
                print("Red Care Calculated Time: ", red_care_time) 

                #Wait That Amount of Care Time
                yield self.env.timeout(red_care_time)

                #Stop Care Timer
                self.red_doctor_care_timer_end = self.env.now
                print("Red Care Timer End: ", self.red_doctor_care_timer_end)

                #Calculate Red Care Time
                self.red_doctor_care_elapsed_time = (self.red_doctor_care_timer_end - self.red_doctor_care_timer_start)
                print("Red Care Elapsed Time: ", self.red_doctor_care_elapsed_time)

                #Add To Data
                if VariablesAndParameters.run_number > VariablesAndParameters.warm_up:
                    Track.individual_times_at_locations_dictionary["With Red Dedicated Doctor"].append(self.red_doctor_care_elapsed_time)

                VariablesAndParameters.run_number += 1

            #YELLOW
            if self.marine.triage_color == "Yellow":
                #LOCATION
                #Start Yellow Location Timer
                self.yellow_holding_area_location_timer_start = self.env.now
                print("Yellow Location Start Time: ", self.yellow_holding_area_location_timer_start)

                #Request Holding Area Location
                holding_area_request = self.holding_area_resource_definition.request()

                #Wait Until Request Can Be Fulfilled
                yield holding_area_request

                #End Yellow Location Timer
                self.yellow_holding_area_location_timer_end = self.env.now
                print("Yellow Location End Time: ", self.yellow_holding_area_location_timer_end)

                #Calculate Yellow Location Elapsed Time
                self.yellow_holding_area_location_elapsed_time = (self.yellow_holding_area_location_timer_end - self.yellow_holding_area_location_timer_start)
                print("Yellow Location Elapsed Time: ", self.yellow_holding_area_location_elapsed_time)

                #Add To Data
                if VariablesAndParameters.run_number > VariablesAndParameters.warm_up:
                    Track.individual_times_at_locations_dictionary["Holding Area"].append(self.yellow_holding_area_location_elapsed_time)

                #Give The Resource Back To The System For Another Marine To Use
                self.holding_area_resource_definition.release(holding_area_request)
                
                #WAIT FOR CARE
                #Start Yellow Doctor Wait Timer
                self.yellow_doctor_wait_timer_start = self.env.now
                print("Yellow Doc Wait Time Start: ", self.yellow_doctor_wait_timer_start)

                #Request Yellow Doctor
                yellow_doctor_request = self.yellow_doctor_resource_definition.request()

                #Wait Until Request Can Be Fulfilled
                yield yellow_doctor_request

                #End Yellow Doctor Wait Timer
                self.yellow_doctor_wait_timer_end = self.env.now
                print("Yellow Doc Wait End Time: ", self.yellow_doctor_wait_timer_end)

                #Calculate Yellow Doctor Wait Time
                self.yellow_doctor_wait_elapsed_time = (self.yellow_doctor_wait_timer_end - self.yellow_doctor_wait_timer_start)
                print("Yellow Doc Elapsed Time: ", self.yellow_doctor_wait_elapsed_time)

                #Add To Data
                if VariablesAndParameters.run_number > VariablesAndParameters.warm_up:
                    Track.individual_times_at_locations_dictionary["Waiting For Yellow Doctor"].append(self.yellow_doctor_wait_elapsed_time)

                #Give The Resource Back To The System For Another Marine To Use
                self.yellow_doctor_resource_definition.release(yellow_doctor_request)
                
                #CARE
                #Start Care Timer
                self.yellow_doctor_care_timer_start = self.env.now
                print("Yellow Care Start Time: ", self.yellow_doctor_care_timer_start)

                #Calculate How Long Care Will Take
                yellow_care_time = numpy.random.lognormal(VariablesAndParameters.yellow_mean_doctor_holding_area_consultation, VariablesAndParameters.yellow_stdev_doctor_holding_area_consultation)
                print("Yellow Care Calculated Time: ", yellow_care_time) 

                #Wait That Amount of Care Time
                yield self.env.timeout(yellow_care_time)

                #Stop Care Timer
                self.yellow_doctor_care_timer_end = self.env.now
                print("Yellow Care Timer End: ", self.yellow_doctor_care_timer_end)

                #Calculate Yellow Care Time
                self.yellow_doctor_care_elapsed_time = (self.yellow_doctor_care_timer_end - self.yellow_doctor_care_timer_start)
                print("Yellow Care Elapsed Time: ", self.yellow_doctor_care_elapsed_time)

                #Add To Data
                if VariablesAndParameters.run_number > VariablesAndParameters.warm_up:
                    Track.individual_times_at_locations_dictionary["With Yellow Dedicated Doctor"].append(self.yellow_doctor_care_elapsed_time)

                VariablesAndParameters.run_number += 1


            #GREEN
            if self.marine.triage_color == "Green":
                #LOCATION
                #Start Green Location Timer
                self.green_aux_treatment_location_timer_start = self.env.now
                print("Green Location Start Time: ", self.green_aux_treatment_location_timer_start)

                #Request Auxillary Treatment Area Location
                aux_treatment_request = self.aux_treatment_area_resource_definition.request()

                #Wait Until Request Can Be Fulfilled
                yield aux_treatment_request

                #End Red Location Timer
                self.green_aux_treatment_location_timer_end = self.env.now
                print("Green Location End Time: ", self.green_aux_treatment_location_timer_end)

                #Calculate Green Location Elapsed Time
                self.green_aux_treatment_location_elapsed_time = (self.green_aux_treatment_location_timer_end - self.green_aux_treatment_location_timer_start)
                print("Green Location Elapsed Time: ", self.green_aux_treatment_location_elapsed_time)

                #Add To Data
                if VariablesAndParameters.run_number > VariablesAndParameters.warm_up:
                    Track.individual_times_at_locations_dictionary["Auxillary Treatment Area"].append(self.green_aux_treatment_location_elapsed_time)

                #Give The Resource Back To The System For Another Marine To Use
                self.aux_treatment_area_resource_definition.release(aux_treatment_request)
                
                #WAIT FOR CARE
                #Start Green Corpsman Wait Timer
                self.green_corpsman_wait_timer_start = self.env.now
                print("Green Corpsman Wait Time Start: ", self.green_corpsman_wait_timer_start)

                #Request Green Corpsman
                green_corpsman_request = self.green_corpsman_resource_definition.request()

                #Wait Until Request Can Be Fulfilled
                yield green_corpsman_request

                #End Green Corpsman Wait Timer
                self.green_corpsman_wait_timer_end = self.env.now
                print("Green Corpsman Wait End Time: ", self.green_corpsman_wait_timer_end)

                #Calculate Green Corpsman Wait Time
                self.green_corpsman_wait_elapsed_time = (self.green_corpsman_wait_timer_end - self.green_corpsman_wait_timer_start)
                print("Green Corpsman Elapsed Time: ", self.green_corpsman_wait_elapsed_time)

                #Add To Data
                if VariablesAndParameters.run_number > VariablesAndParameters.warm_up:
                    Track.individual_times_at_locations_dictionary["Waiting for Green Corpsman"].append(self.green_corpsman_wait_elapsed_time)

                #Give The Resource Back To The System For Another Marine To Use
                self.green_corpsman_resource_definition.release(green_corpsman_request)
                
                #CARE
                #Start Care Timer
                self.green_corpsman_care_timer_start = self.env.now
                print("Green Care Start Time: ", self.green_corpsman_care_timer_start)

                #Calculate How Long Care Will Take
                green_care_time = numpy.random.lognormal(VariablesAndParameters.green_mean_corpsman_auxillary_treatment_area_consultation, VariablesAndParameters.green_stdev_corpsman_auxillary_treatment_area_consultation)
                print("Green Care Calculated Time: ", green_care_time) 

                #Wait That Amount of Care Time
                #BUG
                #Uncommenting will cause system to crash
                yield self.env.timeout(green_care_time)

                #Stop Care Timer
                self.green_corpsman_care_timer_end = self.env.now
                print("Green Care Timer End: ", self.green_corpsman_care_timer_end)

                #Calculate Green Care Time
                self.green_corpsman_care_elapsed_time = (self.green_corpsman_care_timer_end - self.green_corpsman_care_timer_start)
                print("Green Care Elapsed Time: ", self.green_corpsman_care_elapsed_time)

                #Add To Data
                if VariablesAndParameters.run_number > VariablesAndParameters.warm_up:
                    Track.individual_times_at_locations_dictionary["With Green Dedicated Corpsman"].append(self.green_corpsman_care_elapsed_time)
                
                VariablesAndParameters.run_number += 1

            #BLACK
            if self.marine.triage_color == "Black":
                #LOCATION
                #Start Black Location Timer
                self.black_other_location_timer_start = self.env.now
                print("Black Location Start Time: ", self.black_other_location_timer_start)

                #Request Other Location
                other_loc_request = self.other_location_resource_definition.request()

                #Wait Until Request Can Be Fulfilled
                yield other_loc_request

                #End Red Location Timer
                self.black_other_location_timer_end = self.env.now
                print("Black Location End Time: ", self.black_other_location_timer_end)

                #Calculate Black Location Elapsed Time
                self.black_other_location_elapsed_time = (self.black_other_location_timer_end - self.black_other_location_timer_start)
                print("Black Location Elapsed Time: ", self.black_other_location_elapsed_time)

                #Add To Data
                if VariablesAndParameters.run_number > VariablesAndParameters.warm_up:
                    Track.individual_times_at_locations_dictionary["Other Location"].append(self.black_other_location_elapsed_time)

                #Give The Resource Back To The System For Another Marine To Use
                self.other_location_resource_definition.release(other_loc_request)     
                
                #WAIT FOR CARE
                #Start Black Doctor Wait Timer
                self.black_corpsman_wait_timer_start = self.env.now
                print("Black Corpsman Wait Time Start: ", self.black_corpsman_wait_timer_start)

                #Request Black Doctor
                black_corpsman_request = self.black_corpsman_resource_definition.request()

                #Wait Until Request Can Be Fulfilled
                yield black_corpsman_request

                #End Black Corpsman Wait Timer
                self.black_corpsman_wait_timer_end = self.env.now
                print("Black Corpsman Wait End Time: ", self.black_corpsman_wait_timer_end)

                #Calculate Black Corpsman Wait Time
                self.black_corpsman_wait_elapsed_time = (self.black_corpsman_wait_timer_end - self.black_corpsman_wait_timer_start)
                print("Black Corpsman Elapsed Time: ", self.black_corpsman_wait_elapsed_time)

                #Add To Data
                if VariablesAndParameters.run_number > VariablesAndParameters.warm_up:
                    Track.individual_times_at_locations_dictionary["Waiting for Black Corpsman"].append(self.black_corpsman_wait_elapsed_time)

                #Give The Resource Back To The System For Another Marine To Use
                self.black_corpsman_resource_definition.release(black_corpsman_request)
                
                #CARE
                #Start Care Timer
                self.black_corpsman_care_timer_start = self.env.now
                print("Black Care Start Time: ", self.black_corpsman_care_timer_start)

                #Calculate How Long Care Will Take
                black_care_time = numpy.random.lognormal(VariablesAndParameters.black_mean_corpsman_other_location_consultation, VariablesAndParameters.black_stdev_corpsman_other_location_consultation)
                print("Black Care Calculated Time: ", black_care_time) 

                #Wait That Amount of Care Time
                #BUG
                #Uncommenting will cause system to crash.
                yield self.env.timeout(black_care_time)

                #Stop Care Timer
                self.black_corpsman_care_timer_end = self.env.now
                print("Black Care Timer End: ", self.black_corpsman_care_timer_end)

                #Calculate Black Care Time
                self.black_corpsman_care_elapsed_time = (self.black_corpsman_care_timer_end - self.black_corpsman_care_timer_start)
                print("Black Care Elapsed Time: ", self.black_corpsman_care_elapsed_time)

                #Add To Data
                if VariablesAndParameters.run_number > VariablesAndParameters.warm_up:
                    Track.individual_times_at_locations_dictionary["With Black Dedicated Corpsman"].append(self.black_corpsman_care_elapsed_time)

                VariablesAndParameters.run_number += 1

#Class representing...
#CALCULATIONS
#The putting together the outputs of the gonkulator.
class Calculations:
    def total_priority_counts():
        for key, values in Track.individual_marines_priority_count_dictionary.items():
            Track.total_priority_count_dictionary[key] = len(values)

    def average_times_at_locations():
        for key, values in Track.individual_times_at_locations_dictionary.items():
            if len(values) > 0:
                Track.average_times_at_locations_dictionary[key] = sum(values) / len(values)
            else:
                Track.average_times_at_locations_dictionary[key] = 0
            
#RUNNING THE SYSTEM
model = MassCasualtySystem()
model.env.process(model.pickup_and_care_procedures())
model.env.run(until=VariablesAndParameters.simulation_time)

#CALCULATIONS
Calculations.total_priority_counts()
Calculations.average_times_at_locations()

#NEXT UP, PANDAS AND MATPLOTLIB!!
#Remember, probably good to output all this to a .csv as well.