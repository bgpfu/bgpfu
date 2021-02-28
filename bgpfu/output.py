# Copyright (C) 2016 Matt Griswold <grizz@20c.com>
#
# This file is part of bgpfu
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import inspect
import re

import pkg_resources


class Output:
    """
    abstract writing to different output formats
    """

    @property
    def available_formats(self):
        re_out = re.compile(r"^output_(?P<type>\w+)$")
        fmts = []

        for name, obj in inspect.getmembers(type(self), inspect.ismethod):
            match = re_out.match(name)
            if match:
                fmts.append(match.group("type"))

        return fmts

    def write(self, fmt, fobj, data):
        """
        write data in specified format to fobj
        """
        func = "output_" + fmt
        if not hasattr(self, func):
            raise ValueError("unknown output format '%s'" % fmt)
        return getattr(self, func)(fobj, data)

    def load_file(self, filename):
        """
        load file from package
        """
        return pkg_resources.resource_string("bgpfu", filename)

    def _init_jinja(self, tmpl_name):
        tmpl = self.load_file(tmpl_name + ".j2")

    def output_juniper(self, jobj, data):
        eng = self._init_jinja("juniper")

    def output_txt(self, fobj, data):
        if isinstance(data, list):
            fobj.write("\n".join(data))
            fobj.write("\n")
            return
