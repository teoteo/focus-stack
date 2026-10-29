"""Caricamento del firmware sull'Arduino Nano del focheggiatore, senza avrdude.

Parla con il bootloader Arduino (protocollo STK500 v1, lo stesso usato da avrdude con
`-c arduino`): riavvia la scheda tramite DTR (o aspetta che si prema il tasto reset, sulle
schede come l'Ardufocus che non si riavviano da USB), controlla la firma del chip, scrive la flash a
pagine da 128 byte e la rilegge tutta per verificarla. La EEPROM (impostazioni del
focheggiatore) non viene toccata. Funziona sia con il bootloader vecchio (57600 baud) sia con
optiboot (115200 baud).

Se il caricamento si interrompe la scheda non si rovina: il bootloader resta intatto e basta
ripetere l'operazione.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

import serial

from .i18n import tr

STK_OK, STK_INSYNC, CRC_EOP = 0x10, 0x14, 0x20
GET_SYNC, ENTER_PROGMODE, LEAVE_PROGMODE = 0x30, 0x50, 0x51
LOAD_ADDRESS, PROG_PAGE, READ_PAGE, READ_SIGN = 0x55, 0x64, 0x74, 0x75

ATMEGA328P_SIGNATURE = bytes([0x1E, 0x95, 0x0F])
PAGE_SIZE = 128
MAX_APP_SIZE = 30720          # 32 KB meno i 2 KB del bootloader vecchio
BAUD_RATES = (57600, 115200)  # bootloader vecchio, optiboot

Progress = Callable[[str, float], None]   # (fase, frazione 0–1)


class FlashError(Exception):
    pass


def read_hex(path: str | Path) -> bytes:
    """Legge un file Intel HEX e restituisce l'immagine della flash (spazi vuoti = 0xFF)."""
    image = bytearray()
    base = 0
    for n, line in enumerate(Path(path).read_text().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        if not line.startswith(":"):
            raise FlashError(tr("File HEX non valido (riga {n})", n=n))
        rec = bytes.fromhex(line[1:])
        if sum(rec) & 0xFF:
            raise FlashError(tr("Checksum errato nel file HEX (riga {n})", n=n))
        length, addr, rtype, data = rec[0], (rec[1] << 8) | rec[2], rec[3], rec[4:4 + rec[0]]
        if rtype == 0:
            start = base + addr
            if len(image) < start + length:
                image.extend(b"\xff" * (start + length - len(image)))
            image[start:start + length] = data
        elif rtype == 1:
            break
        elif rtype == 2:
            base = ((data[0] << 8) | data[1]) << 4
        elif rtype == 4:
            base = ((data[0] << 8) | data[1]) << 16
    if not image:
        raise FlashError(tr("Il file HEX è vuoto"))
    if len(image) > MAX_APP_SIZE:
        raise FlashError(tr("Firmware troppo grande ({size} byte, massimo {max})", size=len(image), max=MAX_APP_SIZE))
    if len(image) % PAGE_SIZE:
        image.extend(b"\xff" * (PAGE_SIZE - len(image) % PAGE_SIZE))
    return bytes(image)


class _Bootloader:
    def __init__(self, ser: serial.Serial):
        self.ser = ser

    def _cmd(self, payload: bytes, reply_len: int = 0, timeout: float = 1.0) -> bytes:
        self.ser.timeout = timeout
        self.ser.write(payload + bytes([CRC_EOP]))
        self.ser.flush()
        head = self.ser.read(1)
        if head != bytes([STK_INSYNC]):
            raise FlashError(tr("Il bootloader non risponde (ricevuto {data})", data=head.hex() or tr("niente")))
        data = self.ser.read(reply_len) if reply_len else b""
        if len(data) != reply_len or self.ser.read(1) != bytes([STK_OK]):
            raise FlashError(tr("Risposta incompleta dal bootloader"))
        return data

    def sync(self) -> bool:
        for _ in range(8):
            self.ser.reset_input_buffer()
            try:
                self._cmd(bytes([GET_SYNC]), timeout=0.25)
                return True
            except FlashError:
                continue
        return False

    def signature(self) -> bytes:
        return self._cmd(bytes([READ_SIGN]), 3)

    def load_address(self, byte_addr: int) -> None:
        word = byte_addr // 2
        self._cmd(bytes([LOAD_ADDRESS, word & 0xFF, word >> 8]))

    def write_page(self, data: bytes) -> None:
        self._cmd(bytes([PROG_PAGE, len(data) >> 8, len(data) & 0xFF, ord("F")]) + data, timeout=2.0)

    def read_page(self, size: int) -> bytes:
        return self._cmd(bytes([READ_PAGE, size >> 8, size & 0xFF, ord("F")]), size)


def _open_bootloader(port: str) -> tuple[serial.Serial, _Bootloader]:
    """Riavvia l'Arduino (impulso su DTR) e aggancia il bootloader, provando le due velocità."""
    for baud in BAUD_RATES:
        ser = serial.Serial(port, baud, timeout=0.25)
        try:
            ser.dtr = ser.rts = False
            time.sleep(0.25)
            ser.dtr = ser.rts = True
            time.sleep(0.05)
            bl = _Bootloader(ser)
            if bl.sync():
                return ser, bl
        except (OSError, serial.SerialException) as exc:
            ser.close()
            raise FlashError(tr("Impossibile aprire {port}: {exc}", port=port, exc=exc)) from exc
        ser.close()
    raise FlashError(tr("Bootloader non trovato: controlla il cavo USB e che nessun altro programma "
                        "stia usando la porta del focheggiatore"))


def _wait_bootloader(port: str, report: Progress, window: float = 10.0, total: float = 90.0) -> tuple[serial.Serial, _Bootloader]:
    """Aspetta che l'utente prema il tasto reset e aggancia il bootloader.

    Una velocità per finestra di `window` secondi, alternandole fino a `total`: byte ricevuti a
    velocità sbagliata fanno uscire optiboot dal bootloader, quindi cambiarla a ogni tentativo
    farebbe fallire anche quella giusta. Se la pressione cade nella finestra sbagliata basta
    ripremere il tasto.
    """
    start = time.monotonic()
    i = 0
    while time.monotonic() - start < total:
        baud = BAUD_RATES[i % len(BAUD_RATES)]
        i += 1
        left = int(total - (time.monotonic() - start))
        report(tr("Premi il tasto reset sul focheggiatore (ancora {left} s)", left=left), 0.0)
        try:
            ser = serial.Serial(port, baud, timeout=0.05)
        except (OSError, serial.SerialException) as exc:
            raise FlashError(tr("Impossibile aprire {port}: {exc}", port=port, exc=exc)) from exc
        end = min(time.monotonic() + window, start + total)
        while time.monotonic() < end:
            ser.reset_input_buffer()
            ser.write(bytes([GET_SYNC, CRC_EOP]))
            time.sleep(0.05)
            if ser.read(2) == bytes([STK_INSYNC, STK_OK]):
                return ser, _Bootloader(ser)
        ser.close()
    raise FlashError(tr("Bootloader non trovato: premi il tasto reset del focheggiatore mentre "
                        "l'app aspetta, e controlla che nessun altro programma usi la porta"))


def flash(port: str, hex_path: str | Path, progress: Progress | None = None,
          manual_reset: bool = False) -> int:
    """Scrive e verifica il firmware. Restituisce il numero di byte scritti."""
    report = progress or (lambda phase, frac: None)
    image = read_hex(hex_path)
    report(tr("Collegamento al bootloader"), 0.0)
    ser, bl = _wait_bootloader(port, report) if manual_reset else _open_bootloader(port)
    try:
        sig = bl.signature()
        if sig != ATMEGA328P_SIGNATURE:
            raise FlashError(tr("Chip inatteso (firma {sig}): il firmware è per ATmega328P", sig=sig.hex()))
        bl._cmd(bytes([ENTER_PROGMODE]))
        pages = range(0, len(image), PAGE_SIZE)
        for i, addr in enumerate(pages):
            bl.load_address(addr)
            bl.write_page(image[addr:addr + PAGE_SIZE])
            report(tr("Scrittura"), (i + 1) / len(pages))
        for i, addr in enumerate(pages):
            bl.load_address(addr)
            if bl.read_page(PAGE_SIZE) != image[addr:addr + PAGE_SIZE]:
                raise FlashError(tr("Verifica fallita all'indirizzo {addr}: riprova il caricamento", addr=f"{addr:#06x}"))
            report(tr("Verifica"), (i + 1) / len(pages))
        bl._cmd(bytes([LEAVE_PROGMODE]))
    finally:
        ser.close()
    report(tr("Completato"), 1.0)
    return len(image)
