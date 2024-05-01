# energy_webthing
A webthing service that provides the energy values including photovoltaic power using shelly 3em pro (provider values) and shelly pro 1pm (PV values)


The energy_webthing provides an http webthing endpoint to query the current energy values
```
# webthing has been started on host 192.168.0.23
curl http://192.168.0.23:8877/properties

{
    "pv_measures_updated": "2024-04-30T05:16:28",
    "provider_measures_updated": "2024-04-30T05:16:28",
    "provider_power": 275,
    "pv_power": 61,
    "pv_effective_power": 61,
    "consumption_power": 336,
    "pv_surplus_power": 0,
    "consumption_power_estimated_year": 19025,
    "pv_power_estimated_year": 3366,
    "pv_effective_power_estimated_year": 2648,
    "provider_power_1m": 322,
    "provider_power_3m": 323,
    "provider_power_current_hour": 316,
    "provider_power_current_day": 3333,
    "provider_power_current_year": 5198,
    "pv_power_1m": 45,
    "pv_power_3m": 44,
    "pv_power_current_hour": 19,
    "pv_power_current_day": 569,
    "pv_power_current_year": 1116,
    "consumption_power_1m": 368,
    "consumption_power_3m": 368,
    "consumption_power_current_hour": 335,
    "consumption_power_current_day": 3897,
    "pv_surplus_power_5s": 0,
    "pv_surplus_power_1m": 0,
    "pv_surplus_power_3m": 0,
    "pv_surplus_power_5m": 0,
    "pv_surplus_power_current_hour": 0
}
```

## docker example
```
sudo docker run --restart always --name energy --network host  -v /etc/energy:/app/energy -e port=8877 -e pv='http://10.1.211.91' -e provider='http://10.1.211.92' -e directory='/app/energy ' grro/energy_webthing:0.0.21
```
