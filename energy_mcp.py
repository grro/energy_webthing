import asyncio
import logging
import threading
import socket
from threading import Thread
from time import sleep
from typing import List, Dict, Any, Optional, Callable

from fastmcp import FastMCP
from pydantic import AnyUrl, TypeAdapter
from zeroconf import IPVersion, ServiceInfo, Zeroconf

from energy import Energy
from pv import Pv

logger = logging.getLogger(__name__)


class MDNS:
    def __init__(self):
        self.registered: Dict[str, ServiceInfo] = dict()
        self.zc = Zeroconf(ip_version=IPVersion.V4Only)
        self.service_type = "_mcp._tcp.local."
        self.hostname = socket.gethostname()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            self.local_ip = s.getsockname()[0]
        finally:
            s.close()

    def register_mdns(self, name: str, port: int):
        try:
            service_name = f"{name}.{self.service_type}"
            service_info = ServiceInfo(
                type_=self.service_type,
                name=service_name,
                addresses=[socket.inet_aton(self.local_ip)],
                port=port,
                properties={
                    "version": "1.0",
                    "path": "/sse",
                    "server_type": "fastmcp"
                },
                server=f"{self.hostname}.local.",
            )

            logging.info(f"mDNS: Registering {service_name} at {self.local_ip}:{port}")
            self.zc.register_service(service_info)
            self.registered[name] = service_info
        except Exception as e:
            logging.error(f"mDNS Registration failed: {e}")

    def unregister_mdns(self, name: str):
        service_info = self.registered.get(name)
        if service_info is not None:
            logging.info("mDNS: Unregistering service...")
            self.zc.unregister_service(service_info)
            self.zc.close()



class Sessions:
    def __init__(self):
        # Actually initialize the set, not just type-hint it
        self.active_sessions: set[Any] = set()
        # Create a lock for this instance
        self._lock = threading.Lock()

    def add(self, session: Any):
        # Acquire the lock before modifying the set
        with self._lock:
            self.active_sessions.add(session)

    def remove(self, session: Any):
        # Acquire the lock before modifying the set
        with self._lock:
            # discard() removes the element if it exists,
            # without raising a KeyError if it was already removed by another thread
            self.active_sessions.discard(session)

    def get_all(self) -> set[Any]:
        """
        Returns a shallow copy of the active sessions.
        Crucial for thread safety if you need to iterate over them.
        """
        with self._lock:
            # Return a copy so the original set can still be safely
            # modified by other threads while you iterate over the copy
            return set(self.active_sessions)


class Notifier:

    def __init__(self, sessions: Sessions, loop: asyncio.AbstractEventLoop, name: str, value_reader: Callable[[], int] ):
        self.name = name
        self.old_value = None
        self.value_reader = value_reader
        self.loop = loop
        self.sessions = sessions
        self.uri = TypeAdapter(AnyUrl).validate_python(f"sensor://metrics/{name}")

    def check(self):
        new_value = self.value_reader()
        if self.old_value != new_value:
            self.old_value = new_value
            asyncio.run_coroutine_threadsafe(self.__send_notification(), self.loop)

    async def __send_notification(self):
        """
        Sends an SSE update notification to all registered client sessions.
        Cleans up any sessions that have disconnected.
        """
        active_sessions = self.sessions.get_all()

        if not active_sessions:
            return

        # 2. Iterate and send using the pre-computed self.uri
        for session in active_sessions:
            try:
                await session.send_resource_updated(self.uri)
            except Exception as e:
                logger.warning(f"[Server] Client no longer reachable: {e}")
                self.sessions.remove(session)




class EnergyMCPServer:
    def __init__(self, port: int, energy: Energy, pv: Pv, presences: Optional[List[Any]] = None, host: str = "0.0.0.0"):
        self.name = 'Energy'
        self.host = host
        self.port = port
        self.energy = energy
        self.pv = pv
        self.presences = presences or []

        self.mdns = MDNS()
        self.mcp = FastMCP(self.name)
        self.loop = asyncio.new_event_loop()

        self.last_state: Dict[str, bool] = dict()

        self.is_running = True
        self.sessions = Sessions()
        self.notifiers = [Notifier(self.sessions, self.loop, 'grid_power', lambda : self.energy.provider.provider_power),
                          Notifier(self.sessions, self.loop, 'pv_production', lambda : self.energy.pv.power_downstream),
                          Notifier(self.sessions, self.loop, 'available_surplus', lambda : self.energy.power_surplus)]

        self._setup_mcp()

        Thread(target=self.__refresh_loop, daemon=True).start()


    def __refresh_loop(self):
        while self.is_running:
            try:
                for notifier in self.notifiers:
                    notifier.check()
            except Exception as e:
                logging.warning(f"Error in refresh loop: {e}", exc_info=True)
            sleep(2)

    def _setup_mcp(self):
        
        @self.mcp.resource("sensor://metrics")
        def get_metric_names() -> list[str]:
            """
            Returns a list of available energy metric names.

            This resource provides the valid keys that can be dynamically
            queried using the 'sensor://metrics/{name}' endpoint.
            """
            return ['grid_power', 'pv_production', 'available_surplus']


        @self.mcp.resource("sensor://metrics/{name}")
        def get_single_metric(name: str) -> str:
            """
            Retrieves the current value and description for a specific energy metric.

            Automatically registers the client's session to receive real-time
            Server-Sent Events (SSE) updates for this resource.

            Args:
                name (str): The specific metric to query (e.g., 'grid_power').

            Returns:
                str: A descriptive string containing the current value and unit,
                     or an error message if the metric name is invalid.
            """
            # Register the session manually via the low-level MCP server context
            try:
                # The request_context variable in the MCP SDK is a ContextVar.
                # We call .get() if available, otherwise we use the attribute directly.
                ctx_var = self.mcp._mcp_server.request_context
                req_ctx = ctx_var.get() if hasattr(ctx_var, "get") else ctx_var

                if req_ctx and req_ctx.session and req_ctx.session not in self.sessions.get_all():
                    self.sessions.add(req_ctx.session)
                    logger.info(f"[Server] Client session registered for updates (Resource: {name}).")
            except Exception as e:
                logger.debug(f"[Server] Could not register session: {e}")

            # Route the request to the correct data point
            if name == 'grid_power':
                return f"Grid Power: {self.energy.provider.provider_power} W (Positive: Import/Buying | Negative: Exporting)"
            elif name == 'pv_production':
                return f"PV Production: {self.energy.pv.power_downstream} W (Current solar generation)"
            elif name == 'available_surplus':
                return f"Available Surplus: {self.energy.power_surplus} W (Excess solar energy)"

            # Fallback for unknown metrics
            return f"Error: Metric '{name}' is not recognized or not available."

        @self.mcp.tool(name="get_energy_report")
        def get_energy_report() -> str:
            """
            Fetches a comprehensive, real-time snapshot of the household's energy flows.

            This report includes grid usage (import/export), active solar (PV) production,
            battery state of charge and flows, total household consumption, and available surplus energy.

            Returns:
                str: A formatted Markdown string containing the categorized energy metrics.
            """
            try:
                # Note: Assuming your method is spelled 'latest_peeks', keeping it to prevent crashes.
                latest_peaks = ", ".join([str(h) for h in self.energy.pv.latest_peeks_hour_utc()])

                return (
                    "## Real-Time Energy Report\n\n"
    
                    "### Grid & Consumption\n"
                    f"- **Grid Power:** {self.energy.provider.provider_power} W (Positive: Import/Buying | Negative: Exporting)\n"
                    f"- **Total Consumption:** {self.energy.power_consumption} W (Current household load, excluding battery charging)\n\n"
    
                    "### Solar (PV)\n"
                    f"- **PV Production:** {self.energy.pv.power_downstream} W (Current solar generation)\n"
                    f"- **Available Surplus:** {self.energy.power_surplus} W (Excess solar used for battery charging or grid export)\n"
                    f"- **Expected Peak Hour:** {self.energy.pv.power_peak_hour_utc}:00 UTC (Recent peaks: {latest_peaks} UTC)\n\n"
    
                    "### Battery\n"
                    f"- **State of Charge:** {self.energy.battery.state_of_charge}% (Total capacity: 1.92 kWh | Minimum reserve: 10%)\n"
                    f"- **Charging Power:** {self.energy.battery.power_upstream} W (Power flowing into battery)\n"
                    f"- **Discharging Power:** {self.energy.battery.power_downstream} W (Power usage from battery)\n"
                )
            except Exception as e:
                logging.warning(f"Error fetching energy report: {e}", exc_info=True)
                return f"Error: Could not retrieve energy data. {str(e)}"


        @self.mcp.tool(name="get_pv_forecast_info")
        def get_pv_forecast_info() -> str:
            """
            Retrieves the forecasted peak production hour for the solar (PV) system.

            Call this tool to find out when the solar panels are expected to generate
            the most power today. This is useful for scheduling energy-intensive tasks
            (e.g., washing machines, EV charging) to maximize self-consumption.

            Returns:
                str: A formatted Markdown string containing the forecasted daily peak hour.
            """
            return (
                "## PV Forecast Information\n\n"
                f"- **Daily Peak Hour:** {self.pv.power_peak_hour_utc}:00 UTC\n"
                f"- **Recommendation:** Schedule high-energy tasks around this time to maximize the use of your own solar power."
            )

    async def __run(self) -> None:
        logger.info(f"MCP Server '{self.name}' running on http://{self.host}:{self.port}/sse")
        await self.mcp.run_async(transport="sse", host=self.host, port=self.port)


    def start(self):
        self.mdns.register_mdns(self.name, self.port)

        def _run_loop():
            asyncio.set_event_loop(self.loop)
            try:
                self.loop.run_until_complete(self.__run())
            finally:
                self.loop.close()

        thread = threading.Thread(target=_run_loop, daemon=True)
        thread.start()


    def stop(self):
        self.mdns.unregister_mdns(self.name)
        if self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        self.is_running = False
        logging.info("MCP Server stopped")