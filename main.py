import requests
import threading
import time
from datetime import datetime

api_url = "https://api.coxauto-interview.com/api"
vehicle_data=[]
dealer_data=[]

def main_req(url):
	#generic function for all get reqs
	#try catch to catch any exceptions with req
	headers = {
		'accept': 'text/plain',
	}

	try:
		response = requests.get(url, headers=headers, timeout= 15)
		return response
	except requests.exceptions.RequestException as e:  # This is the correct syntax
		print("error", e)
		raise SystemExit(e)

def get_datasetID():
	#simple get req to gen a datatsetID
	datatsetID_url = api_url + "/datasetId"

	response = main_req(datatsetID_url)

    #after req if 200 continue   
	if (response.status_code == 200):
		jsonResponse = response.json()
		datasetId = jsonResponse['datasetId']
		print(datetime.now().strftime('%T') + " Got dataset ID:", datasetId)
		return datasetId

	else:
		#if timeout or api is down handle 
		#simple retry with sleep
		print(datetime.now().strftime('%T') + " Error in get_datasetID", response.status_code)
		time.sleep(5)
		get_datasetID()


def vehicleIds(dataset_ID):
	#get req to get vehicle ids
	vehicleIds_url = api_url + "/" + dataset_ID + "/vehicles"

	response = main_req(vehicleIds_url)

    #after req if 200 continue   
	if (response.status_code == 200):
		jsonResponse = response.json()
		vehicle_ids = jsonResponse['vehicleIds']
		#gives a list of ids
		#return the list do stuff with list
		print(datetime.now().strftime('%T') + " Got Vehicle IDs")
		return vehicle_ids

	else:
		#if api is down handle retry
		#simple retry with sleep
		print(datetime.now().strftime('%T') + " Error in vehicleIds function", response.status_code)
		time.sleep(5)
		vehicleIds(dataset_ID)

def get_data(array_list, url):
	#generic function used to get data for vehicles abd dealers
	mythread = threading.currentThread().getName()
	print (datetime.now().strftime('%T') + " [" + mythread + "] " + "Started")

	response = main_req(url)

    #after req if 200 continue   
	if (response.status_code == 200):
		jsonResponse = response.json()
		#print (datetime.now().strftime('%T') + " [" + mythread + "] " + "Got response")
		array_list.append(jsonResponse)

	else:
		#if api is down handle retry
		#simple retry with sleep
		print(datetime.now().strftime('%T') + " Error in get_data function", response.status_code)
		time.sleep(5)
		get_data(array_list, url)


def get_vehicles(dataset_ID, vehicle_id_list):
	#creates 2 empty lists fou use within function
	vehicles = []
	threads = []

	#removes duplicate vehicle ids 
	vehicle_id_list = list(set(vehicle_id_list))

	#makes a list of urls to retrive vehicle data
	for i in range(len(vehicle_id_list)):
		url = api_url + "/" + dataset_ID + "/vehicles" + "/" + str(vehicle_id_list[i])
		vehicles.append(url)

	#run multiple threads because we want to optimze time 
	#here worst case senario will be 4 sec to finsh all rather than i*4 (because server delay cannot be bypassed)
	print (datetime.now().strftime('%T') + " Getting Vehicles data...")
	for i in range(len(vehicles)):
		t = threading.Thread(target=get_data, args=[vehicle_data, vehicles[i]])
		threads.append(t)
		t.start()
	
	#wait for all threads to finsh
	for x in threads:
		x.join()

	print(datetime.now().strftime('%T') + " " + str(vehicle_data))
	print(datetime.now().strftime('%T') + " Got vehicle data")

def get_dealers(dataset_ID):
	#creates 2 empty lists fou use within function
	dealers = []
	threads = []

	#makes a list of urls to retrive dealer data
	for i in range(len(vehicle_data)):
		url = api_url + "/" + dataset_ID + "/dealers" + "/" + str(vehicle_data[i].get('dealerId'))
		dealers.append(url)

	#remove duplicate dealers
	#because multiple cars can have same dealers
	dealers = list(set(dealers))

	#run multiple threads because we want to optimze time 
	#here worst case senario will be 4 sec to finsh all rather than i*4
	print (datetime.now().strftime('%T') + " Getting Dealers data...")
	for i in range(len(dealers)):
		t = threading.Thread(target=get_data, args=[dealer_data, dealers[i]])
		threads.append(t)
		t.start()
	
	#wait for all threads to finsh
	for x in threads:
		x.join()

	print(datetime.now().strftime('%T') + " " + str(dealer_data))
	print (datetime.now().strftime('%T') + " Got dealers data")

def post_answer(dataset_ID):
	vehicle_inventory = {"dealers":[]}

	for i in range(len(dealer_data)):
		dict_data = dealer_data[i]
		dict_data["vehicles"] = []
		vehicle_inventory["dealers"].append(dict_data)

	for i in range(len(vehicle_data)):
		for j in range(len(vehicle_inventory["dealers"])):
			if(vehicle_data[i].get('dealerId') == vehicle_inventory["dealers"][j].get('dealerId')):
				del vehicle_data[i]['dealerId']
				vehicle_inventory["dealers"][j]["vehicles"].append(vehicle_data[i])

	print(vehicle_inventory)
	url = api_url + "/" + dataset_ID + "/answer"


	headers = {
	'accept': 'text/plain',
	'Content-Type': 'text/json',
	}

	try:
		response = requests.post(url, headers=headers, data=str(vehicle_inventory), timeout=15)
		jsonResponse = response.json()
	except requests.exceptions.RequestException as e:  # This is the correct syntax
		print("error", e)
		raise SystemExit(e)

	if (response.status_code == 200 and jsonResponse['message'] == 'Congratulations.'):
		print(datetime.now().strftime('%T') + " Success posting data and data validated by server")
		print(jsonResponse)

	else:
		#if timeout or api is down handle 
		#simple retry with sleep
		print(datetime.now().strftime('%T') + " Error in posting data", response.status_code)
		print(response.json())
		time.sleep(5)
		get_datasetID()


def main():
	dataset_ID = get_datasetID() # returns a string of datasetID
	vehicle_id_list = vehicleIds(dataset_ID) # retures a list of vehicle_ids
	get_vehicles(dataset_ID, vehicle_id_list)
	get_dealers(dataset_ID)
	post_answer(dataset_ID)

main()