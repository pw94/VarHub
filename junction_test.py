#!/usr/bin/env python
# coding: utf-8

# In[352]:


import requests
import numpy as np
import json
from requests.exceptions import HTTPError


# In[294]:


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


# In[324]:


# Create the list for all the tests and the threshold values
# Lungs
Lungs = [
    {'Metric': 'V30', 'Volume': 30, 'Per_Protocol': 20, 'Accept': 25},
    {'Metric': 'V20', 'Volume': 20, 'Per_Protocol': 25, 'Accept': 30},
    {'Metric': 'V10', 'Volume': 10, 'Per_Protocol': 40, 'Accept': 50},
    {'Metric': 'V5', 'Volume': 5, 'Per_Protocol': 50, 'Accept': 55}]

Heart = [{'Metric': 'V40', 'Volume': 40, 'Per_Protocol': 50, 'Accept': 55}]

Kidneys = [{'Metric': 'V20', 'Volume': 20, 'Per_Protocol': 30, 'Accept': 40}]

Liver =[{'Metric': 'V30', 'Volume': 30, 'Per_Protocol': 30, 'Accept': 40}]

Spine =[{'Metric': 'V30', 'Volume': 30, 'Per_Protocol': 30, 'Accept': 40}]

Bladder =[{'Metric': 'V30', 'Volume': 30, 'Per_Protocol': 20, 'Accept': 30}]


# In[365]:


main_url = 'https://junction-planreview.azurewebsites.net/api/patients'
response = request_json(main_url)
# Start with Abdomen data
# for r in response:
parent_url = main_url + '/'+ response[2] + '/plans'
run_tests(parent_url, response[2])
print(response[2])


# In[364]:


def run_tests(parent_url,patientID):
    response = request_json(parent_url)
    print(response)
    
    dic =[]
    for planID in response:
        # Get the prescribed dose from the planID
        plan_url = parent_url + '/' + planID
        plan = request_json(plan_url)
        prescribed_dose = plan['NumberOfFractions'] *plan['PlannedDosePerFraction']
    
        # Get the volume and dosage mapping for each target region for each plan
    
        # Get all the target regions
        regions = request_json(plan_url + '/dvhcurves')
    
        target = []
        critical_region = []
        # Separate target regions and critical regions
        for region in regions:
            if 'PTV' in region:
                if '_' in region:
                    dose = region.split('_',1)[1]
                else:
                    dose = region.split('V',1)[1]
                target.append({"Region": region, "Dose": float(dose)})
            else:
                critical_region.append(region)

   
        # For target regions check that for dosage above 90% the volume coverage is greater than 90%
        # For dosage above 105% the volume coverage is less than 105%
        # tar = target[0]
        
        for tar in target:
            vol_dose_pairs = request_json(plan_url+'/dvhcurves/'+tar["Region"])['CurvePoints']
            dic1, dic2 = target_volume_test(tar,vol_dose_pairs,planID,patientID)
            dic.append(dic1)
            dic.append(dic2)
            
        
        #Test prescribed threshold volume
        #print(prescribed_th_vol(pairs,prescribed_dose))
    
        #dosage_vol_test(pairs,Lungs_Parameters[0])
        
        #For critical regions check that the dosage is within the specified region
        for crit in critical_region:
            vol_dose_pairs = request_json(plan_url+'/dvhcurves/'+crit)['CurvePoints']
            if 'Lung' in crit:
                dic.append(critical_region_vol_test(Lungs,vol_dose_pairs, prescribed_dose, patientID, planID))
            elif 'Heart' in crit:
                dic.append(critical_region_vol_test(Heart,vol_dose_pairs, prescribed_dose, patientID, planID))
            elif 'Kidney' in crit:
                dic.append(critical_region_vol_test(Kidneys,vol_dose_pairs, prescribed_dose, patientID, planID))
            elif 'Liver' in crit:
                dic.append(critical_region_vol_test(Liver,vol_dose_pairs, prescribed_dose, patientID, planID))
            elif 'Spine' in crit:
                dic.append(critical_region_vol_test(Spine,vol_dose_pairs, prescribed_dose, patientID, planID))
            elif 'Bladder' in crit:
                dic.append(critical_region_vol_test(Bladder,vol_dose_pairs, prescribed_dose, patientID, planID))
        
    with open("tests.json", "w") as write_file:
        json.dump(dic, write_file)
        
    
    
    


# In[358]:


#Test prescribed threshold volume
# Check that the prescribed dose is reached by 95% volume for the region
def target_volume_test(tar,vol_dose_pairs,planID,patientID):
    ninety_percent_pres = 0.9*tar["Dose"]
    threshold_lower = 95
    high_percent = 1.05*tar["Dose"]
    dic1 = []
    dic2 = []
    for pair in vol_dose_pairs:
        if pair['Dose']>=ninety_percent_pres and pair['Dose']<=tar['Dose']:
            if pair["Volume"]<threshold_lower:
                passTh = 'Fail'
            else:
                passTh = 'Pass'
            percent_diff = 100*(threshold_lower-pair["Volume"])/threshold_lower
            description = '% difference:' + str(np.round(percent_diff,2)) + ' for Prescribed Dose: ' + str(tar["Dose"])
            dic1.append({'Patient ID': patientID, 'PlanID': planID, 
                        'Test Name': 'V95% > 90% of Dose',
                        'Verdict': passTh, 'Description': description })
        if pair['Dose']>=high_percent:
            if pair["Volume"]>105:
                passTh = 'Fail'
            else:
                passTh = 'Pass'    
            percent_diff = 100*(105-pair["Volume"])/105
            description = '% difference:' + str(np.round(percent_diff,2)) + ' for Prescribed Dose: ' + str(tar["Dose"])
            dic2.append({'Patient ID': patientID, 'PlanID': planID, 
            'Test Name': 'V105% < 105% of Dose',
            'Verdict': passTh, 'Description': description})
            
    return dic1,dic2


    


# In[333]:


def critical_region_vol_test(threshold,map_vol, dose, patientID, planID):
    dic = []
    for th in threshold:
        dic.append(crit_region(th, map_vol,dose, patientID, planID))
    return dic

def crit_region(th, map_vol, dose, patientID, planID):
    # find volume closest to the vol value
    # compare the dose for that value and check if it is below the input dose
    th_vol = th['Volume']
    r_th = 0.5
    dic = []
    protocol = th['Per_Protocol']*dose/100
    accept = th['Accept']*dose/100
    for m in map_vol:
        if m['Volume']<=th_vol+r_th and m['Volume']>=th_vol-r_th:
            if m['Dose']<protocol:
                verdict = 'Pass'
                des = th['Metric'] + ' is below protocol dose'
            elif m['Dose']<accept:
                verdict = 'Fail *'
                des = th['Metric'] + ' is between protocol dose and accepted variation'
            else:
                verdict = 'Fail'
                des = th['Metric'] + ' is beyond accepted variation dose'
            dic.append({'Patient ID': patientID, 'PlanID': planID, 
            'Test Name': 'Critical Organ Dose Volume',
            'Verdict': verdict, 'Description': des})
            break;
    return dic


# In[199]:





# In[105]:



                


# In[ ]:




