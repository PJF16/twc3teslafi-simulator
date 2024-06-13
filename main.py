import requests
import json
import time
import os
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException

app = FastAPI()

# TeslaFi API URL and API KEY
TESLAFI_API_URL = "https://www.teslafi.com/feed.php"
TESLAFI_API_KEY = os.getenv('TESLAFI_API_KEY')

# Define the data structure
class Vitals(BaseModel):
    contactor_closed: bool
    vehicle_connected: bool
    session_s: int
    grid_v: float
    grid_hz: float
    vehicle_current_a: float
    currentA_a: float
    currentB_a: float
    currentC_a: float
    currentN_a: float
    voltageA_v: float
    voltageB_v: float
    voltageC_v: float
    relay_coil_v: float
    pcba_temp_c: float
    handle_temp_c: float
    mcu_temp_c: float
    uptime_s: int
    input_thermopile_uv: int
    prox_v: float
    pilot_high_v: float
    pilot_low_v: float
    session_energy_wh: float
    config_status: int
    evse_state: int
    current_alerts: list

# cache for api requests
cache = {
    'data': None,
    'last_fetch_time': 0
}
FETCH_INTERVAL = 20  # fetch only every 20 seconds because TeslaFi only allows 3 requests per minute



def get_teslafi_data():
    current_time = time.time()
    if current_time - cache['last_fetch_time'] >= FETCH_INTERVAL:
        params = {
            'token': TESLAFI_API_KEY,
            'command': 'lastGood'
        }
        response = requests.get(TESLAFI_API_URL, params=params)
        if response.status_code == 200:
            cache['data'] = response.json()
            cache['last_fetch_time'] = current_time
        else:
            return None
    return cache['data']




@app.get("/api/1/vitals", response_model=Vitals)
async def data():
    teslafi_data = get_teslafi_data()
    if teslafi_data:
        charging = False
        if teslafi_data.get('charging_state') == "Disconnected":
            # charger not connected
            connected = False
        else:
            # charger connected and extract data
            connected = True
            if teslafi_data.get('charging_state') == "Charging":
                charging = True

        vitals = Vitals(
            contactor_closed=charging,
            vehicle_connected=connected,
            session_s=0,
            grid_v=229.2,
            grid_hz=49.828,
            vehicle_current_a=teslafi_data.get('charger_actual_current'),
            currentA_a=teslafi_data.get('charger_actual_current'), 
            currentB_a=teslafi_data.get('charger_actual_current'),
            currentC_a=teslafi_data.get('charger_actual_current'),
            currentN_a=0.0,
            voltageA_v=teslafi_data.get('charger_voltage'),
            voltageB_v=teslafi_data.get('charger_voltage'),
            voltageC_v=teslafi_data.get('charger_voltage'),
            relay_coil_v=11.9,
            pcba_temp_c=7.4,
            handle_temp_c=1.8,
            mcu_temp_c=15.2,
            uptime_s=26103,
            input_thermopile_uv=-176,
            prox_v=0.0,
            pilot_high_v=11.9,
            pilot_low_v=11.8,
            session_energy_wh=float(teslafi_data.get('charge_energy_added'))*1000,
            config_status=5,
            evse_state=1,
            current_alerts=[]
        )   
        return vitals

    else:
        raise HTTPException(status_code=500, detail="Unable to fetch data from TeslaFi")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8080)
