import ipaddress
import json
import logging

import radix

logger = logging.getLogger(__name__)


def parse_roa(roa):
    """Parses an roa record in place and returns the result."""
    try:
        roa["prefix"] = ipaddress.ip_network(roa["prefix"])
        roa["asn"] = int(roa["asn"].replace("AS", ""))
        roa["maxLength"] = int(roa["maxLength"])
        # check bounds on asn
        if not 0 <= roa["asn"] < 2 ** 32:
            raise ValueError(f"asn {asn} is out of range")
    except ValueError as exc:
        logger.warning(str(exc))
        return None

    return roa


def parse_rib_line(line):
    """
    Parses a line from a rib file and yields prefix_str, roa.
    """

    if line[0] == "#":
        return
    try:
        prefix_str, asns = tuple(line.split())
        prefix = ipaddress.ip_network(prefix_str)
    except Exception as exc:
        line = line.rstrip()
        logger.warning(f"Could not parse line '{line}': {exc}")
        return

    for asn in asns.split("|"):
        try:
            yield prefix_str, dict(
                asn=int(asn), prefix=prefix, maxLength=prefix.prefixlen
            )
        except (TypeError, ValueError):
            line = line.rstrip()
            logger.warning(f"Could not parse asn from line '{line}'")


def _add_node(tree, prefix_str, roa):
    """Add a node to a radix tree under prefix_str."""
    node = tree.search_exact(prefix_str)
    if not node:
        node = tree.add(prefix_str)
    node.data.setdefault("roas", []).append(roa)


class RoaTree:
    def __init__(self, rib_file=None, rpki_file=None):
        """Creates an instance of RoaTree from passed file."""
        self.meta = dict()

        if rib_file and rpki_file:
            raise ValueError("rib and rpki are mutually exclusive")

        if rib_file:
            self.load_rib_file(rib_file)

        if rpki_file:
            self.load_rpki_file(rpki_file)

    def load_rib_file(self, filename, merge=False):
        """Loads a rib file into the tree.

        Merge=True adds to the current tree
        """
        if merge:
            tree = self._tree
        else:
            tree = radix.Radix()

        with open(filename) as fh:
            for line in fh.readlines():
                for prefix_str, roa in parse_rib_line(line):
                    _add_node(tree, prefix_str, roa)

        if merge:
            self.meta.setdefault("filename", []).append(filename)
        else:
            self.meta["filename"] = [filename]
        self.meta["type"] = "rib"
        self._tree = tree

    def load_rpki_file(self, filename):
        """Loads a rpki json file."""
        with open(filename) as fh:
            data = json.load(fh)
        tree = radix.Radix()

        for roa in data["roas"]:
            prefix_str = roa["prefix"]
            roa = parse_roa(roa)
            if not roa:
                continue
            _add_node(tree, prefix_str, roa)

        self.meta = data["metadata"]
        self.meta["filename"] = [filename]
        self.meta["type"] = "rib"
        self._tree = tree

    def check_invalid(self, *args, **kwargs):
        """Check if invalid.

        Returns True for invalid, False if valid or not found.
        """
        return self.validation_state(*args, **kwargs)["state"] == "invalid"

    def validate_best(self, prefix, origin):
        """Validate prefix and orgin against most specific match only."""
        covered_roas = []
        prefix = ipaddress.ip_network(prefix)
        prefix_str = str(prefix)
        vrp = self._tree.search_best(prefix_str)
        if not vrp:
            return {"state": "notfound"}

        vrp_prefix = ipaddress.ip_network(vrp.prefix)
        if not prefix.subnet_of(vrp_prefix):
            return {"state": "notfound"}

        for roa in vrp.data["roas"]:
            if origin == roa["asn"]:
                return {"state": "valid", "roa": roa}

            covered_roas.append(roa)

        return {"state": "invalid", "roas": covered_roas}

    def validation_state(self, prefix, origin, check_maxlength=True):
        """
        prefix is the to-be-tested prefix
        origin is the origin asn to be used in the test
        """

        tree = self._tree
        prefix = ipaddress.ip_network(prefix)
        prefix_str = str(prefix)

        best = tree.search_best(prefix_str)
        if not tree.search_best(prefix_str):
            return {"state": "notfound"}

        covered_roas = []
        worst_prefix = tree.search_worst(prefix_str).prefix

        for vrp in tree.search_covered(worst_prefix):
            vrp_prefix = ipaddress.ip_network(vrp.prefix)

            if not prefix.subnet_of(vrp_prefix):
                continue

            for roa in vrp.data["roas"]:
                covered_roas.append(roa)
                if origin != roa["asn"]:
                    continue

                if vrp.prefixlen > prefix.prefixlen:
                    continue

                if check_maxlength and prefix.prefixlen > roa["maxLength"]:
                    continue
                return {"state": "valid", "roa": roa}

        return {"state": "invalid", "roas": covered_roas}
