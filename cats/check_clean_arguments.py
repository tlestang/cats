import re
import sys


def validate_jobinfo(jobinfo: str, expected_profile_names):
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

    profile = info.pop("profile", "default")
    # Validate partition value
    if profile not in expected_profile_names:
        sys.stderr.write(
            f"ERROR: job info key 'profile' should be one of {expected_profile_names}. Typo?\n"
        )
        return {}

    # check that `cpus`, `gpus` and `memory` are numeric and convert to int
    for key in [k for k in info]:
        try:
            info[key] = int(info[key])
        except ValueError:
            sys.stderr.write(f"ERROR: job info key {key} should be numeric\n")
            return {}

    return info
