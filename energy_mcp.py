from time import sleep
from mcp_server import MCPServer
from energy import Energy





class EnergyMCPServer(MCPServer):

    def __init__(self,port: int, energy: Energy):
        super().__init__("energy", port)
        self.energy = energy

        @self.mcp.resource("resource://provider_power_downstream", description="Current downstream provider power")
        def get_provider_power_downstream() -> int:
            return energy.provider.provider_power_downstream

        @self.mcp.resource("resource://provider_power_downstream_smoothen_5s", description="Current downstream provider power (smoothen 5 sec)")
        def get_provider_power_downstream_smoothen_5s() -> int:
            return energy.provider.provider_power_downstream_5s

        @self.mcp.resource("resource://provider_power_downstream_smoothen_15s", description="Current downstream provider power (smoothen 15 sec)")
        def get_provider_power_downstream_smoothen_15s() -> int:
            return energy.provider.provider_power_downstream_15s

        @self.mcp.resource("resource://provider_power_downstream_smoothen_1m", description="Current downstream provider power (smoothen 1 min)")
        def get_provider_power_downstream_smoothen_1m() -> int:
            return energy.provider.provider_power_downstream_1m

        @self.mcp.resource("resource://provider_power_upstream", description="Current upstream provider power")
        def get_provider_power_upstream() -> int:
            return energy.provider.provider_power_upstream

        @self.mcp.resource("resource://provider_power_upstream_smoothen_5s", description="Current upstream provider power (smoothen 5 sec)")
        def get_provider_power_upstream_smoothen_5s() -> int:
            return energy.provider.provider_power_upstream_5s

        @self.mcp.resource("resource://provider_power_upstream_smoothen_15s", description="Current upstream provider power (smoothen 15 sec)")
        def get_provider_power_upstream_smoothen_15s() -> int:
            return energy.provider.provider_power_upstream_15s

        @self.mcp.resource("resource://provider_power_upstream_smoothen_1m", description="Current upstream provider power (smoothen 1 min)")
        def get_provider_power_upstream_smoothen_1m() -> int:
            return energy.provider.provider_power_upstream_1m

        @self.mcp.resource("resource:/pv_downstream", description="Current downstream pv power")
        def get_pv_power_downstream() -> int:
            return energy.pv.power_downstream

        @self.mcp.resource("resource:/pv_downstream_5s", description="Current downstream pv power (smoothen 5 sec)")
        def get_pv_power_downstream_5s() -> int:
            return energy.pv.power_downstream_5s

        @self.mcp.resource("resource:/pv_downstream_15s", description="Current downstream pv power (smoothen 15 sec)")
        def get_pv_power_downstream_15s() -> int:
            return energy.pv.power_downstream_15s

        @self.mcp.resource("resource:/pv_downstream_1m", description="Current downstream pv power (smoothen 1 min)")
        def get_pv_power_downstream_1m() -> int:
            return energy.pv.power_downstream_1m



        @self.mcp.resource("resource://battery_power_downstream", description="Current downstream battery power")
        def get_battery_power_downstream() -> int:
            return energy.battery.power_downstream

        @self.mcp.resource("resource://battery_power_downstream_smoothen_5s", description="Current downstream battery power (smoothen 5 sec)")
        def get_battery_power_downstream_smoothen_5s() -> int:
            return energy.battery.power_downstream_5s

        @self.mcp.resource("resource://battery_power_downstream_smoothen_15s", description="Current downstream battery power (smoothen 15 sec)")
        def get_battery_power_downstream_smoothen_15s() -> int:
            return energy.battery.power_downstream_15s

        @self.mcp.resource("resource://battery_power_downstream_smoothen_1m", description="Current downstream battery power (smoothen 1 min)")
        def get_battery_power_downstream_smoothen_1m() -> int:
            return energy.battery.power_downstream_1m

        @self.mcp.resource("resource://battery_power_upstream", description="Current upstream battery power")
        def get_battery_power_upstream() -> int:
            return energy.battery.power_upstream

        @self.mcp.resource("resource://battery_power_upstream_smoothen_5s", description="Current upstream battery power (smoothen 5 sec)")
        def get_battery_power_upstream_smoothen_5s() -> int:
            return energy.battery.power_upstream_5s

        @self.mcp.resource("resource://battery_power_upstream_smoothen_15s", description="Current upstream battery power (smoothen 15 sec)")
        def get_battery_power_upstream_smoothen_15s() -> int:
            return energy.battery.power_upstream_15s

        @self.mcp.resource("resource://battery_power_upstream_smoothen_1m", description="Current upstream battery power (smoothen 1 min)")
        def get_battery_power_upstream_smoothen_1m() -> int:
            return energy.battery.power_upstream_1m


# npx @modelcontextprotocol/inspector