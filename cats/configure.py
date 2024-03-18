"""This module exports a function :py:func:`configure
<cats.configure.configure>` that processes both command line arguments
and configuration file. This function returns a runtime configuration
for cats to make a request to a carcon intensity forecast provider.  A
runtime configuration consits of:

- location (postcode)
- job duration
- Interface to carbon intensity forecast provider (See TODO)

"""

import logging
import sys
from collections.abc import Mapping
from typing import Any

import requests
import yaml

from .CI_api_interface import API_interfaces, APIInterface

__all__ = ["get_runtime_config"]


def get_runtime_config(args) -> tuple[dict, APIInterface, str, int]:
    """Return the runtime cats configuration from list of command line
    arguments and content of configuration file.

    Returns a tupe containing a dictionary reprensenting the
    configuration file, an instance of :py:class:`APIInterface
    <cats.CI_api_interface.APIInterface>`, the location as a string
    and the duration in minutes as an integer.

    :param args: Command line arguments
    :return: Runtime cats configuration
    :rtype: tuple[dict, APIInterface, str, int]
    :raises ValueError: If job duration cannot be interpreted as a positive integer.

    """
    configmapping = config_from_file(configpath=args.config)
    CI_API_interface = CI_API_from_config_or_args(args, configmapping)
    location = get_location_from_config_or_args(args, configmapping)
    hw_info = get_hardware_info(args, configmapping)

    msg = "Job duration must be a positive integer (number of minutes)"
    try:
        duration = int(args.duration)
    except ValueError:
        logging.eror(msg)
        raise ValueError
    if duration <= 0:
        logging.error(msg)
        raise ValueError

    return configmapping, CI_API_interface, location, duration


def config_from_file(configpath="") -> Mapping[str, Any]:
    if configpath:
        # if path to config file provided, it is used
        with open(configpath, "r") as f:
            return yaml.safe_load(f)
        logging.info(f"Using provided config file: {configpath}\n")
    else:
        # if no path provided, look for `config.yml` in current directory
        try:
            with open("config.yml", "r") as f:
                return yaml.safe_load(f)
            logging.info("Using config.yml found in current directory\n")
        except FileNotFoundError:
            logging.warning("config file not found")
            return {}


def CI_API_from_config_or_args(args, config) -> APIInterface:
    try:
        api = args.api if args.api else config["api"]
    except KeyError:
        api = "carbonintensity.org.uk"  # default value
        logging.warning(f"Unspecified carbon intensity forecast service, using {api}")
    try:
        return API_interfaces[api]
    except KeyError:
        logging.error(
            f"Error: {api} is not a valid API choice. It must be one of " "\n".join(
                API_interfaces.keys()
            )
        )


def get_location_from_config_or_args(args, config) -> str:
    if args.location:
        location = args.location
        logging.info(f"Using location provided from command line: {location}")
        return location
    if "location" in config.keys():
        location = config["location"]
        logging.info(f"Using location from config file: {location}")
        return location

    r = requests.get("https://ipapi.co/json/")
    if r.status_code != 200:
        logging.error(
            "Could not get location from ipapi.co.\n"
            f"Got Error {r.status_code} - {r.json()['reason']}\n"
            f"{r.json()['message']}"
        )
        sys.exit(1)
    location = r.json()["postal"]
    assert location
    logging.warning(
        f"location not provided. Estimating location from IP address: {location}."
    )
    return location


def get_hardware_info(jobinfo: str, profiles: dict):
    """Parses a string of job info keys in the form

    profile=GPU_partition,memory=8,ncpus=8,ngpus=4

    and checks all required info keys are present and of the right type.

    Returns
    -------

    info: dict
        A dictionary mapping info key to their specified values
    """

    expected_info_keys = (
        "memory",
        "cpus",
        "gpus",
    )
    info = dict([m.groups() for m in re.finditer(r"(\w+)=(\w+)", jobinfo)])

    # Check if some information is missing
    if missing_keys := set(expected_info_keys) - set(info.keys()):
        sys.stderr.write(f"ERROR: Missing job info keys: {missing_keys}")
        return {}

    if "profile" not in info.keys():
        profile_key, profile = next(iter(profiles.items()))
        logging.warning(f"Using default profile {profile_key}")
    else:
        try:
            profile = profiles[info.pop("profile")]
        except KeyError:
            logging.error(
                f"ERROR: job info key 'profile' should be one of {profiles.keys()}. Typo?\n"
            )
        sys.exit(1)

    # check that `cpus`, `gpus` and `memory` are numeric and convert to int
    for key in [k for k in info]:
        try:
            info[key] = int(info[key])
        except ValueError:
            loggin.error(f"job info key {key} should be numeric\n")
            sys.exit(1)

    return [
        (profile[device_type]["power"], info[f"n{device_type}s"])
        for device_type in ["cpu", "gpu"]
    ]
