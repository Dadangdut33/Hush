from audioop import rms as calculate_rms
from numpy import log10

import pyaudio

from hush.custom_logging import logger


def get_db(audio_data: bytes) -> float:
    """Get the db value of the audio data.

    Parameters
    ----------
    audio_data : bytes
        chunk of audio data from pyaudio input stream in bytes

    Returns
    -------
    float
        db value of the audio data
    """
    rms: float = calculate_rms(audio_data, 2) / 32767
    if rms == 0.0:
        return 0.0
    else:
        return 20 * log10(rms)  # convert to db


def get_device_details(sj, p: pyaudio.PyAudio):
    """
    Function to get the device detail, chunk size, sample rate, and number of channels.

    Parameters
    ----
    sj: dict
        setting object
    p: pyaudio.PyAudio
        PyAudio object

    Returns
    ----
    bool
        True if success, False if failed
    dict
        device detail, chunk size, sample rate, and number of channels
    """
    try:
        device = sj.cache["device"]

        # get the id in device string [ID: deviceIndex,hostIndex]
        id = device.split("[ID: ")[1]  # first get the id bracket
        id = id.split("]")[0]  # then get the id
        deviceIndex = id.split(",")[0]
        hostIndex = id.split(",")[1]

        device_detail = p.get_device_info_by_host_api_device_index(int(deviceIndex), int(hostIndex))

        # https://github.com/wiseman/py-webrtcvad/issues/30
        chunk_size = 480  # hard coded chunk size. no need for this to be changeable, we are just detecting speech and db
        sample_rate = int(sj.cache["sample_rate"])
        num_of_channels = str(sj.cache["channel"])
        logger.debug(f"Device: ({device_detail['index']}) {device_detail['name']}")
        logger.debug(f"Sample Rate {sample_rate} | channels {num_of_channels} | chunk size {chunk_size}")
        logger.debug(f"Actual device detail: {device_detail}")

        return True, {
            "device_detail": device_detail,
            "chunk_size": chunk_size,
            "sample_rate": sample_rate,
            "num_of_channels": num_of_channels,
        }
    except Exception as e:
        logger.error("Something went wrong while trying to get the device details.")
        logger.exception(e)
        return False, {
            "device_detail": {},
            "chunk_size": 0,
            "sample_rate": 0,
            "num_of_channels": 0,
        }


def get_input_devices(hostAPI: str):
    """
    Get the input devices (mic) from the specified hostAPI.
    """
    devices = []
    p = pyaudio.PyAudio()
    try:
        for i in range(p.get_host_api_count()):
            current_api_info = p.get_host_api_info_by_index(i)
            # This will ccheck hostAPI parameter
            # If it is empty, get all devices. If specified, get only the devices from the specified hostAPI
            if (hostAPI == current_api_info["name"]) or (hostAPI == ""):
                for j in range(int(current_api_info["deviceCount"])):
                    device = p.get_device_info_by_host_api_device_index(i, j)  # get device info by host api device index
                    if int(device["maxInputChannels"]) > 0:
                        devices.append(f"[ID: {i},{j}] | {device['name']}")  # j is the device index in the host api

        if len(devices) == 0:  # check if input empty or not
            devices = ["[WARNING] No input devices found."]
    except Exception as e:
        logger.error("Something went wrong while trying to get the input devices (mic).")
        logger.exception(e)
        devices = ["[ERROR] Check the terminal/log for more information."]
    finally:
        p.terminate()
        return devices


def get_host_apis():
    """
    Get the host apis from the system.
    """
    apis = []
    p = pyaudio.PyAudio()
    try:
        for i in range(p.get_host_api_count()):
            current_api_info = p.get_host_api_info_by_index(i)
            apis.append(f"{current_api_info['name']}")

        if len(apis) == 0:  # check if input empty or not
            apis = ["[WARNING] No host apis found."]
    except Exception as e:
        logger.error("Something went wrong while trying to get the host apis.")
        logger.exception(e)
        apis = ["[ERROR] Check the terminal/log for more information."]
    finally:
        p.terminate()
        return apis


def get_default_input_device():
    """Get the default input device (mic).

    Returns
    -------
    bool
        True if success, False if failed
    str | dict
        Default input device detail. If failed, return the error message (str).
    """
    p = pyaudio.PyAudio()
    sucess = False
    default_device = None
    try:
        default_device = p.get_default_input_device_info()
        sucess = True
    except Exception as e:
        if "Error querying device -1" in str(e):
            logger.warning("No input device found. Ignore this if you dont have a mic. Err details below:")
            logger.exception(e)
            default_device = "No input device found."
        else:
            logger.error("Something went wrong while trying to get the default input device (mic).")
            logger.exception(e)
            default_device = str(e)
    finally:
        p.terminate()
        return sucess, default_device


def get_default_host_api():
    """Get the default host api.

    Returns
    -------
    bool
        True if success, False if failed
    str | dict
        Default host api detail. If failed, return the error message (str).
    """
    p = pyaudio.PyAudio()
    sucess = False
    default_host_api = None
    try:
        default_host_api = p.get_default_host_api_info()
        sucess = True
    except OSError as e:
        logger.error("Something went wrong while trying to get the default host api.")
        logger.exception(e)
        default_host_api = str(e)
    finally:
        p.terminate()
        return sucess, default_host_api
