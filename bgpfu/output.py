
import inspect
import pkg_resources
import re


class Output(object):
    """
    abstract writing to different output formats
    """

    @property
    def available_formats(self):
        re_out = re.compile('^output_(?P<type>\w+)$')
        fmts = []

        for name, obj in inspect.getmembers(type(self), inspect.ismethod):
            match = re_out.match(name)
            if match:
                fmts.append(match.group('type'))

        return fmts

    def write(self, fmt, fobj, data):
        """
        write data in specified format to fobj
        """
        func = 'output_' + fmt
        if not hasattr(self, func):
            raise ValueError("unknown output format '%s'" % fmt)
        return getattr(self, func)(fobj, data)

    def load_file(self, filename):
        """
        load file from package
        """
        return pkg_resources.resource_string('bgpfu', filename)

    def _init_jinja(self, tmpl_name):
        tmpl = self.load_file(template + '.j2')

    def output_juniper(self, jobj, data):
        eng = self._init_jinja('juniper')

    def output_txt(self, fobj, data):
        if isinstance(data, list):
            fobj.write('\n'.join(data))
            fobj.write('\n')
            return

