from mcp_server import MCPServer
from energy import Energy
from pv import Pv

class EnergyMCPServer(MCPServer):

    def __init__(self, port: int, energy: Energy, pv: Pv):
        super().__init__("energy", port)
        self.energy = energy
        self.pv = pv

        @self.mcp.tool(name="get_provider_power", description="Current power exchange with the grid provider in Watts. Positive values indicate consumption from the grid; negative values indicate feed-in (export) to the grid.")
        def get_provider_power() -> int:
            return self.energy.provider.provider_power

        @self.mcp.tool(name="get_pv_power_production", description="Current power generation by the PV (solar) system in Watts.")
        def get_pv_power_downstream() -> int:
            return self.energy.pv.power_downstream

        @self.mcp.tool(name="get_battery_discharging_power", description="Current battery discharging power in Watts (power provided by the battery).")
        def get_battery_power_downstream() -> int:
            return self.energy.battery.power_downstream

        @self.mcp.tool(name="get_battery_charging_power", description="Current battery charging power in Watts (power flowing into the battery).")
        def get_battery_power_upstream() -> int:
            return self.energy.battery.power_upstream

        @self.mcp.tool(name="get_power_consumption", description="Current total household power consumption in Watts. Calculated from grid usage, battery usage, and PV self-consumption.")
        def get_power_consumption() -> int:
            return self.energy.power_consumption

        @self.mcp.tool(name="get_power_surplus", description="Current available power surplus from PV production in Watts. This is energy not currently consumed which may be used to charge the battery.")
        def get_power_surplus() -> int:
            return self.energy.power_surplus

        @self.mcp.tool(name="get_power_peak_hour", description="The estimated hour of the day (0-23) when PV production reaches its daily peak (UTC time).")
        def get_power_peak_hour() -> int:
            return self.pv.power_peak_hour_utc