from abc import ABC, abstractmethod
from datetime import datetime
import logging


# --- 1. CONFIGURACIÓN DE LOGS Y EXCEPCIONES ---
logging.basicConfig(
    filename="sistema_fj.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8",
)


class SoftwareFJError(Exception):
    """Excepción base del sistema Software FJ."""


class ValidacionError(SoftwareFJError):
    """Error por datos inválidos o parámetros faltantes."""


class ServicioNoDisponibleError(SoftwareFJError):
    """Error cuando un servicio no está disponible."""


class ReservaError(SoftwareFJError):
    """Error en operaciones de reserva o cálculo."""


# --- 2. CLASES ABSTRACTAS Y ENTIDADES ---
class EntidadBase(ABC):
    def __init__(self, id_entidad: str):
        if not id_entidad or not str(id_entidad).strip():
            raise ValidacionError("El ID de la entidad es obligatorio.")
        self._id_entidad = str(id_entidad).strip()
        self._creado_en = datetime.now()

    @property
    def id_entidad(self) -> str:
        return self._id_entidad

    @abstractmethod
    def describir(self) -> str:
        pass


class Cliente(EntidadBase):
    def __init__(self, id_entidad: str, nombre: str, correo: str):
        super().__init__(id_entidad)
        self.nombre = nombre
        self.correo = correo

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str):
        if not valor or len(valor.strip()) < 2:
            raise ValidacionError("El nombre del cliente debe tener al menos 2 caracteres.")
        self._nombre = valor.strip()

    @property
    def correo(self) -> str:
        return self._correo

    @correo.setter
    def correo(self, valor: str):
        if not valor or "@" not in valor or "." not in valor.split("@")[-1]:
            raise ValidacionError(f"Correo electrónico inválido: '{valor}'.")
        self._correo = valor.strip().lower()

    def describir(self) -> str:
        return f"Cliente [{self.id_entidad}]: {self.nombre} ({self.correo})"


class Servicio(EntidadBase, ABC):
    def __init__(self, id_entidad: str, nombre: str, tarifa_base: float, disponible: bool = True):
        super().__init__(id_entidad)
        if not nombre or not nombre.strip():
            raise ValidacionError("El nombre del servicio es obligatorio.")
        if tarifa_base <= 0:
            raise ValidacionError("La tarifa base debe ser mayor que cero.")
        self._nombre = nombre.strip()
        self._tarifa_base = float(tarifa_base)
        self._disponible = bool(disponible)

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def tarifa_base(self) -> float:
        return self._tarifa_base

    @property
    def disponible(self) -> bool:
        return self._disponible

    @disponible.setter
    def disponible(self, estado: bool):
        self._disponible = bool(estado)

    @abstractmethod
    def validar_parametros(self, duracion: float, **kwargs) -> None:
        pass

    @abstractmethod
    def _costo_bruto(self, duracion: float, **kwargs) -> float:
        pass

    # Simulación de sobrecarga de métodos mediante parámetros opcionales
    def calcular_costo(self, duracion: float, descuento: float = 0.0, impuesto: float = 0.0, **kwargs) -> float:
        try:
            if not (0.0 <= descuento < 1.0):
                raise ValidacionError("El descuento debe estar entre 0.0 y 0.99.")
            if impuesto < 0.0:
                raise ValidacionError("El impuesto no puede ser negativo.")
            self.validar_parametros(duracion, **kwargs)
            bruto = self._costo_bruto(duracion, **kwargs)
            con_descuento = bruto * (1.0 - descuento)
            total = con_descuento * (1.0 + impuesto)
            return round(total, 2)
        except SoftwareFJError:
            raise
        except Exception as exc:
            raise ReservaError(f"Error al calcular costo para '{self.nombre}'.") from exc


class ReservaSala(Servicio):
    def __init__(self, id_entidad: str, nombre: str, tarifa_base: float, capacidad: int, disponible: bool = True):
        super().__init__(id_entidad, nombre, tarifa_base, disponible)
        if capacidad <= 0:
            raise ValidacionError("La capacidad de la sala debe ser mayor que cero.")
        self.capacidad = capacidad

    def validar_parametros(self, duracion: float, **kwargs) -> None:
        if duracion <= 0:
            raise ValidacionError("La duración en horas para reserva de sala debe ser mayor que 0.")

    def _costo_bruto(self, duracion: float, **kwargs) -> float:
        return self.tarifa_base * duracion

    def describir(self) -> str:
        return f"Sala '{self.nombre}' (Cap. {self.capacidad}, ${self.tarifa_base}/h)"


class AlquilerEquipo(Servicio):
    def __init__(self, id_entidad: str, nombre: str, tarifa_base: float, categoria: str, disponible: bool = True):
        super().__init__(id_entidad, nombre, tarifa_base, disponible)
        if not categoria or not categoria.strip():
            raise ValidacionError("La categoría del equipo es obligatoria.")
        self.categoria = categoria.strip()

    def validar_parametros(self, duracion: float, **kwargs) -> None:
        if duracion <= 0:
            raise ValidacionError("La duración del alquiler debe ser mayor que 0.")

    def _costo_bruto(self, duracion: float, **kwargs) -> float:
        return self.tarifa_base * duracion

    def describir(self) -> str:
        return f"Equipo '{self.nombre}' [{self.categoria}] (${self.tarifa_base}/unidad-tiempo)"


class AsesoriaEspecializada(Servicio):
    def __init__(self, id_entidad: str, nombre: str, tarifa_base: float, especialidad: str, disponible: bool = True):
        super().__init__(id_entidad, nombre, tarifa_base, disponible)
        if not especialidad or not especialidad.strip():
            raise ValidacionError("La especialidad de la asesoría es obligatoria.")
        self.especialidad = especialidad.strip()

    def validar_parametros(self, duracion: float, **kwargs) -> None:
        if duracion < 1:
            raise ValidacionError("La asesoría especializada requiere al menos 1 hora.")

    def _costo_bruto(self, duracion: float, **kwargs) -> float:
        return self.tarifa_base * duracion

    def describir(self) -> str:
        return f"Asesoría '{self.nombre}' en {self.especialidad} (${self.tarifa_base}/h)"


class Reserva(EntidadBase):
    ESTADOS_VALIDOS = ("PENDIENTE", "CONFIRMADA", "CANCELADA")

    def __init__(self, id_entidad: str, cliente: Cliente, servicio: Servicio, duracion: float, descuento: float = 0.0, impuesto: float = 0.19):
        super().__init__(id_entidad)
        if not isinstance(cliente, Cliente):
            raise ValidacionError("Debe proporcionarse un objeto Cliente válido.")
        if not isinstance(servicio, Servicio):
            raise ValidacionError("Debe proporcionarse un objeto Servicio válido.")
        if not servicio.disponible:
            raise ServicioNoDisponibleError(f"El servicio '{servicio.nombre}' no está disponible.")

        self.cliente = cliente
        self.servicio = servicio
        self.duracion = duracion
        self.estado = "PENDIENTE"
        self.total = self.servicio.calcular_costo(duracion, descuento=descuento, impuesto=impuesto)

    def confirmar(self):
        if self.estado == "CANCELADA":
            raise ReservaError("No se puede confirmar una reserva cancelada.")
        self.estado = "CONFIRMADA"

    def cancelar(self):
        if self.estado == "CONFIRMADA":
            raise ReservaError("No se puede cancelar una reserva ya confirmada.")
        self.estado = "CANCELADA"

    def describir(self) -> str:
        return (
            f"Reserva [{self.id_entidad}] | Estado: {self.estado} | "
            f"{self.cliente.nombre} -> {self.servicio.nombre} ({self.duracion}h) | Total: ${self.total}"
        )


# --- 3. SISTEMA CON LISTAS Y MANEJO DE EXCEPCIONES ---
class SistemaGestionFJ:
    def __init__(self):
        self.clientes: list[Cliente] = []
        self.servicios: list[Servicio] = []
        self.reservas: list[Reserva] = []

    def registrar_cliente(self, id_c: str, nombre: str, correo: str):
        try:
            cliente = Cliente(id_c, nombre, correo)
            self.clientes.append(cliente)
            logging.info(f"Cliente registrado: {cliente.describir()}")
            print(f"[OK] {cliente.describir()}")
            return cliente
        except SoftwareFJError as e:
            logging.error(f"Error al registrar cliente ({id_c}): {e}")
            print(f"[ERROR] {e}")
        finally:
            pass
        return None

    def registrar_servicio(self, servicio: Servicio):
        try:
            self.servicios.append(servicio)
            logging.info(f"Servicio registrado: {servicio.describir()}")
            print(f"[OK] Servicio añadido: {servicio.describir()}")
        except Exception as e:
            logging.error(f"Error al registrar servicio: {e}")
            print(f"[ERROR] {e}")

    def crear_reserva(self, id_r: str, cliente: Cliente, servicio: Servicio, duracion: float, descuento: float = 0.0, impuesto: float = 0.19):
        try:
            reserva = Reserva(id_r, cliente, servicio, duracion, descuento=descuento, impuesto=impuesto)
            self.reservas.append(reserva)
        except SoftwareFJError as e:
            logging.error(f"Fallo en reserva {id_r}: {e}")
            print(f"[ERROR RESERVA] {e}")
        else:
            logging.info(f"Reserva creada: {reserva.describir()}")
            print(f"[OK] {reserva.describir()}")
            return reserva
        finally:
            logging.debug(f"Intento de reserva '{id_r}' finalizado.")
        return None
