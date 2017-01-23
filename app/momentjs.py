"""Template plugin for timestamp rendering."""

from jinja2 import Markup


class momentjs(object):
    """Template class for moment.js plugin.

    Used for rendering timestamps in the local time zone.
    """

    def __init__(self, timestamp):
        """Initialize the instance."""
        self.timestamp = timestamp

    def render(self, format):
        """Render the <script> tag with the specified formatting."""
        return Markup("""<script>document.write(moment("{stamp}").{format});
            </script>""".format(
            stamp=self.timestamp.strftime("%Y-%m-%dT%H:%M:%S Z"),
            format=format))

    def format(self, fmt):
        """Use moment's format function to format."""
        return self.render('format("{0}")'.format(fmt))

    def calendar(self):
        """Use moment's calendar function to format."""
        return self.render('calendar()')

    def fromNow(self):
        """Use moment's fromNow function to format."""
        return self.render('fromNow()')
