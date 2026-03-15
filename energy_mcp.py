import logging
from mcplib.server import MCPServer
from energy import Energy
from pv import Pv

class EnergyMCPServer(MCPServer):
    """
    MCP Server for monitoring household energy flows.
    Integrates grid, solar (PV), and battery data to provide a unified energy balance.
    """

    def __init__(self, port: int, energy: Energy, pv: Pv):
        super().__init__("energy", port)
        self.energy = energy
        self.pv = pv

        @self.mcp.tool(name="get_energy_report",
                       description="Returns a comprehensive real-time report of all household energy flows in Watts.")
        def get_energy_report() -> str:
            """
            Provides the current state of grid, PV production, battery flows, and consumption.
            Use this to analyze the current energy balance and decide on high-power appliance usage.
            """
            try:
                # Grouping these values ensures the AI has a consistent snapshot of the system
                return (
                    f"Real-time Energy Report:\n"
                    f"- Grid Power: {self.energy.provider.provider_power} W (Positive: Buying/Import | Negative: Exporting)\n"
                    f"- PV Production: {self.energy.pv.power_downstream} W (Current solar generation)\n"
                    f"- PV Daily Peek hour: {self.energy.pv.power_peak_hour_utc} UTC (latest " + ", ".join([str(h) for h in self.energy.pv.latest_peeks_hour_utc()]) + " UTC)\n"
                    f"- Battery Discharge: {self.energy.battery.power_downstream} W (Power usage from battery)\n"
                    f"- Battery Charge: {self.energy.battery.power_upstream} W (Power flowing into battery)\n"
                    f"- Total Consumption: {self.energy.power_consumption} W (Current household load, excluding battery charging)\n"
                    f"- Available Surplus: {self.energy.power_surplus} W (Excess solar energy currently used for battery charging or grid export)"
                )
            except Exception as e:
                # Log full stack trace for debugging; return clean error message to AI
                logging.warning(f"Error fetching energy report: {e}", exc_info=True)
                return f"Error: Could not retrieve energy data. {str(e)}"

        @self.mcp.tool(name="get_pv_forecast_info",
                       description="Returns the daily peak production time forecast for the PV system.")
        def get_pv_forecast_info() -> str:
            """
            Provides predicted peak production time.
            Useful for scheduling energy-intensive tasks to maximize self-consumption.
            """
            return (
                f"PV Forecast Information:\n"
                f"- Daily Peak Hour: {self.pv.power_peak_hour_utc}:00 UTC\n"
                f"- Note: Higher solar production is expected around this time."
            )