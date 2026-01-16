from mcp_server import MCPServer
from energy import Energy
from pv import Pv



class EnergyMCPServer(MCPServer):

    def __init__(self,port: int, energy: Energy, pv: Pv):
        super().__init__("energy", port)
        self.energy = energy
        self.pv = pv

        @self.mcp.tool(name="get_provider_power", description="Current provider power. May be negative")
        def get_provider_power() -> int:
            return self.energy.provider.provider_power

        @self.mcp.tool(name="get_provider_power_downstream", description="Current downstream provider power")
        def get_provider_power_downstream() -> int:
            return self.energy.provider.provider_power_downstream

        @self.mcp.tool(name="get_provider_power_upstream", description="Current upstream provider power")
        def get_provider_power_upstream() -> int:
            return self.energy.provider.provider_power_upstream

        @self.mcp.tool(name="get_pv_power_downstream", description="Current downstream pv power")
        def get_pv_power_downstream() -> int:
            return self.energy.pv.power_downstream

        @self.mcp.tool(name="get_battery_power_downstream", description="Current downstream battery power")
        def get_battery_power_downstream() -> int:
            return self.energy.battery.power_downstream

        @self.mcp.tool(name="get_battery_power_upstream", description="Current upstream battery power")
        def get_battery_power_upstream() -> int:
            return self.energy.battery.power_upstream

        @self.mcp.tool(name="get_power_consumption", description="Current power consumption")
        def get_power_consumption() -> int:
            return self.energy.power_consumption

        @self.mcp.tool(name="get_power_surplus", description="Current power surplus")
        def get_power_surplus() -> int:
            return self.energy.power_surplus

        @self.mcp.tool(name="get_power_peak_hour", description="The hour of the day when the pv peak currently occurs (UTC)")
        def get_power_peak_hour() -> int:
            return self.pv.power_peak_hour_utc


# npx @modelcontextprotocol/inspector