#!/usr/bin/env python
# coding: utf-8

# In[115]:


import numpy as np
import math
import json
import requests
from requests.exceptions import HTTPError


# In[116]:


def request_json(url):
    try:
        response = requests.get(url)

        # If the response was successful, no Exception will be raised
        response.raise_for_status()
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')  # Python 3.6
    except Exception as err:
        print(f'Other error occurred: {err}')  # Python 3.6
    return response.json()


# In[178]:


#Test to check if the contours of the predicted radiations correspond to the contours of the detected tumor
def test_contour(patientId, planId, doseContour, imageId, imageContour):
    
    thresholdError = 80000           # this is harcoded and can be changed later
    
    url = 'https://junction-planreview.azurewebsites.net/api/patients/' + patientId + '/plans/' + planId + '/isodose-contours/' + doseContour
    response = requests.get(url).content    
    doseList = response.splitlines()
    n = int(doseList[4].split()[1])        # retrieve number of 3D points 
    doseList = doseList[5:]                # removing first lines containing meta-data
    xDose = np.array([])
    yDose = np.array([])
    zDose = np.array([])
    for line in doseList[:n]:
        coords = line.split()
        xDose = np.append(xDose, float(coords[0]))
        yDose = np.append(yDose, float(coords[1]))
        zDose = np.append(zDose, float(coords[2]))
  

    url = 'https://junction-planreview.azurewebsites.net/api/patients/' + patientId + '/images/' + imageId + '/structure-contours/' + imageContour
    response = requests.get(url).content   
    imageList = response.splitlines()
    m = int(imageList[4].split()[1])   
    imageList = imageList[5:]
    xImage = np.array([])
    yImage = np.array([])
    zImage = np.array([])
    for line in imageList[:m]:
        coords = line.split()
        xImage = np.append(xImage, float(coords[0]))
        yImage = np.append(yImage, float(coords[1]))
        zImage = np.append(zImage, float(coords[2]))
        error = 0
  
    if m < n:
        n = m
    for i in range(n):
        dist = math.sqrt((xDose[i] - xImage[i]) * (xDose[i] - xImage[i]) + (yDose[i] - yImage[i]) * (yDose[i] - yImage[i]) + (zDose[i] - zImage[i]) * (zDose[i] - zImage[i]))
        error = error + dist

    if error > thresholdError:
        err = int(error - thresholdError)
        return json.dumps({'patient_id': patientId, 'plan_id': planId , 'test_name' : 'TestContour', 'is_valid': False, 'Description': (str(err) + ' above threshold')})
    else:
        return json.dumps({'patient_id': patientId, 'plan_id': planId , 'test_name' : 'TestContour', 'is_valid': True, 'Description': 'acceptable'})


# In[179]:


print(test_contour('Abdomen','JSu-IM103', '50.400-Gy', '15657-Series-3-CT02', 'PTV_50.4'))


# In[180]:


print(test_contour('Lung','JSu-IM102', '63.000-Gy', '1622-Series-CT01', 'PTV_63'))


# In[213]:


# Look through all lines. If sum on line is higher than threshold, it means it is  a high dosage. 
# If previous value is above threshold, add to error their difference.
# In this way, check if a low dosage should actually be high as it is probably within a tumor.
def test_insideDose(patientId, planId):
    
    highDoseThresh = 8000
    thresholdError = 300000
    
    url = 'https://junction-planreview.azurewebsites.net/api/patients/' + patientId + '/plans/' + planId + '/dosevoxels'
    response = requests.get(url).content  
    insideList = np.array(response.splitlines()[11:])    
    prevSum = 0
    error = 0
    for line in insideList:
        doses = line.split()
        doses = map(int, doses)
        s = sum(doses)
        if s > highDoseThresh:
            if prevSum > highDoseThresh:
                error = error + abs(s - prevSum)
        prevSum = s
    
    if error > thresholdError:
        err = int(error - thresholdError)
        return json.dumps({'patient_id': patientId, 'plan_id': planId , 'test_name' : 'TestInsideDose', 'is_valid': False, 'Description': (str(err) + ' above threshold')})
    else:
        return json.dumps({'patient_id': patientId, 'plan_id': planId , 'test_name' : 'TestInsideDose', 'is_valid': True, 'Description': 'acceptable'})


# In[214]:


test_insideDose('Abdomen', 'JSu-IM103')


# In[215]:


test_insideDose('Lung', 'JSu-IM102')

