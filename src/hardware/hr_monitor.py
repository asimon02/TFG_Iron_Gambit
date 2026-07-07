"""
hr_monitor.py -- Monitor pasivo de frecuencia cardiaca por BLE

Escucha los paquetes de broadcast de los dispositivos
Polar (ej. Polar Vantage V3 en modo 'Compartir FC') y
extrae las pulsaciones en tiempo real.
"""

import asyncio
import logging
import queue
import threading
from typing import Optional, Callable

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

# Configuracion basica del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("HeartRateMonitor")

class HeartRateMonitor:
    """
    Monitoriza la frecuencia cardiaca mediante Bluetooth Low Energy (BLE)
    en modo pasivo (solo lectura de anuncios).

    Atributos publicos
    ------------------
    data_queue : queue.Queue -- cola thread-safe con los BPM leidos
    callback   : Callable    -- funcion a llamar con cada lectura
    """

    def __init__(self, data_queue: Optional[queue.Queue] = None, callback: Optional[Callable[[int], None]] = None):
        self.data_queue = data_queue
        self.callback = callback
        
        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._stop_event: Optional[asyncio.Event] = None
        self._last_bpm: int = 0
        
        # ID de fabricante de Polar Electro Oy
        self.POLAR_MANUFACTURER_ID = 107
        self._scanner: Optional[BleakScanner] = None

    # -- Ciclo de vida --------------------------------------------------------

    # Inicia el monitor en un hilo secundario
    def start(self):
        if self._is_running:
            return

        self._is_running = True
        self._thread = threading.Thread(target=self._run_thread, daemon=False, name="BLE_PassiveMonitor_Thread")
        self._thread.start()
        logger.info("Monitor pasivo BLE iniciado.")

    # Detiene la monitorizacion de forma segura
    def stop(self):
        if not self._is_running:
            return
            
        logger.info("Deteniendo el monitor BLE...")
        self._is_running = False
        
        if self._stop_event is not None and self._loop is not None:
            try:
                self._loop.call_soon_threadsafe(self._stop_event.set)
            except RuntimeError:
                pass
                
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)

        if self._thread and self._thread.is_alive() and self._loop is not None:
            try:
                self._loop.call_soon_threadsafe(self._loop.stop)
            except RuntimeError:
                pass
            self._thread.join(timeout=1.0)

        self._thread = None
        self._stop_event = None
        self._scanner = None

    # -- Hilo y Bucle Asincrono -----------------------------------------------

    # Punto de entrada del hilo secundario
    def _run_thread(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        self._stop_event = asyncio.Event()
        
        try:
            self._loop.run_until_complete(self._async_main_loop())
        except RuntimeError as e:
            logger.warning(f"Bucle BLE detenido durante el cierre: {e}")
        except Exception as e:
            logger.error(f"Error en bucle BLE: {e}")
        finally:
            pending = asyncio.all_tasks(self._loop)
            for task in pending:
                task.cancel()
            
            if pending:
                self._loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            self._loop.close()
            self._loop = None

    # Arranca y mantiene el escaner Bleak
    async def _async_main_loop(self):
        self._scanner = BleakScanner(detection_callback=self._detection_callback, scanning_mode="active")
        
        try:
            await self._scanner.start()
            await self._stop_event.wait()
        except Exception as e:
            logger.error(f"Error durante el escaneo BLE: {e}")
        finally:
            if self._scanner:
                try:
                    await self._scanner.stop()
                except Exception as e:
                    logger.warning(f"No se pudo detener el scanner BLE limpiamente: {e}")

    # -- Procesamiento de Datos -----------------------------------------------

    # Filtra e intercepta cada paquete de broadcast
    def _detection_callback(self, device: BLEDevice, advertisement_data: AdvertisementData):
        if device.name and "Polar" in device.name:
            if self.POLAR_MANUFACTURER_ID in advertisement_data.manufacturer_data:
                payload = advertisement_data.manufacturer_data[self.POLAR_MANUFACTURER_ID]
                
                if len(payload) >= 13:
                    bpm = payload[-1]
                    
                    if bpm > 0:
                        self._last_bpm = bpm
                        self._emit_data(bpm)

    # Envia los BPM a la interfaz o cola
    def _emit_data(self, bpm: int):
        if self.data_queue is not None:
            self.data_queue.put(bpm)
        
        if self.callback is not None:
            try:
                self.callback(bpm)
            except Exception as e:
                logger.error(f"Error en callback de BPM: {e}")
